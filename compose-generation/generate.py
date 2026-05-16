#!/usr/bin/env python3

import argparse
import ast
import difflib
import os
import re
import shlex
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


STANDARD_ENV = {
    "log_level": ("LOG_LEVEL", "${LOG_LEVEL:-info}"),
    "use_sim_time": ("USE_SIM_TIME", "${USE_SIM_TIME:-false}"),
    "trace": ("ROS_TRACING", "${ROS_TRACING:-false}"),
}

EXCLUDED_ARGS = {"params"}


class GenerationError(Exception):
    pass


def run(cmd, cwd=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def load_config(path):
    with Path(path).open() as stream:
        config = yaml.safe_load(stream)
    required = ["repository_url", "ref", "output", "service_name", "namespace", "extends"]
    missing = [key for key in required if key not in config]
    if missing:
        raise GenerationError(f"missing required config keys: {', '.join(missing)}")
    return config


def checkout_repository(repository_url, ref, destination):
    run(["git", "clone", "--quiet", repository_url, str(destination)])
    run(["git", "checkout", "--quiet", ref], cwd=destination)


def is_commit_ref(ref):
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", ref))


def sanitize_ref(ref):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", ref)


def ref_exists(repo_path, ref_path):
    try:
        run(["git", "rev-parse", "--verify", "--quiet", ref_path], cwd=repo_path)
        return True
    except subprocess.CalledProcessError:
        return False


def package_version(repo_path):
    package_files = sorted(Path(repo_path).glob("*/package.xml"))
    if not package_files:
        raise GenerationError("no package.xml found one level below repository root")
    root = ET.parse(package_files[0]).getroot()
    version = root.findtext("version")
    if not version:
        raise GenerationError(f"no package version found in {package_files[0]}")
    return version


def image_tag(repo_path, ref):
    if ref_exists(repo_path, f"refs/tags/{ref}"):
        return ref
    if ref_exists(repo_path, f"refs/remotes/origin/{ref}") or ref_exists(repo_path, f"refs/heads/{ref}"):
        return f"latest_{sanitize_ref(ref)}_ci"
    if is_commit_ref(ref):
        return f"v{package_version(repo_path)}"
    return f"latest_{sanitize_ref(ref)}_ci"


def image_tag_from_ref_for_test(ref, ref_kind, version):
    if ref_kind == "tag":
        return ref
    if ref_kind == "branch":
        return f"latest_{sanitize_ref(ref)}_ci"
    if ref_kind == "commit":
        return f"v{version}"
    raise ValueError(f"unsupported ref kind: {ref_kind}")


def repository_name(repository_url):
    name = repository_url.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def image_name(config, tag):
    if "image" in config:
        return f"{config['image']}:{tag}"
    owner = config.get("image_owner", "openads-project")
    return f"ghcr.io/{owner}/{repository_name(config['repository_url'])}:{tag}"


def docker_ros_command(repo_path):
    workflow = Path(repo_path) / ".github" / "workflows" / "docker-ros.yml"
    with workflow.open() as stream:
        data = yaml.safe_load(stream)
    for job in data.get("jobs", {}).values():
        for step in job.get("steps", []):
            command = step.get("with", {}).get("command")
            if command:
                parts = shlex.split(command)
                if len(parts) >= 4 and parts[:2] == ["ros2", "launch"]:
                    return parts[2], parts[3]
    raise GenerationError(f"no ros2 launch command found in {workflow}")


def find_launch_file(repo_path, launch_file):
    matches = sorted(Path(repo_path).glob(f"**/launch/{launch_file}"))
    if not matches:
        matches = sorted(Path(repo_path).glob(f"**/{launch_file}"))
    if not matches:
        raise GenerationError(f"launch file not found: {launch_file}")
    return matches[0]


def simple_ast_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.List) and len(node.elts) == 1:
        return simple_ast_string(node.elts[0])
    if isinstance(node, ast.Tuple) and len(node.elts) == 1:
        return simple_ast_string(node.elts[0])
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "join":
            parts = [simple_ast_string(arg) for arg in node.args]
            if all(part is not None for part in parts):
                return os.path.join(*parts)
    return None


def launch_arguments(launch_file):
    tree = ast.parse(Path(launch_file).read_text())
    args = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name != "DeclareLaunchArgument" or not node.args:
            continue
        arg_name = simple_ast_string(node.args[0])
        if not arg_name:
            continue
        default = ""
        for keyword in node.keywords:
            if keyword.arg == "default_value":
                default = simple_ast_string(keyword.value) or ""
                break
        args[arg_name] = default
    return args


def env_name_for_arg(arg_name):
    return STANDARD_ENV.get(arg_name, (arg_name.upper(), None))[0]


def default_value_for_arg(arg_name, upstream_default, config):
    if arg_name == "namespace":
        return config["namespace"]
    if arg_name == "name":
        return config.get("name", repository_name(config["repository_url"]))
    standard = STANDARD_ENV.get(arg_name)
    if standard:
        return standard[1]
    return upstream_default


def parse_existing_environment(path):
    env = {}
    if not Path(path).exists():
        return env
    in_environment = False
    env_indent = None
    line_re = re.compile(r"^(\s+)([A-Z0-9_]+):\s*(.*?)(?:\s+#\s*(.*))?$")
    for line in Path(path).read_text().splitlines():
        stripped = line.strip()
        if stripped == "environment:":
            in_environment = True
            env_indent = None
            continue
        if not in_environment:
            continue
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if env_indent is None:
            env_indent = indent
        elif indent < env_indent:
            break
        match = line_re.match(line)
        if match:
            _, key, value, comment = match.groups()
            env[key] = {"value": value.strip(), "comment": (comment or "").strip()}
    return env


