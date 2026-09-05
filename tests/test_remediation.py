from pathlib import Path

from src.models import ActionType, EnvironmentInfo, RemediationAction
from src.remediation import execute_action


def _action(path: Path, option: str = "PermitRootLogin") -> RemediationAction:
    return RemediationAction(
        "action-1",
        "ssh-test",
        ActionType.SSH_SET_OPTION,
        "Harden SSH",
        {"path": str(path), "option": option, "value": "no"},
    )


def test_ssh_remediation_edits_only_discovered_temp_config(tmp_path: Path) -> None:
    config = tmp_path / "sshd_config"
    config.write_text("PermitRootLogin yes\nPasswordAuthentication yes\n", encoding="utf-8")
    environment = EnvironmentInfo(is_root=True, ssh_config_path=str(config))

    result = execute_action(_action(config), environment)

    assert result.success is True
    assert result.changed is True
    assert "PermitRootLogin no" in config.read_text(encoding="utf-8")
    assert config.with_name("sshd_config.audit-backup").is_file()


def test_remediation_rejects_path_other_than_discovered_config(tmp_path: Path) -> None:
    config = tmp_path / "sshd_config"
    other = tmp_path / "other"
    config.write_text("PermitRootLogin yes\n", encoding="utf-8")
    other.write_text("PermitRootLogin yes\n", encoding="utf-8")
    environment = EnvironmentInfo(is_root=True, ssh_config_path=str(config))

    result = execute_action(_action(other), environment)

    assert result.success is False
    assert other.read_text(encoding="utf-8") == "PermitRootLogin yes\n"


def test_remediation_is_blocked_without_root(tmp_path: Path) -> None:
    config = tmp_path / "sshd_config"
    config.write_text("PermitRootLogin yes\n", encoding="utf-8")

    result = execute_action(_action(config), EnvironmentInfo(ssh_config_path=str(config)))

    assert result.success is False
    assert result.changed is False