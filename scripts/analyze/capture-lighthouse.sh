#!/usr/bin/env bash
# Capture N Lighthouse runs per approach against the preview server.
#
# A single Lighthouse run is an anecdote -- scores swing 5-15% between runs.
# This captures ITER runs per table into inputs/lighthouse/runs/, which
# aggregate_lighthouse.py then medians. Start `pnpm preview` (port 4173)
# in another shell first.
#
# Usage: ITER=5 scripts/analyze/capture-lighthouse.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT=scripts/analyze/inputs/lighthouse/runs
ITER=${ITER:-5}
BASE_URL=${BASE_URL:-http://localhost:4173}

mkdir -p "$OUT"

for app in basic primevue tanstack; do
  for i in $(seq 1 "$ITER"); do
    echo ">>> $app run $i/$ITER"
    pnpm dlx lighthouse@13 "$BASE_URL/benchmark/${app}-table" \
      --preset=desktop --only-categories=performance \
      --throttling.cpuSlowdownMultiplier=4 \
      --output=json --output-path="$OUT/${app}-${i}.json" \
      --chrome-flags='--headless=new --disable-gpu --incognito' \
      --quiet
  done
done

echo "Captured $ITER runs per approach into $OUT"
