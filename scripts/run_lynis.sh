#!/usr/bin/env sh
set -u

if ! command -v lynis >/dev/null 2>&1; then
	printf 'STATUS=unavailable\n'
	exit 0
fi

printf 'STATUS=available\n'
lynis audit system --quick --no-colors 2>&1
