# Example CI

Set the Buildkite pipeline's initial steps to:

```yaml
steps:
  - command: buildkite-agent pipeline upload .buildkite/pipeline.yml
```

The setup step discovers `examples/**/tools/format`,
`examples/**/tools/lint`, and `examples/**/test/**/*.bats`, matching
`.github/workflows/ci.yaml`. It uploads one job per discovered example,
plus the shared `format` integration suite. No language list to maintain.

Each job runs both Bazel and Aspect CLI format/lint entry points where
present, and Bats where enabled in GHA. Commands get pristine fixtures in
a disposable local clone; source files deliberately contain lint and format
violations. Checks continue after failures so the job shows all results.

Use a Linux agent queue with Python 3.9+, Git, Bazelisk available as `bazel`,
Aspect CLI v2026.38.3 (matching GHA), Bats 1.8.2, bats-support 0.3.0,
and bats-assert 2.1.0. Put the Bats libraries on `BATS_LIB_PATH`.
The setup agent only needs Python and `buildkite-agent`.
Jobs inherit the pipeline's default queue.

The C++ formatter currently requires Ubuntu 22.04 with `libtinfo5`, exactly
as GHA does: the pinned clang-format binary's dependency is unavailable on
newer Ubuntu. Provision that dependency in the agent image; this pipeline
does not install packages with sudo. Existing Bazel 8 exceptions and Bats
exclusions are copied from GHA, whose FIXME records unresolved failures in
Python, C++, Java, and Shell Bats suites.

No Aspect Workflows runner or credentials are needed. CLI invocations use
`--remote=none`, including those inside Bats. Buildkite disables the repo's
Aspect artifact/GitHub reporting features and Workflows feature. Bazel
ignores agent-wide system/home rc files; workspace rc files still apply.

Preview generated jobs without uploading:

```sh
python3 .buildkite/examples.py
```

Check discovery and runner behavior:

```sh
python3 -m unittest discover -s .buildkite -p 'test_*.py'
```

This pipeline covers the example matrices and shared formatter Bats suite.
Root tests, macOS Java tests, Python compatibility, link checking, BCR patch
validation, and releases remain in GHA.
