from pathlib import Path

from src.checks import run_fallback_checks
from src.models import ActionType, Applicability, EnvironmentInfo
from src.parser import normalize_findings


def test_fallback_checks_and_normalization_find_insecure_ssh(tmp_path: Path) -> None:
    config = tmp_path / "sshd_config"
    config.write_text("PermitRootLogin yes\nPasswordAuthentication yes\n", encoding="utf-8")
    config.chmod(0o666)
    environment = EnvironmentInfo(
        ssh_config_path=str(config), package_manager=None, is_root=True
    )

    findings = normalize_findings(run_fallback_checks(environment), environment)

    action_types = {finding.auto_remediation for finding in findings}
    assert ActionType.SSH_SET_OPTION in action_types
    assert ActionType.SET_FILE_MODE in action_types


def test_missing_ssh_is_informational() -> None:
    environment = EnvironmentInfo()

    findings = normalize_findings(run_fallback_checks(environment), environment)

    ssh_finding = next(item for item in findings if item.finding_id == "ssh_config")
    assert ssh_finding.applicability == Applicability.NOT_APPLICABLE


def test_match_block_options_are_not_treated_as_global(tmp_path: Path) -> None:
    config = tmp_path / "sshd_config"
    config.write_text("Match User demo\n    PermitRootLogin yes\n", encoding="utf-8")
    environment = EnvironmentInfo(ssh_config_path=str(config))

    findings = normalize_findings(run_fallback_checks(environment), environment)

    assert not any(item.finding_id == "ssh_permit_root_login" for item in findings)