"""Normalize bounded check output into explainable findings."""

from __future__ import annotations

from .models import ActionType, Applicability, EnvironmentInfo, Finding, RawCheck, Severity


def normalize_findings(checks: list[RawCheck], environment: EnvironmentInfo) -> list[Finding]:
    findings: list[Finding] = []
    for check in checks:
        applicability = Applicability.LIMITED if environment.is_container else Applicability.APPLICABLE

        if check.check_id == "ssh_permit_root_login" and check.status == "yes":
            findings.append(Finding(
                check.check_id, "SSH permits direct root login", Severity.MEDIUM,
                check.evidence, applicability, "Set PermitRootLogin to no after confirming administrative access.",
                ActionType.SSH_SET_OPTION, check.metadata,
            ))
        elif check.check_id == "ssh_password_authentication" and check.status == "yes":
            findings.append(Finding(
                check.check_id, "SSH password authentication is enabled", Severity.MEDIUM,
                check.evidence, applicability, "Set PasswordAuthentication to no after confirming key-based access.",
                ActionType.SSH_SET_OPTION, check.metadata,
            ))
        elif check.check_id == "ssh_config_permissions" and check.status == "writable":
            findings.append(Finding(
                check.check_id, "SSH configuration is group/world writable", Severity.MEDIUM,
                check.evidence, applicability, "Remove group and world write permissions from the explicit config file.",
                ActionType.SET_FILE_MODE, check.metadata,
            ))
        elif check.check_id == "unattended_upgrades" and check.status == "missing":
            findings.append(Finding(
                check.check_id, "Automatic security updates are unavailable", Severity.LOW,
                check.evidence, applicability, "Install unattended-upgrades on supported Debian/Ubuntu hosts.",
                ActionType.INSTALL_UNATTENDED_UPGRADES,
            ))
        elif check.check_id == "lynis_availability" and check.status == "missing":
            findings.append(Finding(
                check.check_id, "Lynis is not installed", Severity.INFO,
                check.evidence, Applicability.APPLICABLE, "Optionally install Lynis; fallback checks remain available.",
                ActionType.INSTALL_LYNIS,
            ))
        elif check.check_id == "privilege" and check.status == "unprivileged":
            findings.append(Finding(
                check.check_id, "Audit has limited privileges", Severity.INFO,
                check.evidence, Applicability.LIMITED, "Run with appropriate privileges only when remediation is required.",
            ))
        elif check.check_id == "ssh_config" and check.status == "unavailable":
            findings.append(Finding(
                check.check_id, "SSH server configuration not found", Severity.INFO,
                check.evidence, Applicability.NOT_APPLICABLE, "No action is required if this environment does not run SSH.",
            ))
        elif check.check_id == "lynis_run" and check.status == "failed":
            findings.append(Finding(
                check.check_id, "Lynis scan did not complete", Severity.INFO,
                check.evidence, Applicability.LIMITED, "Review Lynis output; fallback checks completed independently.",
            ))
    return findings