#!/bin/bash
set -e
cd "${0%/*}/.."

TAG="${VERSION:-latest}"
IMAGE="${IMAGE:-f25e-job-template}"
JOBNAME="${JOBNAME:-hello}"

echo "Running image '$IMAGE:$TAG'"
echo "Running job '$JOBNAME'"
echo "$(pwd)"

set +e
docker run \
  --mount type=bind,source=$(pwd)/config_examples/hello_minimal.yaml,target=/etc/f25e/config.yaml,readonly \
  --entrypoint web \
  --rm \
  $IMAGE

set -e

RESULT=$?
exit $RESULT
