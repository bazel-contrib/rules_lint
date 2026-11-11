#!/usr/bin/env python3
"""Discover the GHA example matrices and upload one Buildkite job per example."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


BATS_EXCLUDED = {"examples/python", "examples/cpp", "examples/java", "examples/shell"}
BAZEL_8 = {
    "format": {"examples/csharp", "examples/fsharp", "examples/nodejs"},
    "lint": {"examples/cpp", "examples/kotlin", "examples/nodejs"},
    "integration": {"examples/java", "examples/shell", "examples/kotlin", "format"},
}


def discover(root):
    checks = {}

    def add(folder, check):
        checks.setdefault(folder, []).append(check)

    # Same predicates as ci.yaml's find commands. Union the matrices so a
    # language gets one job even when it has both format and lint coverage.
    for tool in ("format", "lint"):
        for path in sorted((root / "examples").glob(f"**/tools/{tool}")):
            if path.is_dir():
                add(path.parent.parent.relative_to(root).as_posix(), tool)
    folders = {
        path.relative_to(root).as_posix().split("/test/", 1)[0]
        for path in (root / "examples").glob("**/test/**/*.bats")
    }
    for folder in sorted((folders - BATS_EXCLUDED) | {"format"}):
        add(folder, "integration")
    return checks


def pipeline(root):
    groups = [
        {"group": ":books: Examples", "key": "examples", "steps": []},
        {"group": ":test_tube: Ruleset tests", "key": "ruleset-tests", "steps": []},
    ]
    for folder, checks in sorted(discover(root).items()):
        group = groups[0] if folder.startswith("examples/") else groups[1]
        group["steps"].append({
            "label": f":test_tube: {folder.removeprefix('examples/')}",
            "key": folder.replace("/", "-"),
            "command": shlex.join([
                "bash", ".buildkite/run-example.sh", folder, *checks,
            ]),
            "timeout_in_minutes": 60,
            "depends_on": "setup",
        })
    return {
        "steps": [group for group in groups if group["steps"]],
    }


def run(root, folder, checks):
    import shutil

    expected = discover(root)
    if folder not in expected or checks != expected[folder]:
        raise ValueError("Expected a discovered example and its complete check list")
    for tool in ("git", "bazel", "aspect", "bats"):
        if tool == "bats" and "integration" not in checks:
            continue
        if not shutil.which(tool):
            raise RuntimeError(f"Required agent tool missing: {tool}")

    env = dict(os.environ, CI="true", BUILDKITE="true")
    # Buildkite owns orchestration. Never inherit Aspect service credentials or
    # Workflows runner endpoints from an agent's environment.
    for name in list(env):
        if name.startswith("ASPECT_WORKFLOWS_") or name in {
            "ASPECT_API_TOKEN", "ASPECT_CLOUD_API_TOKEN",
        }:
            del env[name]
    original_version = env.pop("USE_BAZEL_VERSION", None)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="rules-lint-buildkite-") as temporary:
        temporary = Path(temporary)
        checkout = temporary / "checkout"
        subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(root), str(checkout)], check=True)
        subprocess.run(["git", "checkout", "--quiet", "--detach", commit], cwd=checkout, check=True)
        wrappers = temporary / "bin"
        wrappers.mkdir()
        # Bats also invokes these tools. Apply the same policy to every call,
        # including nested calls, without modifying any test fixtures.
        for tool, body in {
            "aspect": 'task="$1"; shift\nexec {real} "$task" --remote=none --buildkite-annotations:enabled=false --artifact-upload:enabled=false --workflows:enabled=false "$@"\n',
            "bazel": 'exec {real} --nosystem_rc --nohome_rc --bazelrc={rc} "$@"\n',
        }.items():
            path = wrappers / tool
            # Bats uses FD 3 for TAP output. A newly started Bazel server must
            # not inherit it, or Bats waits for EOF after all tests finish.
            path.write_text("#!/usr/bin/env bash\nset -euo pipefail\nexec 3>&-\n" + body.format(
                real=shlex.quote(shutil.which(tool)),
                rc=shlex.quote(str(root / ".buildkite/ci.bazelrc")),
            ))
            path.chmod(0o755)
        env["PATH"] = str(wrappers) + os.pathsep + env["PATH"]

        commands = {
            "format": [
                ["bazel", "run", "//tools/format"],
                ["aspect", "format", "--scope=all", "--severity=warn"],
            ],
            "lint": [
                ["bazel", "build", "--config=lint", "--output_groups=rules_lint_human", "//..."],
                ["bazel", "build", "--config=lint", "--output_groups=rules_lint_patch", "--@rules_lint//lint:fix", "//..."],
                ["aspect", "lint", "--strategy=soft", "--", "//..."],
                ["aspect", "lint", "--fix", "--strategy=soft", "--", "//..."],
            ],
            "integration": [["bats", "./test"]],
        }
        failed = False
        for check in checks:
            env.pop("USE_BAZEL_VERSION", None)
            if folder in BAZEL_8[check]:
                env["USE_BAZEL_VERSION"] = "8.x"
            elif original_version:
                env["USE_BAZEL_VERSION"] = original_version
            for command in commands[check]:
                print(f"--- {folder}: {shlex.join(command)}", flush=True)
                # GHA uses independent checkouts. Restore fixtures between
                # commands, but only inside our disposable clone: --fix and
                # format intentionally mutate source files.
                subprocess.run(["git", "reset", "--hard", "--quiet", commit], cwd=checkout, check=True)
                subprocess.run(["git", "clean", "-fd", "--quiet"], cwd=checkout, check=True)
                result = subprocess.run(command, cwd=checkout / folder, env=env)
                failed |= result.returncode != 0
        return int(failed)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    if len(sys.argv) == 1:
        print(json.dumps(pipeline(root), indent=2))
    elif len(sys.argv) >= 4 and sys.argv[1] == "run":
        sys.exit(run(root, sys.argv[2], sys.argv[3:]))
    else:
        sys.exit("Usage: examples.py [run FOLDER CHECK ...]")
