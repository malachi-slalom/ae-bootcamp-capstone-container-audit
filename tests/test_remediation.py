from pathlib import Path

import src.policy as policy_module
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


def test_ssh_remediation_is_allowed_in_root_container(tmp_path: Path) -> None:
    config = tmp_path / "sshd_config"
    config.write_text("PermitRootLogin yes\n", encoding="utf-8")
    environment = EnvironmentInfo(
        is_root=True, is_container=True, ssh_config_path=str(config)
    )

    result = execute_action(_action(config), environment)

    assert result.success is True
    assert "PermitRootLogin no" in config.read_text(encoding="utf-8")


def test_exact_demo_file_permission_fix_is_allowed_in_container(
    tmp_path: Path, monkeypatch
) -> None:
    target = tmp_path / "insecure.txt"
    target.write_text("demo\n", encoding="utf-8")
    target.chmod(0o666)
    monkeypatch.setattr(
        policy_module, "NARROW_PERMISSION_PATHS", frozenset({str(target.resolve())})
    )
    action = RemediationAction(
        "action-1",
        "world_writable_opt_demo_insecure",
        ActionType.SET_FILE_MODE,
        "Remove group and world write permissions.",
        {"path": str(target), "mode": 0o644},
    )

    result = execute_action(
        action, EnvironmentInfo(is_root=True, is_container=True)
    )

    assert result.success is True
    assert target.stat().st_mode & 0o777 == 0o644


def test_file_permission_fix_rejects_unlisted_path(tmp_path: Path) -> None:
    target = tmp_path / "unlisted.txt"
    target.write_text("demo\n", encoding="utf-8")
    target.chmod(0o666)
    action = RemediationAction(
        "action-1",
        "unsafe-path",
        ActionType.SET_FILE_MODE,
        "Change permissions.",
        {"path": str(target), "mode": 0o644},
    )

    result = execute_action(action, EnvironmentInfo(is_root=True, is_container=True))

    assert result.success is False
    assert target.stat().st_mode & 0o777 == 0o666