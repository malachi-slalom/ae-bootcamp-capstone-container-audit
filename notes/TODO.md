# MVP Implementation Tracker

## Implementation Plan

Build a thin, standard-library-only vertical slice first: discover the environment, run fallback checks, normalize findings, create an allowlisted plan, default safely through approval, re-check, and write JSON/Markdown artifacts. Add isolated remediation tests before enabling any system mutation.

## Ordered Task List

- [x] Define environment, finding, action, and result dataclasses.
- [x] Implement machine-readable discovery script and Python wrapper.
- [x] Implement mandatory fallback checks and optional Lynis integration.
- [x] Normalize all check output into findings.
- [x] Generate plans containing only explicit low-risk action types.
- [x] Implement interactive approval and non-interactive report-only behavior.
- [x] Implement narrow, testable SSH and file-permission remediations.
- [x] Re-run checks after the approval stage and compare results.
- [x] Write raw JSON artifacts and a final Markdown report under `outputs/`.
- [x] Wire `python -m src.main` and add CLI options.
- [x] Add unit and end-to-end smoke tests that never require root.
- [x] Refine README usage and safety documentation.
- [x] Stream explicit observe, check, interpret, plan, approve, act, verify, and report stages from the runtime flow.
- [x] Preserve check coverage, approval decisions, and targeted before/after verification in artifacts.
- [x] Add tests for visible planning before approval and approved-action verification.
- [x] Package the interactive audit workflow as the invokable `container-audit` Copilot skill.

## Assumptions

- Python 3.11+ and a POSIX shell are available.
- `outputs/` is the repository's artifact directory; the singular `output/` mention in `security_audit.md` is treated as a typo.
- SSH remediation is offered only for an existing, explicit config path and is skipped in containers by default.
- Non-interactive execution never modifies the system unless an explicit approval option is supplied.
- Tests use temporary files and injected environment data; they never modify `/etc`.

## Deferred Items

- HTTP/API interface.
- Automatic PAM, firewall, sysctl, account, or password changes.
- Broad permission scanning or recursive permission changes.
- Production-grade distro support beyond Debian/Ubuntu-like systems.
- LLM-generated commands or open-ended plugin execution.

## Demo Notes

Run `python -m src.main`, inspect discovery and findings, choose report-only or approve one low-risk action, then open the printed report path. Run `python -m src.main --non-interactive` for a deterministic no-change demo.

## Milestones

- [x] Milestone 1: first complete report-only vertical slice.
- [x] Milestone 2: bounded approval and remediation with tests.
- [x] Milestone 3: documentation and final verification.

The complete staged CLI loop and bounded remediation tests pass in a container. Final validation: 18 tests passed, shell syntax passed, static diagnostics were clean, and a live non-interactive run generated Markdown and JSON artifacts.
