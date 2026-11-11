"""Run with python3 -m unittest discover -s .buildkite -p 'test_*.py'."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import examples


class PipelineTest(unittest.TestCase):
    def test_discovery_unions_checks_and_preserves_exclusions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in (
                "examples/ruby/tools/format", "examples/ruby/tools/lint",
                "examples/ruby/test/nested", "examples/python/test",
                "examples/new-language/tools/lint",
            ):
                (root / directory).mkdir(parents=True)
            (root / "examples/ruby/test/nested/lint.bats").touch()
            (root / "examples/python/test/lint.bats").touch()
            self.assertEqual(examples.discover(root), {
                "examples/ruby": ["format", "lint", "integration"],
                "examples/new-language": ["lint"],
                "format": ["integration"],
            })
            steps = examples.pipeline(root)["steps"]
            self.assertEqual(len(steps), 3)
            self.assertTrue(all(step["depends_on"] == "setup" for step in steps))

    def test_runner_restores_fixtures_and_continues_after_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            root = temporary / "repo"
            fixture = root / "examples/nodejs/fixture"
            fixture.parent.mkdir(parents=True)
            fixture.write_text("original")
            for kind in ("format", "lint"):
                (fixture.parent / "tools" / kind).mkdir(parents=True)
            for args in (
                ["init", "--quiet"], ["add", "."],
                ["-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "--quiet", "-m", "fixture"],
            ):
                subprocess.run(["git", *args], cwd=root, check=True)
            # Git does not track empty directories.
            for kind in ("format", "lint"):
                (fixture.parent / "tools" / kind / "BUILD").touch()
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                            "commit", "--quiet", "-m", "tools"], cwd=root, check=True)
            tools = temporary / "bin"
            tools.mkdir()
            log = temporary / "calls.jsonl"
            for tool in ("bazel", "aspect"):
                path = tools / tool
                path.write_text("#!/usr/bin/env python3\n" + '''
import json, os, pathlib, sys
fixture = pathlib.Path('fixture')
assert fixture.read_text() == 'original', 'fixtures were not restored'
fixture.write_text('modified')
assert 'ASPECT_API_TOKEN' not in os.environ
assert 'ASPECT_WORKFLOWS_REMOTE_CACHE' not in os.environ
with open(os.environ['CALLS'], 'a') as log:
    log.write(json.dumps([pathlib.Path(sys.argv[0]).name, sys.argv[1:], os.environ.get('USE_BAZEL_VERSION')]) + '\\n')
sys.exit(1 if '--output_groups=rules_lint_human' in sys.argv else 0)
''')
                path.chmod(0o755)
            with patch.dict(os.environ, {
                "PATH": str(tools) + os.pathsep + os.environ["PATH"],
                "CALLS": str(log), "ASPECT_API_TOKEN": "test-token",
                "ASPECT_WORKFLOWS_REMOTE_CACHE": "test-endpoint",
            }), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(examples.run(root, "examples/nodejs", ["format", "lint"]), 1)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(len(calls), 6)
            self.assertTrue(all(call[2] == "8.x" for call in calls))
            for tool, args, _ in calls:
                if tool == "aspect":
                    self.assertEqual(args[1], "--remote=none")
                    for feature in ("buildkite-annotations", "artifact-upload", "workflows"):
                        self.assertIn(f"--{feature}:enabled=false", args)
                else:
                    self.assertEqual(args[:2], ["--nosystem_rc", "--nohome_rc"])
            self.assertEqual(fixture.read_text(), "original")


if __name__ == "__main__":
    unittest.main()
