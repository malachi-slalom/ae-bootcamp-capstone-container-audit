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


def test_planner_allows_typed_low_risk_action_in_container() -> None:
    actions = build_plan([_finding()], EnvironmentInfo(is_root=True, is_container=True))

    assert len(actions) == 1
    assert actions[0].action_type == ActionType.SSH_SET_OPTION


def test_planner_proposes_safe_container_action() -> None:
    environment = EnvironmentInfo(is_root=True, is_container=True)
    findings = [_finding()]

    decisions = explain_plan(findings, environment, build_plan(findings, environment))

    assert decisions[0].disposition == "proposed"
    assert decisions[0].action_id == "action-1"


def test_planner_keeps_untyped_container_finding_report_only() -> None:
    finding = Finding(
        "listener_port_8080",
        "TCP port 8080 is listening",
        Severity.MEDIUM,
        "0.0.0.0:8080",
        Applicability.LIMITED,
        "Review exposure manually.",
    )
    environment = EnvironmentInfo(is_root=True, is_container=True)

    decisions = explain_plan([finding], environment, build_plan([finding], environment))

    assert decisions[0].disposition == "report_only"
    assert "No allowlisted" in decisions[0].reason


def test_planner_classifies_container_findings_by_action_type() -> None:
    findings = [
        Finding(
            "world_writable_opt_demo_insecure",
            "Demo file is world writable",
            Severity.MEDIUM,
            "/opt/demo/insecure.txt mode is 0666",
            Applicability.APPLICABLE,
            "Remove group and world write permissions.",
            ActionType.SET_FILE_MODE,
            {"path": "/opt/demo/insecure.txt", "mode": 0o666},
        ),
        Finding(
            "unattended_upgrades",
            "Automatic security updates are unavailable",
            Severity.LOW,
            "unattended-upgrades package status: missing",
            Applicability.APPLICABLE,
            "Install unattended-upgrades.",
            ActionType.INSTALL_UNATTENDED_UPGRADES,
        ),
        Finding(
            "aide",
            "AIDE is unavailable",
            Severity.LOW,
            "aide package status: missing",
            Applicability.LIMITED,
            "Review AIDE installation manually.",
        ),
    ]
    environment = EnvironmentInfo(
        is_root=True, is_container=True, package_manager="apt-get"
    )

    actions = build_plan(findings, environment)
    decisions = explain_plan(findings, environment, actions)

    assert [action.action_type for action in actions] == [
        ActionType.SET_FILE_MODE,
        ActionType.INSTALL_UNATTENDED_UPGRADES,
    ]
    assert actions[0].parameters == {
        "path": "/opt/demo/insecure.txt",
        "mode": 0o644,
    }
    assert [decision.disposition for decision in decisions] == [
        "proposed",
        "proposed",
        "report_only",
    ]


def test_non_interactive_approval_defaults_to_report_only() -> None:
    actions = build_plan([_finding()], EnvironmentInfo(is_root=True))

    mode, approved = choose_actions(actions, interactive=False)

    assert mode == ApprovalMode.REPORT
    assert approved == []


def test_review_approves_individual_action() -> None:
    actions = build_plan([_finding()], EnvironmentInfo(is_root=True))
    prompts: list[str] = []

    mode, approved = choose_actions(
        actions,
        ApprovalMode.REVIEW,
        input_fn=lambda prompt: prompts.append(prompt) or "yes",
        interactive=True,
    )

    assert mode == ApprovalMode.REVIEW
    assert approved == actions
    assert "Evidence: PasswordAuthentication is yes" in prompts[0]
    assert "Risk: low; supported: yes" in prompts[0]


def test_review_mode_cannot_prompt_non_interactively() -> None:
    actions = build_plan([_finding()], EnvironmentInfo(is_root=True))

    mode, approved = choose_actions(actions, ApprovalMode.REVIEW, interactive=False)

    assert mode == ApprovalMode.REPORT
    assert approved == []