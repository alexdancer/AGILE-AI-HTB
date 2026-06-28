#!/usr/bin/env sh
set -eu

compose() {
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    docker compose "$@"
  fi
}

cleanup() {
  compose down >/dev/null 2>&1 || true
}

wait_for_health() {
  i=0
  while [ "$i" -lt 30 ]; do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
      return 0
    fi
    i=$((i + 1))
    sleep 1
  done
  curl -fsS http://localhost:8000/health
}

echo "docker smoke will stop and recreate this repo's Compose service; named volumes are kept" >&2

trap cleanup EXIT INT TERM

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon unavailable; start Docker and rerun scripts/docker-smoke.sh" >&2
  exit 1
fi

cleanup
compose up -d --build agile-ai-htb
wait_for_health
curl -fsS http://localhost:8000/login >/dev/null
compose exec -T agile-ai-htb test -s /data/harness.db
compose down >/dev/null
compose up -d --no-build agile-ai-htb
wait_for_health
compose exec -T agile-ai-htb test -s /data/harness.db

echo "docker smoke ok"
