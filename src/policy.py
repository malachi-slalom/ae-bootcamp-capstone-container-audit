"""Central allowlist policy for bounded remediation actions."""

from __future__ import annotations

from pathlib import Path

from .models import ActionType, EnvironmentInfo

CONTAINER_ACTION_TYPES = frozenset(
    {
        ActionType.SSH_SET_OPTION,
        ActionType.SET_FILE_MODE,
        ActionType.INSTALL_UNATTENDED_UPGRADES,
        ActionType.INSTALL_LYNIS,
    }
)
NARROW_PERMISSION_PATHS = frozenset(
    {
        "/opt/demo/insecure.txt",
        "/srv/demo/public.txt",
    }
)


def action_type_allowed(action_type: ActionType, environment: EnvironmentInfo) -> bool:
    """Return whether this typed action is permitted in the current context."""
    return not environment.is_container or action_type in CONTAINER_ACTION_TYPES


def permission_path_allowed(path: str, environment: EnvironmentInfo) -> bool:
    """Allow only the discovered SSH config or fixed demo-owned files."""
    resolved = Path(path).resolve()
    if str(resolved) in NARROW_PERMISSION_PATHS:
        return True
    if environment.ssh_config_path is None:
        return False
    return resolved == Path(environment.ssh_config_path).resolve()
