# GitHub Copilot Instructions for This Repository

## Project Intent

This repository implements a **small agentic Linux security audit proof-of-concept** for a course project.

The goal is **not** to build:
- a purely deterministic one-shot reporting script, or
- a fully autonomous unrestricted shell agent.

The goal is to build a **partially agentic** system that demonstrates this loop:

1. discover the environment
2. run security checks
3. interpret findings
4. build a remediation plan
5. ask the user for approval
6. apply safe allowlisted fixes
7. re-run checks
8. generate a final report

This repo should clearly demonstrate:
- context awareness
- tool use
- planning
- human-in-the-loop approval
- bounded action execution
- verification after action

## Source of Truth

When making changes, use these files as the primary specification:
- `docs/development_spec.md`
- `security_audit.md`
- `README.md`

If implementation and docs diverge, align the implementation to those files unless there is a strong reason to update the docs.

## Architectural Intent

Use:
- shell scripts for deterministic environment/tool interactions
- Python for orchestration, parsing, planning, approval flow, remediation logic, and reporting

The Python layer should not simply print a static report after running checks.

It should support a semi-agentic control flow:
- inspect context
- decide which checks are applicable
- decide whether to prompt for Lynis installation
- summarize findings
- offer remediation choices
- respond to user decisions
- apply only approved safe actions
- verify and report

## Required Runtime Behavior

The main workflow must support:
- discovery
- scan
- interpretation
- planning
- approval prompts
- safe remediation
- verification
- report generation

A report-only mode is allowed, but it must not be the only meaningful behavior.

## Safety Constraints

Do not implement unrestricted autonomous remediation.

Only allow explicit allowlisted actions, such as:
- set SSH daemon options:
  - `PermitRootLogin no`
  - `PasswordAuthentication no`
- install/configure unattended upgrades if applicable
- fix permissions on narrow approved paths
- optionally install Lynis with explicit user approval

Do not automatically modify:
- PAM
- firewall rules
- kernel sysctls
- user accounts/passwords
- broad filesystem permissions

## CLI / Interaction Guidance

The CLI should make the agentic loop visible.

Preferred interaction:
1. show environment summary
2. show findings summary
3. present remediation options
4. ask user whether to:
   - apply all low-risk fixes
   - review fixes one-by-one
   - generate report only
5. apply selected fixes
6. re-run checks
7. summarize before/after outcome

The code should make this flow easy to demo in 3–4 minutes.

## Copilot Implementation Guidance

When contributing code:
- preserve modular structure
- keep functions small and testable
- prefer deterministic helpers over ad hoc shell
- update `notes/TODO.md` with plan/progress
- add or update tests for core logic
- avoid overengineering or unnecessary frameworks

## When Revising Existing Code

If the current implementation is too deterministic, revise it so that:
- the orchestration layer includes explicit decision points
- approval flow is central to the runtime UX
- remediation planning is shown as a distinct step
- verification happens after actions
- final reporting includes before/after and user choices

Focus on making the system visibly **agentic-but-bounded**.