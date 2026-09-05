---
name: container-audit
description: "Use when: interactively auditing this Linux container, planning bounded security remediations, applying approved safe actions, verifying changes, and producing before/after reports."
---

# Copilot Agent Skill: Partially Agentic Security Audit Assistant

## Purpose

This skill guides an interactive, **partially agentic Linux security audit** in this repository.

It combines:
- deterministic scripts for inspection/checks
- Python orchestration for reasoning/planning
- human-in-the-loop approval for remediations
- safe, bounded actions only

It must not collapse into a static “run checks and print report” tool.

---

## What “Partially Agentic” Means in This Project

The project demonstrates the following loop:

### Observe
Gather context:
- OS
- distro
- privileges
- container status
- tool availability
- SSH config presence
- listening ports if available

### Reason
Interpret what findings mean in this environment:
- is the check applicable?
- is this a container-specific limitation?
- is there enough evidence?
- is remediation supported and safe?

### Plan
Construct a remediation plan from findings:
- low-risk auto-fixable with approval
- recommend-only/manual review
- not applicable

### Ask
Prompt the user before changes:
- apply all low-risk
- review one-by-one
- skip remediation

### Act
Apply only approved allowlisted remediations.

### Verify
Re-run checks and show before/after.

### Report
Produce a concise, useful summary and final Markdown report.

---

## Required User Experience

A good run should look like:

1. "I inspected the environment and found X"
2. "I ran checks and identified Y findings"
3. "Here is what I can safely fix"
4. "How would you like to proceed?"
5. user chooses approval mode
6. approved changes are applied
7. checks are re-run
8. before/after results are shown
9. final report is written

If the environment has few findings, still present:
- discovered context
- checks performed
- any limitations
- what would be remediable if needed

---

## Preferred Code Shape

Use:
- `scripts/` for deterministic shell interactions
- `src/discovery.py` for discovery orchestration
- `src/checks.py` for fallback checks
- `src/parser.py` for normalized findings
- `src/planner.py` for remediation planning
- `src/approval.py` for human-in-the-loop interaction
- `src/remediation.py` for bounded safe actions
- `src/orchestration.py` for end-to-end control flow
- `src/report.py` for report artifacts

The orchestration layer should explicitly model:
- findings
- remediation plan
- approvals
- actions taken
- verification results

---

## Runtime Interaction Requirements

Do not hide the planning/approval loop.

The user should be able to see:
- findings summary
- remediation summary
- risk labels
- approval choices
- action results
- verification summary

Minimum interaction modes:
- report only
- apply all low-risk
- review one-by-one

---

## Safety Boundaries

Allowed remediation categories:
- SSH config changes for:
  - `PermitRootLogin no`
  - `PasswordAuthentication no`
- unattended upgrades installation/config if applicable
- narrow file permission fixes
- optional Lynis install with approval

Not allowed:
- arbitrary command generation for fixes
- firewall rule changes
- PAM changes
- sysctl changes
- user/password changes
- broad chmod/chown operations

---

## Behavior in Limited Environments

If:
- Lynis is missing,
- root is unavailable,
- systemd is missing,
- sshd config is absent,
- network/package manager access is unavailable,

then:
- continue with degraded functionality,
- produce a useful report,
- explain limitations clearly,
- avoid pretending remediation succeeded.

---

## Workflow

When invoked:

1. Review `docs/development_spec.md`, `security_audit.md`, and `.github/copilot-instructions.md`.
2. Run `python -m src.main` in an interactive terminal when user input is available.
3. Present the discovered context, interpreted findings, and bounded remediation plan.
4. Require the user to approve all low-risk actions, review actions individually, or select report-only.
5. Never infer approval from invocation of the skill itself.
6. Apply changes only through the repository's typed, allowlisted remediation functions.
7. Re-run checks and report before/after results and artifact paths.
8. Update `notes/TODO.md` when implementation changes are made.
9. Run focused tests for code changes, followed by `python -m pytest -q` when feasible.

---

## Guidance for Revising Existing Code

If current code produces a report but lacks agentic interaction, revise it by:

1. making remediation planning a first-class step
2. adding an approval prompt before modifications
3. ensuring approved actions are executed through explicit action types
4. re-running checks after actions
5. including user choices and before/after state in the report

Do not add cosmetic text around a deterministic pipeline. The runtime flow must include actual decision points.

---

## Demo Priorities

Optimize for:
- a short, clear 3–4 minute demo
- visible human-in-the-loop behavior
- safe remediations
- understandable terminal output
- reliable behavior in a sandbox/container

Fallback checks are more important than deep Lynis integration for demo reliability.

---

## Development Practices

When working in this repo:
- consult `docs/development_spec.md`
- consult `security_audit.md`
- update `notes/TODO.md`
- implement incrementally
- add tests for core logic
- prefer simple and robust code over broad coverage