"""Shared data contracts for the audit workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Applicability(str, Enum):
    APPLICABLE = "applicable"
    LIMITED = "limited"
    NOT_APPLICABLE = "not_applicable"


class ActionType(str, Enum):
    SSH_SET_OPTION = "ssh_set_option"
    SET_FILE_MODE = "set_file_mode"
    INSTALL_UNATTENDED_UPGRADES = "install_unattended_upgrades"
    INSTALL_LYNIS = "install_lynis"


@dataclass(frozen=True)
class RawCheck:
    check_id: str
    status: str
    evidence: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvironmentInfo:
    os_id: str = "unknown"
    os_version: str = "unknown"
    kernel: str = "unknown"
    user: str = "unknown"
    is_root: bool = False
    is_container: bool = False
    container_type: str = "none"
    lynis_available: bool = False
    ssh_config_path: str | None = None
    package_manager: str | None = None
    network_tool: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    finding_id: str
    title: str
    severity: Severity
    evidence: str
    applicability: Applicability
    recommendation: str
    auto_remediation: ActionType | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RemediationAction:
    action_id: str
    finding_id: str
    action_type: ActionType
    description: str
    parameters: dict[str, Any]
    risk: Severity = Severity.LOW
    finding_title: str = ""
    evidence: str = ""


@dataclass(frozen=True)
class ActionResult:
    action_id: str
    success: bool
    changed: bool
    message: str


@dataclass(frozen=True)
class PlanningDecision:
    finding_id: str
    disposition: str
    reason: str
    action_id: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    action_id: str
    finding_id: str
    status: str
    message: str


@dataclass(frozen=True)
class AuditRun:
    environment: EnvironmentInfo
    before_checks: list[RawCheck]
    before: list[Finding]
    plan: list[RemediationAction]
    planning_decisions: list[PlanningDecision]
    approval_mode: str
    approved_action_ids: list[str]
    not_approved_action_ids: list[str]
    results: list[ActionResult]
    after_checks: list[RawCheck]
    after: list[Finding]
    verification_results: list[VerificationResult]
    resolved_finding_ids: list[str]
    new_finding_ids: list[str]
    report_path: str = ""


def to_dict(value: Any) -> Any:
    """Convert dataclasses and string enums into JSON-compatible values."""
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: to_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_dict(item) for item in value]
    return value