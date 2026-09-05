"""Bounded security probes with no system mutation."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

from .models import EnvironmentInfo, RawCheck

ROOT = Path(__file__).resolve().parents[1]
DEMO_FILE_PATHS = {
    "world_writable_opt_demo_insecure": Path("/opt/demo/insecure.txt"),
    "world_writable_srv_demo_public": Path("/srv/demo/public.txt"),
}
LOGIN_BANNER_PATHS = {
    "login_banner_etc_issue": Path("/etc/issue"),
    "login_banner_etc_issue_net": Path("/etc/issue.net"),
}
WEAK_PROFILE_PATH = Path("/opt/demo/weak_profile.sh")


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


def _package_status(environment: EnvironmentInfo, package: str) -> str:
    if environment.package_manager != "apt-get":
        return "unknown"
    try:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", package],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return "installed" if "install ok installed" in result.stdout else "missing"


def _file_mode_check(check_id: str, path: Path) -> RawCheck:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        return RawCheck(check_id, "missing", f"{path} does not exist", {"path": str(path)})
    except OSError as error:
        return RawCheck(check_id, "unknown", f"Could not inspect {path}: {error}", {"path": str(path)})
    status = "world_writable" if mode & stat.S_IWOTH else "secure"
    return RawCheck(
        check_id,
        status,
        f"{path} mode is {mode:04o}",
        {"path": str(path), "mode": mode},
    )


def _banner_check(check_id: str, path: Path) -> RawCheck:
    try:
        status = "configured" if path.read_text(encoding="utf-8", errors="replace").strip() else "empty"
    except FileNotFoundError:
        status = "missing"
    except OSError as error:
        return RawCheck(check_id, "unknown", f"Could not inspect {path}: {error}", {"path": str(path)})
    return RawCheck(check_id, status, f"Login banner {path} is {status}", {"path": str(path)})


def _umask_check(path: Path) -> RawCheck:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return RawCheck("weak_demo_umask", "missing", f"{path} does not exist", {"path": str(path)})
    except OSError as error:
        return RawCheck("weak_demo_umask", "unknown", f"Could not inspect {path}: {error}", {"path": str(path)})

    matches = re.findall(r"(?im)^\s*umask\s+([0-7]{1,4})\s*(?:#.*)?$", content)
    if not matches:
        return RawCheck("weak_demo_umask", "unset", f"No numeric umask was found in {path}", {"path": str(path)})
    value = int(matches[-1], 8)
    status = "weak" if value & 0o022 != 0o022 else "secure"
    return RawCheck(
        "weak_demo_umask",
        status,
        f"{path} sets umask {value:03o}",
        {"path": str(path), "umask": value},
    )


def _listener_check(environment: EnvironmentInfo, port: int) -> RawCheck:
    command = None
    if environment.network_tool == "ss":
        command = ["ss", "-lnt"]
    elif environment.network_tool == "netstat":
        command = ["netstat", "-lnt"]
    if command is None:
        return RawCheck(f"listener_port_{port}", "unknown", "No supported network inspection tool is available")
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return RawCheck(f"listener_port_{port}", "unknown", f"Listener inspection failed: {error}")
    if result.returncode != 0:
        return RawCheck(f"listener_port_{port}", "unknown", f"Listener inspection exited {result.returncode}")
    pattern = re.compile(rf"(?:^|\s)(?:\[[^\]]+\]|[^\s:]*):{port}(?:\s|$)")
    matching_lines = [line.strip() for line in result.stdout.splitlines() if pattern.search(line)]
    status = "listening" if matching_lines else "not_listening"
    evidence = matching_lines[0] if matching_lines else f"No TCP listener was detected on port {port}"
    return RawCheck(f"listener_port_{port}", status, evidence, {"port": port})


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

    unattended_status = _package_status(environment, "unattended-upgrades")
    checks.append(
        RawCheck(
            "unattended_upgrades",
            unattended_status,
            f"unattended-upgrades package status: {unattended_status}",
        )
    )

    aide_status = _package_status(environment, "aide")
    checks.append(
        RawCheck(
            "aide",
            aide_status,
            f"aide package status: {aide_status}",
        )
    )

    checks.extend(_file_mode_check(check_id, path) for check_id, path in DEMO_FILE_PATHS.items())
    checks.extend(_banner_check(check_id, path) for check_id, path in LOGIN_BANNER_PATHS.items())
    checks.append(_umask_check(WEAK_PROFILE_PATH))
    checks.append(_listener_check(environment, 8080))

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