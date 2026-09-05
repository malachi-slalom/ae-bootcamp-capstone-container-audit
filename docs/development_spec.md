# Development Spec: Agentic Linux Security Audit PoC

## 1. Project Goal

Build a small proof-of-concept project for an Agentic Engineering course.

The project demonstrates an **agentic audit loop** inside a Linux sandbox/container:

1. discover the environment
2. run security checks
3. interpret findings
4. ask the user for approval before remediating
5. apply safe, allowlisted fixes
6. re-run checks
7. generate a final report

This project should prioritize:
- reliability
- explainability
- demo clarity
- safe behavior
- minimal dependencies

This is a short-demo project, not a production hardening platform.

---

## 2. MVP Definition

The MVP must support the following end-to-end behavior:

- user runs the tool
- environment discovery runs
- security checks run
- findings are normalized into a structured list
- a remediation plan is generated
- the user is asked what to do
- approved safe fixes are applied
- checks are re-run
- a before/after report is generated

The MVP must work even if:
- Lynis is not installed
- the environment is a container
- the process is not running as root

In these cases it should degrade gracefully and still produce a useful report.

Container status must not globally disable remediation. Safe local actions may be
offered when their action type and exact target are allowlisted, privileges are
sufficient, and the user explicitly approves them. Host-level, disruptive, or
unbounded changes remain recommendation-only.

---

## 3. Core Demo Story

A successful 3–4 minute demo should be able to show:

1. start audit
2. inspect detected environment
3. see findings
4. choose remediation mode:
   - apply all low-risk
   - review one-by-one
   - report only
5. apply one or two safe fixes
6. re-run verification
7. show final report

If the environment has very few real findings, the tool must still:
- surface discovery results,
- explain what checks were performed,
- provide a report,
- and demonstrate the approval flow.

---

## 4. Agentic Behavior Requirements

This project must clearly demonstrate agentic behavior, not just scripting.

The system should show:
- **context awareness**: adapts to distro/container/tool availability
- **planning**: forms a remediation plan from findings
- **tool use**: runs scripts and interprets outputs
- **human-in-the-loop behavior**: asks before changes
- **bounded autonomy**: executes only safe allowlisted actions
- **verification loop**: re-checks after acting

Do not implement unrestricted autonomous shell behavior.

---

## 5. Interface Requirements

## 5.1 Primary interface: CLI
The CLI is required.

Primary invocation should be:

```bash
python -m src.main
```