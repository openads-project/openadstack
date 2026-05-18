#!/usr/bin/env python3
"""Render compose files from an includes directory into the project tree."""

from __future__ import annotations

import argparse
import base64
import copy
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq


OCI_MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
    ]
)
OCI_LAYER_ACCEPT = ", ".join(["application/octet-stream", "*/*"])
COMPOSE_FILENAMES = {
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
}



def create_yaml() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


YAML_LOADER = create_yaml()


@dataclass(frozen=True)
class OciReference:
    registry: str
    repository: str
    reference: str


class RegistryClient:
    def __init__(self) -> None:
        self._tokens: dict[tuple[str, str], str] = {}
        self._credentials = load_docker_credentials()

    def get_json(self, registry: str, path: str, accept: str) -> dict[str, Any]:
        data = self._request(registry, path, accept)
        return json.loads(data.decode("utf-8"))

    def get_bytes(self, registry: str, path: str, accept: str) -> bytes:
        return self._request(registry, path, accept)

    def _request(self, registry: str, path: str, accept: str) -> bytes:
        url = f"https://{registry}{path}"
        headers = {"Accept": accept, "User-Agent": "render-compose-files/1.0"}
        token = self._tokens.get((registry, path))
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            return self._open(url, headers)
        except HTTPError as error:
            if error.code != 401:
                raise
            challenge = error.headers.get("WWW-Authenticate", "")
            token = self._fetch_bearer_token(registry, challenge)
            self._tokens[(registry, path)] = token
            headers["Authorization"] = f"Bearer {token}"
            return self._open(url, headers)

    def _open(self, url: str, headers: dict[str, str]) -> bytes:
        with urlopen(Request(url, headers=headers), timeout=60) as response:
            return response.read()

    def _fetch_bearer_token(self, registry: str, challenge: str) -> str:
        scheme, _, params_text = challenge.partition(" ")
        if scheme.lower() != "bearer":
            raise RuntimeError(f"unsupported registry auth challenge: {challenge}")

        params = parse_auth_params(params_text)
        realm = params.pop("realm", None)
        if not realm:
            raise RuntimeError(f"registry auth challenge has no realm: {challenge}")

        query = urlencode(params)
        url = f"{realm}?{query}" if query else realm
        headers = {"User-Agent": "render-compose-files/1.0"}
        credential = self._credentials.get(registry)
        if credential:
            headers["Authorization"] = "Basic " + base64.b64encode(
                f"{credential[0]}:{credential[1]}".encode("utf-8")
            ).decode("ascii")

        with urlopen(Request(url, headers=headers), timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))

        token = payload.get("token") or payload.get("access_token")
        if not token:
            raise RuntimeError(f"registry token response from {realm} did not include a token")
        return str(token)


def parse_auth_params(params_text: str) -> dict[str, str]:
    params: dict[str, str] = {}
    key = ""
    value = ""
    in_key = True
    in_quotes = False
    escaped = False

    def flush() -> None:
        nonlocal key, value, in_key
        if key:
            params[key.strip()] = value.strip().strip('"')
        key = ""
        value = ""
        in_key = True

    for char in params_text:
        if escaped:
            value += char
            escaped = False
        elif char == "\\" and in_quotes and not in_key:
            escaped = True
        elif char == '"' and not in_key:
            in_quotes = not in_quotes
            value += char
        elif char == "=" and in_key:
            in_key = False
        elif char == "," and not in_quotes:
            flush()
        elif in_key:
            key += char
        else:
            value += char
    flush()
    return params


