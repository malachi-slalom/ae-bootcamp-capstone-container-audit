import json
import subprocess
import sys
from pathlib import Path

from src.approval import ApprovalMode
from src.models import EnvironmentInfo
from src.orchestration import run_audit


def test_report_only_workflow_writes_before_after_artifacts(tmp_path: Path) -> None:
    environment = EnvironmentInfo(
        os_id="test",
        os_version="1",
        user="tester",
        is_root=False,
        is_container=True,
        container_type="test-container",
    )

    run = run_audit(tmp_path, interactive=False, environment=environment)

    report = Path(run.report_path)
    assert report.is_file()
    assert "No system changes were attempted" in report.read_text(encoding="utf-8")
    artifact = next(tmp_path.glob("*.json"))
    data = json.loads(artifact.read_text(encoding="utf-8"))
    assert data["approval_mode"] == "report"
    assert data["before"] == data["after"]
    assert data["before_checks"] == data["after_checks"]
    assert data["approved_action_ids"] == []
    assert data["planning_decisions"]


def test_workflow_reports_agent_stages_in_order(tmp_path: Path) -> None:
    environment = EnvironmentInfo(
        os_id="test",
        os_version="1",
        user="tester",
        is_root=False,
        is_container=True,
        container_type="test-container",
    )
    events: list[tuple[str, str]] = []

    run_audit(tmp_path, interactive=False, environment=environment, reporter=lambda *event: events.append(event))

    stages = [stage for stage, _ in events]
    assert stages == [
        "observe",
        "observe",
        "check",
        "interpret",
        "plan",
        "approve",
        "act",
        "verify",
        "report",
    ]
    assert "fallback checks always ran" in events[2][1]
    assert "report-only" in events[4][1]


def test_approved_action_is_rechecked_and_reported(tmp_path: Path) -> None:
    config = tmp_path / "sshd_config"
    config.write_text("PermitRootLogin yes\nPasswordAuthentication no\n", encoding="utf-8")
    config.chmod(0o600)
    environment = EnvironmentInfo(
        os_id="test",
        os_version="1",
        user="root",
        is_root=True,
        ssh_config_path=str(config),
    )

    run = run_audit(
        tmp_path / "output",
        requested_mode=ApprovalMode.APPLY,
        interactive=False,
        environment=environment,
    )

    assert run.approved_action_ids == ["action-1"]
    assert run.results[0].success is True
    assert run.verification_results[0].status == "resolved"
    assert run.resolved_finding_ids == ["ssh_permit_root_login"]
    assert "PermitRootLogin no" in config.read_text(encoding="utf-8")
    data = json.loads(next((tmp_path / "output").glob("*.json")).read_text(encoding="utf-8"))
    assert data["verification_results"][0]["finding_id"] == "ssh_permit_root_login"


def test_cli_runs_non_interactively(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            "--non-interactive",
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    for stage in ("observe", "check", "interpret", "plan", "approve", "act", "verify", "report"):
        assert f"[{stage}]" in result.stdout
    assert list(tmp_path.glob("*.md"))