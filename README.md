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