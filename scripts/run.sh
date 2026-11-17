#!/usr/bin/env bash

# Launch Astro Assist from the repository root.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

python3 run.py