def load_docker_credentials() -> dict[str, tuple[str, str]]:
    config_path = Path.home() / ".docker" / "config.json"
    if not config_path.exists():
        return {}

    with config_path.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    credentials: dict[str, tuple[str, str]] = {}
    auths = config.get("auths") or {}
    for registry, auth_config in auths.items():
        auth = auth_config.get("auth")
        if auth:
            decoded = base64.b64decode(auth).decode("utf-8")
            username, _, password = decoded.partition(":")
            credentials[normalize_registry(registry)] = (username, password)

    helpers = {
        normalize_registry(registry): auth_config.get("credHelper")
        for registry, auth_config in auths.items()
        if auth_config.get("credHelper")
    }
    default_helper = config.get("credsStore")

    for registry in auths:
        normalized = normalize_registry(registry)
        if normalized in credentials:
            continue
        helper = helpers.get(normalized) or default_helper
        if not helper:
            continue
        helper_credentials = read_docker_credential_helper(helper, registry)
        if helper_credentials:
            credentials[normalized] = helper_credentials

    return credentials


def normalize_registry(registry: str) -> str:
    parsed = urlparse(registry)
    return parsed.netloc if parsed.netloc else registry


def read_docker_credential_helper(helper: str, registry: str) -> tuple[str, str] | None:
    helper_command = f"docker-credential-{helper}"
    try:
        result = subprocess.run(
            [helper_command, "get"],
            input=registry,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        return None

    payload = json.loads(result.stdout)
    username = payload.get("Username")
    secret = payload.get("Secret")
    if not username or secret is None:
        return None
    return str(username), str(secret)


def parse_oci_reference(uri: str) -> OciReference:
    if not uri.startswith("oci://"):
        raise ValueError(f"not an OCI reference: {uri}")

    reference = uri.removeprefix("oci://")
    registry, slash, remainder = reference.partition("/")
    if not slash or not registry or not remainder:
        raise ValueError(f"invalid OCI reference: {uri}")

    if "@" in remainder:
        repository, digest = remainder.rsplit("@", 1)
        ref = digest
    else:
        repository, colon, tag = remainder.rpartition(":")
        if not colon or "/" in tag:
            repository = remainder
            tag = "latest"
        ref = tag

    if not repository or not ref:
        raise ValueError(f"invalid OCI reference: {uri}")
    return OciReference(registry=registry, repository=repository, reference=ref)


def load_compose_from_oci(client: RegistryClient, uri: str) -> CommentedMap:
    reference = parse_oci_reference(uri)
    manifest = client.get_json(
        reference.registry,
        f"/v2/{reference.repository}/manifests/{reference.reference}",
        OCI_MANIFEST_ACCEPT,
    )

    if manifest.get("manifests"):
        digest = manifest["manifests"][0]["digest"]
        manifest = client.get_json(
            reference.registry,
            f"/v2/{reference.repository}/manifests/{digest}",
            OCI_MANIFEST_ACCEPT,
        )

    layers = manifest.get("layers") or []
    for layer in layers:
        digest = layer.get("digest")
        if not digest:
            continue
        blob = client.get_bytes(
            reference.registry,
            f"/v2/{reference.repository}/blobs/{digest}",
            OCI_LAYER_ACCEPT,
        )
        compose = compose_from_blob(blob)
        if compose is not None:
            return compose

    raise RuntimeError(f"no compose YAML file found in OCI artifact {uri}")


def compose_from_blob(blob: bytes) -> CommentedMap | None:
    for candidate in expand_blob_candidates(blob):
        document = try_load_compose_yaml(candidate)
        if document is not None:
            return document
    return None


def expand_blob_candidates(blob: bytes) -> list[bytes]:
    candidates = [blob]
    try:
        candidates.append(gzip.decompress(blob))
    except OSError:
        pass

    expanded: list[bytes] = []
    for candidate in candidates:
        expanded.append(candidate)
        expanded.extend(extract_tar_yaml_files(candidate))
    return expanded


def extract_tar_yaml_files(blob: bytes) -> list[bytes]:
    try:
        with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
            members = [member for member in archive.getmembers() if member.isfile()]
            preferred = [
                member
                for member in members
                if Path(member.name).name in COMPOSE_FILENAMES
            ]
            yaml_members = preferred or [
                member
                for member in members
                if Path(member.name).suffix in {".yaml", ".yml"}
            ]
            files: list[bytes] = []
            for member in yaml_members:
                extracted = archive.extractfile(member)
                if extracted:
                    files.append(extracted.read())
            return files
    except tarfile.TarError:
        return []


def try_load_compose_yaml(content: bytes) -> CommentedMap | None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return None

    try:
        document = YAML_LOADER.load(text)
    except Exception:
        return None

    if isinstance(document, CommentedMap) and any(
        key in document for key in ("services", "include", "networks", "volumes")
    ):
        return document
    return None


def read_yaml(path: Path) -> CommentedMap:
    with path.open(encoding="utf-8") as compose_file:
        document = YAML_LOADER.load(compose_file) or CommentedMap()
    if not isinstance(document, CommentedMap):
        raise ValueError(f"{path} must contain a YAML mapping")
    return document


def render_compose(path: Path, destination: Path, client: RegistryClient) -> str:
    local_compose = read_yaml(path)
    includes = normalize_includes(local_compose.get("include"))
    oci_includes = [include for include in includes if is_oci_include(include)]
    remaining_includes = [include for include in includes if not is_oci_include(include)]

    rendered = CommentedMap()
    for include in oci_includes:
        rendered = merge_compose(rendered, load_compose_from_oci(client, include))

    local_without_oci = copy_commented_map(local_compose)
    if remaining_includes:
        local_without_oci["include"] = denormalize_includes(remaining_includes)
    else:
        remove_key_with_comment(local_without_oci, "include")

    rendered = merge_compose(rendered, local_without_oci)
    output = io.StringIO()
    output.write(generated_header(path, destination))
    YAML_LOADER.dump(rendered, output)
    return output.getvalue()


def generated_header(source: Path, destination: Path) -> str:
    script_path = Path(__file__).resolve()
    destination_dir = destination.resolve().parent
    script_relative = os.path.relpath(script_path, destination_dir)
    source_relative = os.path.relpath(source.resolve(), destination_dir)
    return (
        f"# Auto-generated by `{script_relative}` based on\n"
        f"#   {source_relative}\n\n"
    )


def normalize_includes(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def denormalize_includes(includes: list[Any]) -> Any:
    if len(includes) == 1:
        return includes[0]
    sequence = CommentedSeq()
    sequence.extend(includes)
    return sequence


def copy_commented_map(mapping: CommentedMap) -> CommentedMap:
    return copy.copy(mapping)


def remove_key_with_comment(mapping: CommentedMap, key: str) -> None:
    if key in mapping:
        del mapping[key]
    mapping.ca.items.pop(key, None)


def is_oci_include(include: Any) -> bool:
    return isinstance(include, str) and include.startswith("oci://")


def merge_compose(base: Any, override: Any) -> Any:
    if isinstance(base, CommentedMap) and isinstance(override, CommentedMap):
        for key, value in override.items():
            if key in base:
                base[key] = merge_compose(base[key], value)
            else:
                base[key] = value
                copy_key_comment(override, base, key)
        return base
    return override


def copy_key_comment(source: CommentedMap, target: CommentedMap, key: Any) -> None:
    if key in source.ca.items:
        target.ca.items[key] = source.ca.items[key]


def iter_input_files(includes_dir: Path) -> list[Path]:
    return sorted(path for path in includes_dir.rglob("*") if path.is_file())


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def render_files(includes_dir: Path, output_dir: Path, dry_run: bool) -> None:
    client = RegistryClient()
    for source in iter_input_files(includes_dir):
        relative = source.relative_to(includes_dir)
        destination = output_dir / relative

        if source.name == "docker-compose.yml":
            print(f"render {source} -> {destination}")
            if not dry_run:
                write_text_atomic(destination, render_compose(source, destination, client))
        else:
            print(f"copy   {source} -> {destination}")
            if not dry_run:
                copy_file(source, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy includes into the project tree and render OCI compose includes.",
    )
    parser.add_argument(
        "--includes-dir",
        type=Path,
        default=Path("includes"),
        help="Input directory to render from (default: includes).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory for rendered files (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned writes without changing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    includes_dir = args.includes_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not includes_dir.is_dir():
        print(f"error: includes directory does not exist: {includes_dir}", file=sys.stderr)
        return 2

    render_files(includes_dir, output_dir, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
