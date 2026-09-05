"""Environment discovery through the bounded project shell script."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .models import EnvironmentInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCRIPT = ROOT / "scripts" / "discover_env.sh"


def parse_discovery(output: str, limitation: str | None = None) -> EnvironmentInfo:
    values: dict[str, str] = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()

    container_type = values.get("CONTAINER_TYPE", "none")
    lynis = values.get("LYNIS", "none")
    ssh_config = values.get("SSH_CONFIG", "none")
    package_manager = values.get("PACKAGE_MANAGER", "none")
    network_tool = values.get("NETWORK_TOOL", "none")

    return EnvironmentInfo(
        os_id=values.get("OS_ID", "unknown"),
        os_version=values.get("OS_VERSION", "unknown"),
        kernel=values.get("KERNEL", "unknown"),
        user=values.get("USER", "unknown"),
        is_root=values.get("IS_ROOT") == "true",
        is_container=container_type != "none",
        container_type=container_type,
        lynis_available=lynis != "none",
        ssh_config_path=None if ssh_config == "none" else ssh_config,
        package_manager=None if package_manager == "none" else package_manager,
        network_tool=None if network_tool == "none" else network_tool,
        limitations=(limitation,) if limitation else (),
    )


def discover_environment(script: Path = DEFAULT_SCRIPT) -> EnvironmentInfo:
    if not script.is_file():
        return parse_discovery("", f"Discovery script not found: {script}")

    try:
        result = subprocess.run(
            ["sh", str(script)], capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return parse_discovery("", f"Discovery failed: {error}")

    limitation = None
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit code {result.returncode}"
        limitation = f"Discovery was incomplete: {detail}"
    return parse_discovery(result.stdout, limitation)