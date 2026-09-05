---
name: container-audit
description: "Use when: interactively auditing this Linux container, interpreting scanner and fallback findings, presenting a bounded remediation plan, asking the user for approval, applying approved safe actions, verifying changes, and producing before/after reports."
---

# Copilot Agent Skill: Interactive Container Security Audit

## Purpose

This skill runs an **interactive, partially agentic Linux container security audit** for this repository.

It is intended for a short demo and must visibly demonstrate the loop:

1. observe
2. reason
3. plan
4. ask
5. act
6. verify
7. report

This skill must **not** collapse into:
- a static one-shot report generator, or
- an unrestricted autonomous shell agent.

It should combine:
- deterministic scripts for environment inspection and checks
- Python orchestration for interpretation and planning
- human-in-the-loop approval before changes
- bounded, allowlisted remediation actions only

---

## Source of Truth

Use these files as the primary implementation and behavior references:

- `docs/development_spec.md`
- `security_audit.md`
- `.github/copilot-instructions.md`
- `README.md`

If implementation diverges from these docs, prefer aligning the code to the docs unless the docs clearly need revision.

---

## What “Partially Agentic” Means Here

The runtime behavior should visibly include:

### Observe
Inspect:
- OS and distro
- privilege level
- container status
- Lynis availability
- package manager availability
- SSH config presence
- listening services/ports
- demo-specific files and configs where relevant

### Reason
Interpret findings in context:
- Is the finding real and evidenced?
- Is it applicable in a container?
- Is it safe to remediate in-container?
- Is it recommend-only?
- Does remediation require approval?

### Plan
Create a remediation plan that clearly separates:
- safe, approval-required remediations
- recommend-only findings
- not-applicable findings

### Ask
Before any change, present options:
- report only
- apply all low-risk
- review actions one-by-one

### Act
Apply only approved, allowlisted, low-risk actions.

### Verify
Re-run checks and compare before/after state.

### Report
Produce a concise summary plus final Markdown artifacts.

---

## Required Runtime UX

A successful run should visibly show:

1. discovered environment summary
2. checks performed
3. findings summary
4. remediation plan
5. approval choices
6. actions taken
7. verification / re-check results
8. final report path

Do not skip directly from “scan complete” to “final report” if remediable findings exist.

The runtime should feel interactive and agentic, even if the underlying tools are deterministic.

---

## Demo Container Expectations

The current demo environment is an intentionally “dirty” Debian container.

This skill should expect and look for findings such as:

### Safe-remediable in-container findings
- SSH `PermitRootLogin yes`
- SSH `PasswordAuthentication yes`
- world-writable file `/opt/demo/insecure.txt`
- world-writable file `/srv/demo/public.txt`
- missing `unattended-upgrades`

### Recommend-only findings
- missing `aide`
- empty or missing login banner files (`/etc/issue`, `/etc/issue.net`)
- weak umask in `/opt/demo/weak_profile.sh`
- listener on port `8080`
- generic Lynis findings that are host-oriented or not clearly safe to fix

If some of these are not currently detected by the implementation, prefer updating the checks and planner rather than ignoring them.

---

## Allowed In-Container Remediations

For this demo, the following are allowed **inside the container** with explicit user approval:

### SSH config hardening
- set `PermitRootLogin no`
- set `PasswordAuthentication no`

Verification may be file-based if service restart/reload is unavailable.

### Narrow file-permission fixes
Only for explicit, approved files such as:
- `/opt/demo/insecure.txt`
- `/srv/demo/public.txt`

No broad recursive chmod operations.

### Unattended upgrades
Install/configure `unattended-upgrades` if:
- package manager is available
- privileges are sufficient
- user explicitly approves

### Optional Lynis installation
Only if missing and explicitly approved.

---

## Report-Only / Recommend-Only Categories

The following should generally remain recommend-only unless explicitly implemented safely:

- AIDE installation
- login banner configuration
- weak umask remediation outside a narrowly defined demo-owned path
- service/network exposure analysis that does not have a safe bounded remediation
- host/kernel hardening recommendations from Lynis
- firewall/PAM/sysctl/user-account changes

Do not auto-remediate these.

---

## Safety Boundaries

Allowed remediation categories:
- SSH config changes for approved keys
- unattended-upgrades installation/configuration if applicable
- narrow file permission fixes
- optional Lynis installation with approval

Not allowed:
- arbitrary shell-generated remediations
- firewall rule changes
- PAM changes
- kernel sysctl changes
- user/password changes
- broad chmod/chown operations
- destructive cleanup outside explicit demo paths

When uncertain, recommend rather than apply.

---

## Behavior in Container Context

Do **not** treat all container findings as report-only by default.

Instead:
- allow safe, local, file-based remediations inside the container
- treat host-level or disruptive changes as recommend-only
- clearly mark limited applicability where appropriate

Good rule of thumb:
- if the action is bounded, local, reversible, and low-risk, it may be offered with approval
- otherwise it should remain report-only

---

## Workflow

When invoked:

1. Review:
   - `docs/development_spec.md`
   - `security_audit.md`
   - `.github/copilot-instructions.md`

2. Inspect the current implementation before acting.
   - If findings or planner behavior are too sparse/coarse for the demo container, revise code first.

3. Run the audit flow interactively, preferably via:
   - `python -m src.main`

4. Ensure the runtime presents:
   - environment summary
   - findings summary
   - remediation plan
   - approval options

5. Require explicit user approval before any system modification.
   - Never infer approval from invocation of this skill.

6. Apply changes only through typed, allowlisted remediation functions in the repository.

7. Re-run checks and present:
   - resolved findings
   - remaining findings
   - failed/skipped actions
   - artifact/report paths

8. If code changes are required:
   - update `notes/TODO.md`
   - run focused tests first
   - then run `python -m pytest -q` when feasible

---

## Runtime Interaction Requirements

Minimum supported approval modes:
- `report only`
- `apply all low-risk`
- `review one-by-one`

For one-by-one review, present:
- finding title
- evidence
- recommended fix
- risk level
- whether remediation is supported

Do not hide the remediation plan or approval decision points.

---

## Guidance for Revising Existing Code

If current behavior is too deterministic or too sparse, revise the implementation so that:

1. fallback checks detect the intended dirty-demo findings
2. remediation planning is a distinct visible step
3. safe in-container remediations are not incorrectly downgraded to report-only
4. approval prompts occur before any changes
5. verification happens after remediation
6. final report includes before/after state and user choices

Do not solve this with cosmetic narration alone.
The code path must include real decision points.

---

## Demo Priorities

Optimize for:
- a clear 3–4 minute demo
- visible human-in-the-loop behavior
- several meaningful findings
- a few safe remediations
- understandable before/after reporting
- reliable operation in a Debian container

Fallback checks are required and more important than deep Lynis dependence for demo reliability.

---

## Development Practices

When modifying code in this repo:
- consult `docs/development_spec.md`
- consult `security_audit.md`
- update `notes/TODO.md`
- implement incrementally
- keep dependencies minimal
- add or update tests for parser, planner, remediation, and reporting behavior
- prefer robust deterministic checks over broad but fragile scanner logic

---

## Success Criteria

A successful invocation of this skill should result in one of two outcomes:

### If the implementation is already sufficient
- the audit runs interactively
- the user is shown findings and remediation choices
- approved safe actions are applied
- checks are re-run
- a before/after report is produced

### If the implementation is not yet sufficient
- the agent first revises the implementation so the above behavior is possible
- then runs the audit flow again

---