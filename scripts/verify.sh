#!/usr/bin/env sh
set -u

# Verification deliberately uses the same bounded observations as the initial run.
exec "$(dirname "$0")/discover_env.sh"
