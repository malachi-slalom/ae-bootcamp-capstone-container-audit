"""Human approval handling for planned remediations."""

from __future__ import annotations

import sys
from enum import Enum
from typing import Callable

from .models import RemediationAction


class ApprovalMode(str, Enum):
    REPORT = "report"
    APPLY = "apply"
    REVIEW = "review"


def choose_actions(
    actions: list[RemediationAction],
    requested_mode: ApprovalMode | None = None,
    input_fn: Callable[[str], str] = input,
    interactive: bool | None = None,
) -> tuple[ApprovalMode, list[RemediationAction]]:
    if not actions:
        return ApprovalMode.REPORT, []

    is_interactive = sys.stdin.isatty() if interactive is None else interactive
    mode = requested_mode
    if mode is None and not is_interactive:
        mode = ApprovalMode.REPORT
    elif mode is None:
        answer = input_fn("Mode [r]eport only, [a]pply all low-risk, re[v]iew: ").strip().lower()
        mode = {"a": ApprovalMode.APPLY, "v": ApprovalMode.REVIEW}.get(answer, ApprovalMode.REPORT)

    if mode == ApprovalMode.APPLY:
        return mode, list(actions)
    if mode == ApprovalMode.REVIEW:
        if not is_interactive:
            return ApprovalMode.REPORT, []
        approved = []
        for action in actions:
            prompt = (
                f"\nFinding: {action.finding_title or action.finding_id}\n"
                f"Evidence: {action.evidence or 'See finding details above.'}\n"
                f"Recommended fix: {action.description}\n"
                f"Risk: {action.risk.value}; supported: yes\n"
                "Approve this action [y/N]? "
            )
            answer = input_fn(prompt).strip().lower()
            if answer in {"y", "yes"}:
                approved.append(action)
        return mode, approved
    return ApprovalMode.REPORT, []