"""Normalize bounded check output into explainable findings."""

from __future__ import annotations

from .models import ActionType, Applicability, EnvironmentInfo, Finding, RawCheck, Severity


def normalize_findings(checks: list[RawCheck], environment: EnvironmentInfo) -> list[Finding]:
    findings: list[Finding] = []
    for check in checks:
        applicability = Applicability.APPLICABLE

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
                check.evidence, applicability, "Install unattended-upgrades in this Debian/Ubuntu environment.",
                ActionType.INSTALL_UNATTENDED_UPGRADES,
            ))
        elif check.check_id.startswith("world_writable_") and check.status == "world_writable":
            findings.append(Finding(
                check.check_id, "Demo file is world writable", Severity.MEDIUM,
                check.evidence, applicability, "Remove group and world write permissions from this explicit demo file.",
                ActionType.SET_FILE_MODE, check.metadata,
            ))
        elif check.check_id == "aide" and check.status == "missing":
            findings.append(Finding(
                check.check_id, "AIDE file integrity monitoring is unavailable", Severity.LOW,
                check.evidence, Applicability.LIMITED if environment.is_container else applicability,
                "Review whether AIDE should be installed and initialized for this workload.",
            ))
        elif check.check_id.startswith("login_banner_") and check.status in {"empty", "missing"}:
            findings.append(Finding(
                check.check_id, "Login banner is not configured", Severity.LOW,
                check.evidence, Applicability.LIMITED if environment.is_container else applicability,
                "Define an approved legal or security notice for this login banner.",
                metadata=check.metadata,
            ))
        elif check.check_id == "weak_demo_umask" and check.status == "weak":
            findings.append(Finding(
                check.check_id, "Demo profile sets a weak umask", Severity.MEDIUM,
                check.evidence, applicability, "Review the demo-owned profile and set an appropriate restrictive umask.",
                metadata=check.metadata,
            ))
        elif check.check_id == "listener_port_8080" and check.status == "listening":
            findings.append(Finding(
                check.check_id, "TCP port 8080 is listening", Severity.MEDIUM,
                check.evidence, Applicability.LIMITED if environment.is_container else applicability,
                "Confirm the service is expected and restrict exposure outside this tool.",
                metadata=check.metadata,
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