#!/usr/bin/env sh
set -u

package=${1:-}
case "$package" in
    lynis|unattended-upgrades) ;;
    *)
        printf 'Unsupported package: %s\n' "$package" >&2
        exit 2
        ;;
esac

if [ "$(id -u)" != 0 ]; then
    printf 'Package installation requires root privileges.\n' >&2
    exit 1
fi
if ! command -v apt-get >/dev/null 2>&1; then
    printf 'apt-get is unavailable.\n' >&2
    exit 1
fi

DEBIAN_FRONTEND=noninteractive apt-get install -y "$package"