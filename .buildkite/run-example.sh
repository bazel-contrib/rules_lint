#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
# Each job provisions its own tools. The setup job's filesystem is not shared
# with generated jobs, and the default agent image does not provide Aspect.
image="rules-lint-example-ci:${BUILDKITE_COMMIT:-$(git rev-parse HEAD)}"
echo '--- Build test image'
# Namespace uses a remote BuildKit driver. Explicitly export the result into
# the local Docker daemon; otherwise only the builder cache has the image.
docker build --load --progress=plain --file .buildkite/Dockerfile --tag "$image" .buildkite
echo '--- Run checks'
docker run --rm --init \
  --mount "type=bind,source=$PWD,target=/workspace" \
  --env USE_BAZEL_VERSION \
  "$image" python3 .buildkite/examples.py run "$@"
