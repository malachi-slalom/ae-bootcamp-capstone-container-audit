from pathlib import Path
from subprocess import CompletedProcess

import src.checks as checks_module
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


def test_dirty_demo_findings_are_detected_and_safely_classified(
    tmp_path: Path, monkeypatch
) -> None:
    insecure = tmp_path / "insecure.txt"
    public = tmp_path / "public.txt"
    issue = tmp_path / "issue"
    issue_net = tmp_path / "issue.net"
    profile = tmp_path / "weak_profile.sh"
    for path in (insecure, public):
        path.write_text("demo\n", encoding="utf-8")
        path.chmod(0o666)
    issue.write_text("", encoding="utf-8")
    issue_net.write_text("", encoding="utf-8")
    profile.write_text("umask 000\n", encoding="utf-8")
    monkeypatch.setattr(checks_module, "DEMO_FILE_PATHS", {
        "world_writable_opt_demo_insecure": insecure,
        "world_writable_srv_demo_public": public,
    })
    monkeypatch.setattr(checks_module, "LOGIN_BANNER_PATHS", {
        "login_banner_etc_issue": issue,
        "login_banner_etc_issue_net": issue_net,
    })
    monkeypatch.setattr(checks_module, "WEAK_PROFILE_PATH", profile)

    def fake_run(command, **kwargs):
        if command[0] == "dpkg-query":
            return CompletedProcess(command, 1, stdout="", stderr="missing")
        return CompletedProcess(
            command,
            0,
            stdout="State Recv-Q Send-Q Local Address:Port Peer Address:Port\nLISTEN 0 5 0.0.0.0:8080 0.0.0.0:*\n",
            stderr="",
        )

    monkeypatch.setattr(checks_module.subprocess, "run", fake_run)
    environment = EnvironmentInfo(
        package_manager="apt-get", network_tool="ss", is_root=True, is_container=True
    )

    findings = normalize_findings(run_fallback_checks(environment), environment)
    findings_by_id = {finding.finding_id: finding for finding in findings}

    expected = {
        "unattended_upgrades",
        "aide",
        "world_writable_opt_demo_insecure",
        "world_writable_srv_demo_public",
        "login_banner_etc_issue",
        "login_banner_etc_issue_net",
        "weak_demo_umask",
        "listener_port_8080",
    }
    assert expected <= findings_by_id.keys()
    assert findings_by_id["unattended_upgrades"].auto_remediation == ActionType.INSTALL_UNATTENDED_UPGRADES
    assert findings_by_id["world_writable_opt_demo_insecure"].auto_remediation == ActionType.SET_FILE_MODE
    assert findings_by_id["world_writable_srv_demo_public"].auto_remediation == ActionType.SET_FILE_MODE
    for finding_id in expected - {
        "unattended_upgrades",
        "world_writable_opt_demo_insecure",
        "world_writable_srv_demo_public",
    }:
        assert findings_by_id[finding_id].auto_remediation is None