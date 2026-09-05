# Agentic Linux Security Audit PoC

A small proof-of-concept for demonstrating **agentic AI applied to Linux security auditing**.

## What it demonstrates

This project implements a simple agentic loop:

1. **Discover** the environment
2. **Scan** for security issues
3. **Interpret** findings
4. **Ask for approval**
5. **Apply safe fixes**
6. **Verify**
7. **Report**

The goal is to demonstrate agentic behavior in a short course demo, not to replace production security tooling.

---

## Why this is agentic

The system does more than run a script:

- adapts to the discovered environment
- decides which checks are applicable
- builds a remediation plan
- asks the user before changing the system
- executes only bounded, allowlisted actions
- re-checks and reports the outcome

This forms a clear:
**observe → plan → act → verify** loop.

---

## MVP Features

- Linux environment discovery
- Lynis integration if available
- fallback checks if Lynis is missing
- normalized findings
- human-in-the-loop remediation approval
- safe, allowlisted remediations only
- before/after report generation
- runtime skill file for the audit agent: `security_audit.md`

---

## Intended Environment

- Debian/Ubuntu-like Linux
- sandbox/container friendly
- may run with limited privileges

The project is designed to degrade gracefully when:
- Lynis is not installed
- root privileges are unavailable
- systemd/service control is unavailable

---

## Running

Primary entrypoint:

```bash
python -m src.main
```

When attached to a terminal, the CLI offers three modes:

- `report`: make no changes
- `apply`: apply every proposed low-risk action
- `review`: approve proposed actions one at a time

For a deterministic report-only run:

```bash
python -m src.main --non-interactive
```

To explicitly authorize all proposed low-risk actions without prompts:

```bash
python -m src.main --non-interactive --mode apply
```

The command streams each stage as it occurs, including interpreted findings and the safe plan before approval. Markdown reports and JSON evidence are written to `outputs/` by default. The artifacts retain raw checks, planning decisions, approvals, action results, and targeted before/after verification. Use `--output-dir PATH` to select another location.

## Checks and planning

Fallback checks always run and cover SSH configuration, SSH config permissions, unattended-upgrades availability, Lynis availability, and execution privilege. If Lynis is installed, its quick audit also runs; a Lynis failure does not prevent fallback checks or reporting.

Findings are normalized with severity, evidence, applicability, recommendation, and optional remediation type. Containers and unprivileged sessions still produce reports, but no remediation plan is executable in those environments.

## Safety boundaries

The executor accepts only fixed action types for:

- setting `PermitRootLogin no` or `PasswordAuthentication no` in the discovered SSH config
- removing group/world write bits from that exact SSH config path
- installing `lynis` or `unattended-upgrades` with `apt-get`

Approval is mandatory. Non-interactive runs default to report-only unless `--mode apply` is explicitly supplied. The project never executes model-generated commands and does not modify PAM, firewall rules, sysctls, users, passwords, or broad filesystem trees.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use temporary files and never modify real system configuration.