def generated_environment(launch_args, config, existing_env):
    overrides = config.get("environment_overrides", {}) or {}
    stale = sorted(key for key in existing_env if key not in {env_name_for_arg(arg) for arg in launch_args})
    entries = {}
    for arg_name, upstream_default in launch_args.items():
        if arg_name in EXCLUDED_ARGS:
            continue
        env_key = env_name_for_arg(arg_name)
        generated_default = default_value_for_arg(arg_name, upstream_default, config)
        value = overrides.get(env_key, generated_default)
        comment = None
        if env_key in overrides and upstream_default and value != upstream_default:
            comment = upstream_default
        existing = existing_env.get(env_key)
        if existing and existing["comment"] == upstream_default and existing["value"] != upstream_default:
            value = existing["value"]
            comment = upstream_default
        entries[arg_name] = {"env": env_key, "value": value, "default": upstream_default, "comment": comment}
    return entries, stale


def ordered_args(launch_args, config):
    preferred = ["namespace", "name"]
    inputs = config.get("input_arguments", []) or []
    outputs = config.get("output_arguments", []) or []
    configured_other = config.get("other_arguments", []) or []
    used = set(preferred + inputs + outputs + configured_other + list(EXCLUDED_ARGS))
    other = [arg for arg in launch_args if arg not in used]
    order = [arg for arg in preferred if arg in launch_args]
    order.extend(arg for arg in inputs if arg in launch_args)
    order.extend(arg for arg in outputs if arg in launch_args)
    order.extend(arg for arg in configured_other if arg in launch_args)
    order.extend(other)
    return order


def append_env_line(lines, key, value, comment=None):
    suffix = f" # {comment}" if comment else ""
    lines.append(f"      {key}: {value}{suffix}")


def render_compose(config, package, launch_file, launch_args, env_entries, tag):
    install_package = config.get("install_package", package)
    lines = [
        "services:",
        "",
        f"  {config['service_name']}:",
        "    extends:",
        f"      file: {config['extends']['file']}",
        f"      service: {config['extends']['service']}",
        f"    image: {image_name(config, tag)}",
        "    environment:",
        "      # --- name ------",
    ]

    groups = [
        ("# --- inputs ----", config.get("input_arguments", []) or []),
        ("# --- outputs ---", config.get("output_arguments", []) or []),
    ]

    for arg in ["namespace", "name"]:
        entry = env_entries.get(arg)
        if entry:
            append_env_line(lines, entry["env"], entry["value"], entry["comment"])
    for label, args in groups:
        present = [arg for arg in args if arg in env_entries]
        if present:
            lines.append(f"      {label}")
            for arg in present:
                entry = env_entries[arg]
                append_env_line(lines, entry["env"], entry["value"], entry["comment"])

    grouped = {"namespace", "name", *(config.get("input_arguments", []) or []), *(config.get("output_arguments", []) or [])}
    other = [arg for arg in ordered_args(launch_args, config) if arg not in grouped and arg in env_entries]
    if other:
        lines.append("      # --- other -----")
        for arg in other:
            entry = env_entries[arg]
            append_env_line(lines, entry["env"], entry["value"], entry["comment"])

    command_args = [arg for arg in ordered_args(launch_args, config) if arg in env_entries]
    lines.extend(
        [
            "    command:",
            "      - /bin/bash",
            "      - -ic",
            "      - |",
            f"        ros2 launch {package} {launch_file} \\",
        ]
    )
    for index, arg in enumerate(command_args):
        entry = env_entries[arg]
        slash = " \\" if index < len(command_args) - 1 else ""
        lines.append(f"          {arg}:=$${{{entry['env']}}}{slash}")

    lines.extend(
        [
            "    # volumes:",
            f"    #   - ./params.yml:/docker-ros/ws/install/{install_package}/share/{install_package}/config/params.yml",
            "",
        ]
    )
    return "\n".join(lines)


def generate(config_path):
    config_path = Path(config_path)
    config = load_config(config_path)
    output_path = Path(config["output"])
    existing_env = parse_existing_environment(output_path)
    with tempfile.TemporaryDirectory(prefix="compose-generation-") as temp_dir:
        repo_path = Path(temp_dir) / "repo"
        checkout_repository(config["repository_url"], config["ref"], repo_path)
        package, launch_name = docker_ros_command(repo_path)
        launch_path = find_launch_file(repo_path, launch_name)
        args = launch_arguments(launch_path)
        tag = image_tag(repo_path, config["ref"])
    env_entries, stale = generated_environment(args, config, existing_env)
    rendered = render_compose(config, package, launch_name, args, env_entries, tag)
    return rendered, stale


def main():
    parser = argparse.ArgumentParser(description="Generate docker-compose.yml from ROS module metadata.")
    parser.add_argument("config", help="module generation config")
    parser.add_argument("--check", action="store_true", help="fail if the generated file differs from the output")
    args = parser.parse_args()

    config = load_config(args.config)
    output_path = Path(config["output"])
    rendered, stale = generate(args.config)
    for key in stale:
        print(f"warning: stale environment variable in existing compose: {key}", file=sys.stderr)

    if args.check:
        current = output_path.read_text() if output_path.exists() else ""
        if current != rendered:
            diff = difflib.unified_diff(
                current.splitlines(True),
                rendered.splitlines(True),
                fromfile=str(output_path),
                tofile=f"{output_path} (generated)",
            )
            sys.stderr.writelines(diff)
            return 1
        return 0

    output_path.write_text(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
