#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="agentic-security-demo:latest"
CONTAINER_NAME="agentic-security-demo"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[*] Building demo image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" -f "${REPO_ROOT}/docker/demo/Dockerfile" "${REPO_ROOT}"

# Remove existing container if present
if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "[*] Removing existing container: ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

echo "[*] Starting demo container: ${CONTAINER_NAME}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  --hostname "${CONTAINER_NAME}" \
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
echo "Quick checks inside the container:"
echo "  cat /etc/os-release"
echo "  grep -E '^(PermitRootLogin|PasswordAuthentication)' /etc/ssh/sshd_config"
echo "  ls -l /opt/demo/insecure.txt"
echo
echo "To run your audit tooling inside the container, you can either:"
echo "  1. docker cp your project into the container and run it there, or"
echo "  2. mount your repo into a new container invocation, or"
echo "  3. exec into the container and install/copy what you need."