#!/usr/bin/env bash
set -euo pipefail

mkdir -p /run/sshd /var/run/sshd

# Start sshd if available; don't fail if it cannot start in the container
if command -v /usr/sbin/sshd >/dev/null 2>&1; then
  /usr/sbin/sshd || true
fi

# Start a harmless HTTP listener on 8080 for demo/network visibility
if command -v python3 >/dev/null 2>&1; then
  cd /opt/demo/www
  nohup python3 -m http.server 8080 >/tmp/demo-http.log 2>&1 &
fi

echo "Demo Debian security container is running."
echo
echo "Included tools:"
echo "- lynis"
echo "- openssh-server"
echo "- python3"
echo
echo "Intentional demo findings:"
echo "- SSH config may allow root login"
echo "- SSH config may allow password authentication"
echo "- /opt/demo/insecure.txt is world-writable"
echo "- /srv/demo/public.txt is world-writable"
echo "- weak umask file at /opt/demo/weak_profile.sh"
echo "- unattended-upgrades is not installed"
echo "- aide is not installed"
echo "- login banner files are empty"
echo "- extra listening HTTP port on 8080"
echo
echo "Container ready."

exec tail -f /dev/null