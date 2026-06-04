#!/usr/bin/env bash

set -euo pipefail

if [ ! -f .env ] && [ -f .env.docker ]; then
  cp .env.docker .env
elif [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
fi

docker compose up -d --build
