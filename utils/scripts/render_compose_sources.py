#!/usr/bin/env python3
"""Render `.docker-compose.oci-overrides.yml` files next to their generated compose files."""

import argparse
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from oras.auth import utils as oras_auth_utils
from oras.client import OrasClient
from oras.container import Container
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REMOTE_NAME = ".docker-compose.oci-overrides.yml"
OUTPUT_NAME = "docker-compose.yml"
SERVICE_KEY_ORDER = (
    "profiles",
    "depends_on",
    "extends",
    "restart",
    "healthcheck",
    "image",
    "environment",
    "command",
    "volumes",
)

YAML_RT = YAML()
YAML_RT.preserve_quotes = True
YAML_RT.width = 4096
YAML_RT.indent(mapping=2, sequence=4, offset=2)


def oci_compose(client: OrasClient, uri: str) -> CommentedMap:
    with tempfile.TemporaryDirectory() as outdir:
        for path in pull_oci(client, uri.removeprefix("oci://"), outdir):
            document = load_yaml(Path(path))
            if any(key in document for key in ("services", "include", "networks", "volumes")):
                return document
    raise RuntimeError(f"no compose YAML layer found in {uri}")


def pull_oci(client: OrasClient, reference: str, outdir: str) -> list[str]:
    try:
        return client.pull(reference, outdir=outdir)
    except ValueError as error:
        if "unauthorized" not in str(error).lower() or not load_docker_credentials(
            client, reference
        ):
            raise
    return client.pull(reference, outdir=outdir)


def load_docker_credentials(client: OrasClient, reference: str) -> bool:
    registry = Container(reference).registry
    config = oras_auth_utils.load_configs()
    helper = config.get("credHelpers", {}).get(registry) or config.get("credsStore")
    if not helper:
        return False

    binary = f"docker-credential-{helper}"
    try:
        process = subprocess.run(
            [binary, "get"],
            input=f"{registry}\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        credentials = json.loads(process.stdout)
        username = credentials["Username"]
        secret = credentials["Secret"]
        if not username or not secret:
            raise ValueError("credential helper returned empty credentials")
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
    ) as error:
        raise RuntimeError(
            f"failed to load Docker credentials for {registry} using {binary}"
        ) from error

    client.auth.set_token_auth(None)
    client.auth.set_basic_auth(username, secret)
    return True


def load_yaml(source: str | Path) -> CommentedMap:
    text = source.read_text() if isinstance(source, Path) else source
    document = YAML_RT.load(text) or CommentedMap()
    if not isinstance(document, CommentedMap):
        raise ValueError("compose YAML must be a mapping")
    return document


def render_compose(source: Path, client: OrasClient) -> str:
    local = load_yaml(source)
    header = generated_header(source, local)
    includes = include_list(local.get("include"))
    rendered = CommentedMap()
    for include in includes:
        if is_oci(include):
            rendered = merge(rendered, oci_compose(client, include))
    apply_service_prefixes(rendered, local)
    local = copy.copy(local)
    local.pop("include", None)
    local.ca.items.pop("include", None)
    rendered = merge(rendered, local)
    order_service_keys(rendered)
    buffer = io.StringIO()
    buffer.write(header)
    YAML_RT.dump(rendered, buffer)
    return buffer.getvalue()


def apply_service_prefixes(rendered: CommentedMap, local: CommentedMap) -> None:
    rendered_services = rendered.get("services")
    local_services = local.get("services")
    if not isinstance(rendered_services, CommentedMap) or not isinstance(
        local_services, CommentedMap
    ):
        return

    for local_name in local_services:
        prefix, separator, source_name = local_name.rpartition(".")
        if (
            not prefix
            or not separator
            or local_name in rendered_services
            or source_name not in rendered_services
        ):
            continue

        index = list(rendered_services).index(source_name)
        comments = rendered_services.ca.items.pop(source_name, None)
        service = rendered_services.pop(source_name)
        rendered_services.insert(index, local_name, service)
        if comments is not None:
            rendered_services.ca.items[local_name] = comments


