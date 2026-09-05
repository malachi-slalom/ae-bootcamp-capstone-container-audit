"""Bounded security probes with no system mutation."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

from .models import EnvironmentInfo, RawCheck

ROOT = Path(__file__).resolve().parents[1]


def _read_sshd_options(path: Path) -> dict[str, str]:
    options: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return options
    for line in lines:
        content = line.strip()
        if content.lower().startswith("match "):
            break
        if not content or content.startswith("#"):
            continue
        parts = content.split(None, 1)
        if len(parts) == 2:
            options[parts[0].lower()] = parts[1].strip().lower()
    return options


def run_fallback_checks(environment: EnvironmentInfo) -> list[RawCheck]:
    checks: list[RawCheck] = []

    if environment.ssh_config_path:
        path = Path(environment.ssh_config_path)
        options = _read_sshd_options(path)
        checks.extend(
            [
                RawCheck(
                    "ssh_permit_root_login",
                    options.get("permitrootlogin", "unset"),
                    f"PermitRootLogin is {options.get('permitrootlogin', 'not explicitly set')} in {path}",
                    {"path": str(path), "option": "PermitRootLogin"},
                ),
                RawCheck(
                    "ssh_password_authentication",
                    options.get("passwordauthentication", "unset"),
                    f"PasswordAuthentication is {options.get('passwordauthentication', 'not explicitly set')} in {path}",
                    {"path": str(path), "option": "PasswordAuthentication"},
                ),
            ]
        )
        try:
            mode = stat.S_IMODE(path.stat().st_mode)
            checks.append(
                RawCheck(
                    "ssh_config_permissions",
                    "secure" if mode & 0o022 == 0 else "writable",
                    f"{path} mode is {mode:04o}",
                    {"path": str(path), "mode": mode},
                )
            )
        except OSError as error:
            checks.append(RawCheck("ssh_config_permissions", "unknown", str(error)))
    else:
        checks.append(RawCheck("ssh_config", "unavailable", "No SSH server config was found"))

    unattended_status = "unknown"
    if environment.package_manager == "apt-get":
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", "unattended-upgrades"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            unattended_status = "installed" if "install ok installed" in result.stdout else "missing"
        except (OSError, subprocess.TimeoutExpired):
            unattended_status = "unknown"
    checks.append(
        RawCheck(
            "unattended_upgrades",
            unattended_status,
            f"unattended-upgrades package status: {unattended_status}",
        )
    )

    checks.append(
        RawCheck(
            "lynis_availability",
            "available" if environment.lynis_available else "missing",
            "Lynis is available" if environment.lynis_available else "Lynis is not installed; fallback checks were used",
        )
    )
    checks.append(
        RawCheck(
            "privilege",
            "root" if environment.is_root else "unprivileged",
            f"Audit is running as {environment.user} (uid {os.geteuid()})",
        )
    )
    return checks


def run_lynis(environment: EnvironmentInfo) -> list[RawCheck]:
    if not environment.lynis_available:
        return []
    try:
        result = subprocess.run(
            ["sh", str(ROOT / "scripts" / "run_lynis.sh")],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return [RawCheck("lynis_run", "failed", f"Lynis execution failed: {error}")]

    suggestions = [
        line.strip() for line in result.stdout.splitlines() if "suggestion" in line.lower()
    ]
    status = "completed" if result.returncode == 0 else "failed"
    evidence = f"Lynis {status} with {len(suggestions)} suggestion lines"
    return [RawCheck("lynis_run", status, evidence, {"suggestions": suggestions[:20]})]


def run_checks(environment: EnvironmentInfo) -> list[RawCheck]:
    return run_fallback_checks(environment) + run_lynis(environment)