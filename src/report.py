"""Artifact and Markdown report generation."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .models import AuditRun, Finding, to_dict


def _finding_lines(findings: list[Finding]) -> list[str]:
    if not findings:
        return ["No reportable findings."]
    lines: list[str] = []
    for finding in findings:
        lines.extend(
            [
                f"### {finding.title}",
                f"- Severity: **{finding.severity.value}**",
                f"- Applicability: `{finding.applicability.value}`",
                f"- Evidence: {finding.evidence}",
                f"- Recommendation: {finding.recommendation}",
                "",
            ]
        )
    return lines


def write_artifacts(run: AuditRun, output_dir: Path) -> AuditRun:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    json_path = output_dir / f"audit-{timestamp}.json"
    report_path = output_dir / f"audit-{timestamp}.md"

    final_run = replace(run, report_path=str(report_path))
    json_path.write_text(json.dumps(to_dict(final_run), indent=2) + "\n", encoding="utf-8")

    environment = run.environment
    lines = [
        "# Linux Security Audit Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Environment",
        "",
        f"- OS: `{environment.os_id} {environment.os_version}`",
        f"- Kernel: `{environment.kernel}`",
        f"- User: `{environment.user}`",
        f"- Root: `{str(environment.is_root).lower()}`",
        f"- Container: `{environment.container_type}`",
        f"- Lynis available: `{str(environment.lynis_available).lower()}`",
        "",
        "## Initial Findings",
        "",
        *_finding_lines(run.before),
        "## Remediation Plan",
        "",
    ]
    for decision in run.planning_decisions:
        action = f" via `{decision.action_id}`" if decision.action_id else ""
        lines.append(
            f"- `{decision.finding_id}`: **{decision.disposition}**{action}. {decision.reason}"
        )
        if decision.action_id:
            planned_action = next(
                action for action in run.plan if action.action_id == decision.action_id
            )
            lines.append(
                f"  - Type: `{planned_action.action_type.value}`; "
                f"risk: `{planned_action.risk.value}`; fix: {planned_action.description}"
            )
    if not run.planning_decisions:
        lines.append("No remediation decisions were needed.")
    lines.extend(
        [
        "",
        "## Approval and Actions",
        "",
        f"Approval mode: `{run.approval_mode}`",
        f"Approved actions: {', '.join(run.approved_action_ids) or 'none'}",
        f"Not approved: {', '.join(run.not_approved_action_ids) or 'none'}",
        "",
        ]
    )
    if run.results:
        for result in run.results:
            status = "succeeded" if result.success else "failed"
            lines.append(f"- `{result.action_id}` {status}: {result.message}")
    else:
        lines.append("No system changes were attempted.")
    lines.extend(
        [
            "",
            "## Verification",
            "",
            f"- Resolved findings: {', '.join(run.resolved_finding_ids) or 'none'}",
            f"- New findings: {', '.join(run.new_finding_ids) or 'none'}",
            f"- Checks re-run: {len(run.after_checks)}",
            "",
        ]
    )
    for verification in run.verification_results:
        lines.append(
            f"- `{verification.action_id}` / `{verification.finding_id}`: "
            f"**{verification.status}**. {verification.message}"
        )
    lines.extend(
        ["", "## Final Findings", "", *_finding_lines(run.after), "## Limitations", ""]
    )
    limitations = list(environment.limitations)
    if environment.is_container:
        limitations.append("Container-local results do not represent host hardening.")
    if not environment.is_root:
        limitations.append("Limited privileges may reduce visibility and prevent remediation.")
    lines.extend(f"- {item}" for item in limitations)
    if not limitations:
        lines.append("- No discovery limitations were recorded.")
    lines.extend(["", f"Raw artifact: `{json_path.name}`", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return final_run