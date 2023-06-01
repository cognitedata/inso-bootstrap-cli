#!/bin/bash
set -e
cd "${0%/*}/.."

TAG="${VERSION:-latest}"
IMAGE="${IMAGE:-bootstrap-cli}"

echo "Running image '$IMAGE:$TAG'"
echo "$(pwd)"

set +e
# adopt the parameters and config as you need
docker run \
  --mount type=bind,source=$(pwd)/configs/config-deploy-example-v3.yml,target=/etc/config.yaml,readonly \
  --entrypoint run \
  --env-file=.env_trading_root \
  --rm \
  $IMAGE \
  --dry-run \
  deploy \
  /etc/config.yaml

set -e

RESULT=$?
exit $RESULT
