"""Execution boundary for explicitly allowlisted remediations."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .models import ActionResult, ActionType, EnvironmentInfo, RemediationAction
from .policy import action_type_allowed, permission_path_allowed

ROOT = Path(__file__).resolve().parents[1]
SSH_OPTIONS = {"PermitRootLogin", "PasswordAuthentication"}
PACKAGES = {
    ActionType.INSTALL_LYNIS: "lynis",
    ActionType.INSTALL_UNATTENDED_UPGRADES: "unattended-upgrades",
}


def _authorized_ssh_path(action: RemediationAction, environment: EnvironmentInfo) -> Path | None:
    requested = action.parameters.get("path")
    if not isinstance(requested, str) or environment.ssh_config_path is None:
        return None
    path = Path(requested).resolve()
    expected = Path(environment.ssh_config_path).resolve()
    return path if path == expected and path.is_file() else None


def _authorized_permission_path(
    action: RemediationAction, environment: EnvironmentInfo
) -> Path | None:
    requested = action.parameters.get("path")
    if not isinstance(requested, str) or not permission_path_allowed(requested, environment):
        return None
    path = Path(requested).resolve()
    return path if path.is_file() else None


def _set_ssh_option(path: Path, option: str, value: str) -> tuple[bool, str]:
    if option not in SSH_OPTIONS or value != "no":
        return False, "SSH option or value is not allowlisted"

    original = path.read_text(encoding="utf-8", errors="replace")
    lines = original.splitlines(keepends=True)
    replacement = f"{option} {value}\n"
    updated: list[str] = []
    replaced = False
    inserted = False
    in_match_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("match "):
            if not replaced and not inserted:
                updated.append(replacement)
                inserted = True
            in_match_block = True
        parts = stripped.split(None, 1)
        if not in_match_block and len(parts) == 2 and parts[0].lower() == option.lower():
            updated.append(replacement)
            replaced = True
        else:
            updated.append(line)
    if not replaced and not inserted:
        if updated and not updated[-1].endswith("\n"):
            updated[-1] += "\n"
        updated.append(replacement)

    new_content = "".join(updated)
    if new_content == original:
        return False, f"{option} is already set to {value}"

    original_mode = path.stat().st_mode & 0o7777
    backup = path.with_name(f"{path.name}.audit-backup")
    shutil.copy2(path, backup)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as temporary:
            temporary.write(new_content)
            temporary_name = temporary.name
        os.chmod(temporary_name, original_mode)
        os.replace(temporary_name, path)

        sshd = shutil.which("sshd")
        if sshd:
            validation = subprocess.run(
                [sshd, "-t", "-f", str(path)], capture_output=True, text=True, check=False
            )
            no_host_keys = "no hostkeys available" in validation.stderr.lower()
            if validation.returncode != 0 and not no_host_keys:
                shutil.copy2(backup, path)
                return False, f"SSH validation failed; restored backup: {validation.stderr.strip()}"
    finally:
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()

    return True, f"Set {option} to {value}; backup: {backup}"


def execute_action(action: RemediationAction, environment: EnvironmentInfo) -> ActionResult:
    if not environment.is_root:
        return ActionResult(action.action_id, False, False, "Remediation requires root privileges")
    if not action_type_allowed(action.action_type, environment):
        return ActionResult(
            action.action_id,
            False,
            False,
            "Action type is not approved for in-container remediation",
        )

    if action.action_type == ActionType.SSH_SET_OPTION:
        path = _authorized_ssh_path(action, environment)
        option = action.parameters.get("option")
        value = action.parameters.get("value")
        if path is None or not isinstance(option, str) or not isinstance(value, str):
            return ActionResult(action.action_id, False, False, "SSH target is not allowlisted")
        changed, message = _set_ssh_option(path, option, value)
        success = changed or "already set" in message
        return ActionResult(action.action_id, success, changed, message)

    if action.action_type == ActionType.SET_FILE_MODE:
        path = _authorized_permission_path(action, environment)
        mode = action.parameters.get("mode")
        if path is None or not isinstance(mode, int) or mode < 0 or mode > 0o777:
            return ActionResult(action.action_id, False, False, "File permission target is not allowlisted")
        current_mode = path.stat().st_mode & 0o777
        if mode & 0o022:
            return ActionResult(action.action_id, False, False, "Requested mode remains group/world writable")
        if current_mode == mode:
            return ActionResult(action.action_id, True, False, f"Mode is already {mode:04o}")
        path.chmod(mode)
        verified = path.stat().st_mode & 0o777 == mode
        return ActionResult(action.action_id, verified, verified, f"Set mode to {mode:04o}" if verified else "Mode verification failed")

    package = PACKAGES.get(action.action_type)
    if package and environment.package_manager == "apt-get":
        result = subprocess.run(
            ["sh", str(ROOT / "scripts" / "maybe_install_lynis.sh"), package],
            capture_output=True,
            text=True,
            check=False,
        )
        message = result.stdout.strip() or result.stderr.strip() or f"Installer exited {result.returncode}"
        if result.returncode != 0:
            return ActionResult(action.action_id, False, False, message)
        verification = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", package],
            capture_output=True,
            text=True,
            check=False,
        )
        verified = "install ok installed" in verification.stdout
        return ActionResult(action.action_id, verified, verified, message if verified else "Package verification failed")

    return ActionResult(action.action_id, False, False, "Action type is not supported in this environment")


def execute_actions(actions: list[RemediationAction], environment: EnvironmentInfo) -> list[ActionResult]:
    return [execute_action(action, environment) for action in actions]