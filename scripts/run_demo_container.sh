#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="agentic-security-demo:latest"
CONTAINER_NAME="agentic-security-demo"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[*] Building demo image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" -f "${REPO_ROOT}/docker/demo/Dockerfile" "${REPO_ROOT}"

if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "[*] Removing existing container: ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

echo "[*] Starting demo container: ${CONTAINER_NAME}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  --hostname "${CONTAINER_NAME}" \
  -v "${REPO_ROOT}:/workspace" \
  -w /workspace \
  "${IMAGE_NAME}" >/dev/null

echo
echo "[+] Container started."
echo "[+] Name: ${CONTAINER_NAME}"
echo
echo "Useful commands:"
echo "  docker exec -it ${CONTAINER_NAME} bash"
echo "  docker logs ${CONTAINER_NAME}"
echo "  docker rm -f ${CONTAINER_NAME}"
echo
echo "Suggested demo commands inside the container:"
echo "  cd /workspace"
echo "  lynis audit system --quick || true"
echo "  grep -E '^(PermitRootLogin|PasswordAuthentication)' /etc/ssh/sshd_config"
echo "  ls -l /opt/demo/insecure.txt /srv/demo/public.txt"
echo "  cat /opt/demo/weak_profile.sh"
echo "  ss -tulpn || netstat -tulpn || true"
echo "  dpkg -l | grep -E 'unattended-upgrades|aide' || true"
echo "  python3 -m src.main"