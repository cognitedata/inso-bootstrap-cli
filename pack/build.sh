#!/bin/bash
set -e
cd "${0%/*}/.."

TAG="${VERSION:-latest}"
IMAGE="${IMAGE:-bootstrap-cli}"
PUBLISH="${PUBLISH:-false}"

echo "Building image $IMAGE:$TAG"

set +e
if $PUBLISH -eq "true"; then
  # building a poetry project, which provides `bootstrap-cli` as a command
  # keeping `logs/*` in the image, so that the `bootstrap-cli` logging can write to it
  pack build "$IMAGE:$TAG" --buildpack paketo-buildpacks/python \
                          --builder paketobuildpacks/builder:base \
                          --buildpack paketo-buildpacks/source-removal \
                          --default-process=github \
                          --env BP_INCLUDE_FILES='src/*:logs/*' \
                          --env BP_POETRY_VERSION='1.3.2' \
                          --publish
else
  # local build
  pack build "$IMAGE:$TAG" --buildpack paketo-buildpacks/python \
                          --builder paketobuildpacks/builder:base \
                          --buildpack paketo-buildpacks/source-removal \
                          --default-process=run \
                          --env BP_INCLUDE_FILES='src/*:logs/*' \
                          --env BP_POETRY_VERSION='1.3.2' \
                          --env BP_LIVE_RELOAD_ENABLED=true
fi
set -e

RESULT=$?
exit $RESULT
