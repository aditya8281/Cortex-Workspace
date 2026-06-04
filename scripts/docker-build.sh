#!/usr/bin/env bash

set -euo pipefail

if [ ! -f .env ] && [ -f .env.docker ]; then
  cp .env.docker .env
fi

docker compose build
