from src.approval import ApprovalMode, choose_actions
from src.models import ActionType, Applicability, EnvironmentInfo, Finding, Severity
from src.planner import build_plan, explain_plan


def _finding() -> Finding:
    return Finding(
        "ssh_password_authentication",
        "SSH password authentication is enabled",
        Severity.MEDIUM,
        "PasswordAuthentication is yes",
        Applicability.APPLICABLE,
        "Set PasswordAuthentication to no.",
        ActionType.SSH_SET_OPTION,
        {"path": "/tmp/sshd_config", "option": "PasswordAuthentication"},
    )


def test_planner_blocks_actions_in_container() -> None:
    assert build_plan([_finding()], EnvironmentInfo(is_root=True, is_container=True)) == []


def test_planner_explains_why_container_finding_is_report_only() -> None:
    environment = EnvironmentInfo(is_root=True, is_container=True)
    findings = [_finding()]

    decisions = explain_plan(findings, environment, build_plan(findings, environment))

    assert decisions[0].disposition == "report_only"
    assert decisions[0].reason == "Automatic remediation is disabled in containers."


def test_non_interactive_approval_defaults_to_report_only() -> None:
    actions = build_plan([_finding()], EnvironmentInfo(is_root=True))

    mode, approved = choose_actions(actions, interactive=False)

    assert mode == ApprovalMode.REPORT
    assert approved == []


def test_review_approves_individual_action() -> None:
    actions = build_plan([_finding()], EnvironmentInfo(is_root=True))

    mode, approved = choose_actions(
        actions, ApprovalMode.REVIEW, input_fn=lambda _: "yes", interactive=True
    )

    assert mode == ApprovalMode.REVIEW
    assert approved == actions


def test_review_mode_cannot_prompt_non_interactively() -> None:
    actions = build_plan([_finding()], EnvironmentInfo(is_root=True))

    mode, approved = choose_actions(actions, ApprovalMode.REVIEW, interactive=False)

    assert mode == ApprovalMode.REPORT
    assert approved == []