def include_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def is_oci(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("oci://")


def order_service_keys(compose: CommentedMap) -> None:
    services = compose.get("services")
    if not isinstance(services, CommentedMap):
        return
    for service in services.values():
        if not isinstance(service, CommentedMap):
            continue
        for key in reversed(SERVICE_KEY_ORDER):
            if key in service:
                service.move_to_end(key, last=False)


def merge(base: Any, override: Any, indent: int = 0) -> Any:
    if isinstance(base, CommentedMap) and isinstance(override, CommentedMap):
        for key, value in override.items():
            if key in base:
                original = base[key]
                if isinstance(original, CommentedMap) and isinstance(value, CommentedMap):
                    base[key] = merge(original, value, indent + 2)
                else:
                    if plain(original) != plain(value):
                        base.yaml_set_comment_before_after_key(
                            key, before=original_comment(base, key, original), indent=indent
                        )
                        following = following_comment(original)
                    else:
                        following = ""
                    base[key] = value
                    if following:
                        preserve_following_comment(base, key, following, indent)
            else:
                base[key] = value
                if key in override.ca.items:
                    base.ca.items[key] = override.ca.items[key]
        return base
    return override


def following_comment(value: Any) -> str:
    comments = []
    if isinstance(value, list):
        for tokens in value.ca.items.values():
            if tokens and tokens[0]:
                comments.append(tokens[0].value)
    return normalize_comment_block("".join(comments).rstrip()) if comments else ""


def preserve_following_comment(mapping: CommentedMap, key: Any, comment: str, indent: int) -> None:
    keys = list(mapping.keys())
    try:
        next_key = keys[keys.index(key) + 1]
    except (ValueError, IndexError):
        return
    mapping.yaml_set_comment_before_after_key(next_key, before=comment, indent=indent)


def original_comment(source: CommentedMap, key: Any, value: Any) -> str:
    text = scalar_text(value)
    return f"{key}:{text}" if text.startswith("\n") else f"{key}: {text}"


def uncommented(value: Any) -> Any:
    value = copy.deepcopy(value)
    clear_comments(value)
    return value


def clear_comments(value: Any) -> None:
    if hasattr(value, "ca"):
        value.ca.items.clear()
        value.ca.comment = None
        value.ca.end = []
    if isinstance(value, CommentedMap):
        for item in value.values():
            clear_comments(item)
    elif isinstance(value, list):
        for item in value:
            clear_comments(item)


def normalize_comment_block(text: str) -> str:
    normalized = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("# "):
            normalized.append(stripped[2:])
        elif stripped.startswith("#"):
            normalized.append(stripped[1:])
        else:
            normalized.append(line)
    return "\n".join(normalized)


def plain(value: Any) -> Any:
    if isinstance(value, CommentedMap):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    return value


def scalar_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if not isinstance(value, (CommentedMap, list)):
        return str(value)
    rendered = io.StringIO()
    YAML_RT.dump(uncommented(value), rendered)
    return "\n" + rendered.getvalue().replace("\n...\n", "\n").rstrip()


def generated_header(source: Path, compose: CommentedMap) -> str:
    parent = source.resolve().parent
    lines = [
        f"# Auto-generated by `{os.path.relpath(Path(__file__).resolve(), parent)}`",
        f"# based on `{REMOTE_NAME}` with resolved includes",
    ]
    if "include" in compose:
        lines.append("#   include:")
        for include in include_list(compose["include"]):
            if is_oci(include):
                lines.append(f"#     # {oci_source_url(include)}")
                lines.append(f"#     - {include}")
            else:
                rendered = io.StringIO()
                YAML_RT.dump(CommentedSeq([uncommented(include)]), rendered)
                lines += [f"#     {line}" for line in rendered.getvalue().rstrip().splitlines()]
    return "\n".join(lines) + "\n\n"


def oci_source_url(uri: str) -> str:
    """Derive the upstream compose source URL from an OpenADS OCI reference."""
    if not uri.startswith("oci://"):
        raise ValueError(f"unsupported compose OCI reference: {uri}")

    repository, separator, ref = uri.removeprefix("oci://").rpartition(":")
    if not separator or not ref:
        raise ValueError(f"unsupported compose OCI reference: {uri}")

    if repository.endswith("/compose"):
        repository = repository.removesuffix("/compose")
    elif repository.startswith("ghcr.io/") and ref.startswith("compose-"):
        # Backwards-compatible support for `<repository>:compose-<ref>`.
        ref = ref.removeprefix("compose-")
    else:
        raise ValueError(f"unsupported compose OCI reference: {uri}")

    registry, separator, project = repository.partition("/")
    if not separator or not project or not ref:
        raise ValueError(f"unsupported compose OCI reference: {uri}")

    if registry == "ghcr.io" and project.count("/") == 1:
        return (
            f"https://github.com/{project}/blob/{ref}"
            "/deployment/compose/docker-compose.yml"
        )

    if registry == "gitlab.ika.rwth-aachen.de:5050":
        return (
            f"https://gitlab.ika.rwth-aachen.de/{project}"
            f"/-/blob/{ref}"
            "/deployment/compose/docker-compose.yml"
        )

    raise ValueError(f"unsupported compose OCI reference: {uri}")


def relative_path(path: Path) -> str:
    return os.path.relpath(path.resolve(), Path.cwd())


def remote_files(root_dir: Path) -> list[Path]:
    ignored = {".git", "utils"}
    return sorted(
        path for path in root_dir.rglob(REMOTE_NAME)
        if not any(part in ignored for part in path.relative_to(root_dir).parts)
    )


def render_files(root_dir: Path, dry_run: bool) -> None:
    client = OrasClient()
    for source in remote_files(root_dir):
        destination = source.with_name(OUTPUT_NAME)
        print(f"rendering {relative_path(source)} -> {relative_path(destination)}")
        if not dry_run:
            destination.write_text(render_compose(source, client))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root_dir = args.root_dir.resolve()
    if not root_dir.is_dir():
        print(f"error: root directory does not exist: {root_dir}", file=sys.stderr)
        return 2
    render_files(root_dir, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
