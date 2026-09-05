"""Create a bounded remediation plan from normalized findings."""

from __future__ import annotations

from .models import (
    ActionType,
    Applicability,
    EnvironmentInfo,
    Finding,
    PlanningDecision,
    RemediationAction,
    Severity,
)
from .policy import action_type_allowed, permission_path_allowed


def build_plan(findings: list[Finding], environment: EnvironmentInfo) -> list[RemediationAction]:
    if not environment.is_root:
        return []

    actions: list[RemediationAction] = []
    for finding in findings:
        if (
            not finding.auto_remediation
            or finding.applicability != Applicability.APPLICABLE
            or not action_type_allowed(finding.auto_remediation, environment)
        ):
            continue

        parameters: dict[str, object] = {}
        if finding.auto_remediation == ActionType.SSH_SET_OPTION:
            path = finding.metadata.get("path")
            option = finding.metadata.get("option")
            if not isinstance(path, str) or option not in {"PermitRootLogin", "PasswordAuthentication"}:
                continue
            parameters = {"path": path, "option": option, "value": "no"}
        elif finding.auto_remediation == ActionType.SET_FILE_MODE:
            path = finding.metadata.get("path")
            if not isinstance(path, str) or not permission_path_allowed(path, environment):
                continue
            current_mode = finding.metadata.get("mode")
            if not isinstance(current_mode, int):
                continue
            parameters = {"path": path, "mode": current_mode & ~0o022}
        elif finding.auto_remediation in {ActionType.INSTALL_LYNIS, ActionType.INSTALL_UNATTENDED_UPGRADES}:
            if environment.package_manager != "apt-get":
                continue
        else:
            continue

        actions.append(RemediationAction(
            action_id=f"action-{len(actions) + 1}",
            finding_id=finding.finding_id,
            action_type=finding.auto_remediation,
            description=finding.recommendation,
            parameters=parameters,
            risk=Severity.LOW,
            finding_title=finding.title,
            evidence=finding.evidence,
        ))
    return actions


def explain_plan(
    findings: list[Finding],
    environment: EnvironmentInfo,
    actions: list[RemediationAction],
) -> list[PlanningDecision]:
    actions_by_finding = {action.finding_id: action for action in actions}
    decisions: list[PlanningDecision] = []
    for finding in findings:
        action = actions_by_finding.get(finding.finding_id)
        if action is not None:
            decisions.append(PlanningDecision(
                finding.finding_id,
                "proposed",
                "Evidence is applicable and an allowlisted low-risk action is available.",
                action.action_id,
            ))
        elif finding.applicability == Applicability.NOT_APPLICABLE:
            decisions.append(PlanningDecision(
                finding.finding_id, "not_applicable", "The finding does not apply to this environment."
            ))
        elif (
            environment.is_container
            and finding.auto_remediation is not None
            and not action_type_allowed(finding.auto_remediation, environment)
        ):
            decisions.append(PlanningDecision(
                finding.finding_id,
                "report_only",
                "This action type is not approved for in-container remediation.",
            ))
        elif not environment.is_root and finding.auto_remediation:
            decisions.append(PlanningDecision(
                finding.finding_id,
                "report_only",
                "The allowlisted remediation requires root privileges.",
            ))
        elif finding.auto_remediation is None:
            decisions.append(PlanningDecision(
                finding.finding_id,
                "report_only",
                "No allowlisted automatic remediation is defined.",
            ))
        else:
            decisions.append(PlanningDecision(
                finding.finding_id,
                "report_only",
                "The environment or evidence does not satisfy the remediation preconditions.",
            ))
    return decisions