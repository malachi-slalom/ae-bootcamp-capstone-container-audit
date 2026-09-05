"""Observe, plan, approve, act, verify, and report."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .approval import ApprovalMode, choose_actions
from .checks import run_checks
from .discovery import discover_environment
from .models import AuditRun, EnvironmentInfo, Finding, RemediationAction, VerificationResult
from .parser import normalize_findings
from .planner import build_plan, explain_plan
from .remediation import execute_actions
from .report import write_artifacts

StageReporter = Callable[[str, str], None]


def _report(reporter: StageReporter | None, stage: str, message: str) -> None:
    if reporter is not None:
        reporter(stage, message)


def _finding_summary(findings: list[Finding]) -> str:
    if not findings:
        return "No reportable findings were identified."
    return "; ".join(
        f"{finding.finding_id} ({finding.severity.value}, {finding.applicability.value})"
        for finding in findings
    )


def _plan_summary(plan: list[RemediationAction], finding_count: int) -> str:
    if not plan:
        return (
            f"No safe actions are executable in this environment; "
            f"all {finding_count} finding(s) are report-only."
        )
    actions = "; ".join(
        f"{action.action_id}: {action.description} [{action.risk.value}]" for action in plan
    )
    excluded = finding_count - len({action.finding_id for action in plan})
    return f"{len(plan)} safe action(s) proposed; {excluded} finding(s) are report-only. {actions}"


def run_audit(
    output_dir: Path,
    requested_mode: ApprovalMode | None = None,
    interactive: bool | None = None,
    environment: EnvironmentInfo | None = None,
    reporter: StageReporter | None = None,
) -> AuditRun:
    _report(reporter, "observe", "Discovering the runtime environment.")
    discovered = environment or discover_environment()
    _report(
        reporter,
        "observe",
        f"Detected {discovered.os_id} {discovered.os_version}; "
        f"container={discovered.is_container}; root={discovered.is_root}; "
        f"lynis={discovered.lynis_available}.",
    )

    raw_checks = run_checks(discovered)
    _report(
        reporter,
        "observe",
        f"Completed {len(raw_checks)} check(s); fallback checks always ran.",
    )
    before = normalize_findings(raw_checks, discovered)
    _report(reporter, "reason", _finding_summary(before))

    plan = build_plan(before, discovered)
    planning_decisions = explain_plan(before, discovered, plan)
    _report(reporter, "plan", _plan_summary(plan, len(before)))
    approval_mode, approved = choose_actions(plan, requested_mode, interactive=interactive)
    _report(
        reporter,
        "ask",
        f"Mode={approval_mode.value}; approved {len(approved)} of {len(plan)} safe action(s).",
    )
    results = execute_actions(approved, discovered)
    changed = sum(result.changed for result in results)
    succeeded = sum(result.success for result in results)
    _report(reporter, "act", f"Executed {len(results)} action(s); {succeeded} succeeded, {changed} changed state.")

    verified_environment = discovered if environment is not None else discover_environment()
    verification_checks = run_checks(verified_environment)
    after = normalize_findings(verification_checks, verified_environment)
    before_ids = {finding.finding_id for finding in before}
    after_ids = {finding.finding_id for finding in after}
    resolved_finding_ids = sorted(before_ids - after_ids)
    new_finding_ids = sorted(after_ids - before_ids)
    actions_by_id = {action.action_id: action for action in approved}
    verification_results = []
    for result in results:
        action = actions_by_id[result.action_id]
        resolved = action.finding_id not in after_ids
        if not result.success:
            status = "action_failed"
            message = "The action failed; the finding could not be verified as resolved."
        elif resolved:
            status = "resolved"
            message = "The target finding was absent when checks were re-run."
        else:
            status = "still_present"
            message = "The action completed, but the target finding remains after re-checking."
        verification_results.append(
            VerificationResult(result.action_id, action.finding_id, status, message)
        )
    _report(
        reporter,
        "verify",
        f"Re-ran {len(verification_checks)} check(s); resolved {len(resolved_finding_ids)}, "
        f"new {len(new_finding_ids)}, remaining {len(before_ids & after_ids)}.",
    )
    run = AuditRun(
        environment=discovered,
        before_checks=raw_checks,
        before=before,
        plan=plan,
        planning_decisions=planning_decisions,
        approval_mode=approval_mode.value,
        approved_action_ids=[action.action_id for action in approved],
        not_approved_action_ids=[
            action.action_id for action in plan if action not in approved
        ],
        results=results,
        after_checks=verification_checks,
        after=after,
        verification_results=verification_results,
        resolved_finding_ids=resolved_finding_ids,
        new_finding_ids=new_finding_ids,
    )
    final_run = write_artifacts(run, output_dir)
    _report(reporter, "report", final_run.report_path)
    return final_run