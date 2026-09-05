#!/usr/bin/env bash
set -euo pipefail

mkdir -p /run/sshd /var/run/sshd

# Start sshd if available; don't fail the container if it cannot start
if command -v /usr/sbin/sshd >/dev/null 2>&1; then
  /usr/sbin/sshd || true
fi

echo "Demo Debian security container is running."
echo "Intentionally insecure settings:"
echo "- /etc/ssh/sshd_config may allow root login and password auth"
echo "- /opt/demo/insecure.txt is world-writable"

# Keep container alive
exec tail -f /dev/null