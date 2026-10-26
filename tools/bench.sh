#!/bin/sh
set -eu

ROOT=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

RUNS=50

measure() {
    label=$1
    cmd=$2
    total=0
    i=0
    while [ "$i" -lt "$RUNS" ]; do
        start=$(date +%s%N)
        eval "$cmd" >/dev/null 2>&1
        end=$(date +%s%N)
        total=$((total + (end - start)))
        i=$((i + 1))
    done
    avg_ms=$(awk -v t="$total" -v r="$RUNS" 'BEGIN { printf "%.2f", (t / r) / 1000000 }')
    printf "%s: %s ms\\n" "$label" "$avg_ms"
}

if command -v hyperfine >/dev/null 2>&1; then
    hyperfine --runs "$RUNS" \
        'python3 -I -S -c pass' \
        'bin/kao list >/dev/null' \
        'bin/kao --random >/dev/null'
else
    measure "python3 -I -S -c pass" "python3 -I -S -c pass"
    measure "bin/kao list" "bin/kao list >/dev/null"
    measure "bin/kao --random" "bin/kao --random >/dev/null"
fi
