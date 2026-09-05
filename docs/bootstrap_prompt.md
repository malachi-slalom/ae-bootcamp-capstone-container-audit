You are implementing a small proof-of-concept project for an Agentic Engineering course.

Read and follow these files as the source of truth:
- docs/development_spec.md
- security_audit.md
- README.md

Your task is to build the MVP described there inside this repository.

High-level goal:
Build a CLI-first agentic Linux security audit PoC that:
1. discovers the environment,
2. runs security checks,
3. interprets findings,
4. asks the user for approval before remediation,
5. applies a small set of safe allowlisted fixes,
6. re-runs checks,
7. generates a final report.

Important priorities:
- Prioritize a working end-to-end MVP over breadth or polish.
- Keep dependencies minimal.
- Prefer Python standard library + shell scripts + pytest.
- Do not overengineer.
- Do not build a large web app.
- CLI is required; endpoint is optional and should only be added if the CLI MVP is complete.
- Fallback checks are mandatory and more important than Lynis integration for MVP reliability.
- All remediations must be explicitly allowlisted and safe.
- Do not implement unrestricted autonomous shell execution.

Development process requirements:
1. First, inspect the repo and existing files.
2. Then create/update `notes/TODO.md` with:
   - implementation plan,
   - ordered task list,
   - assumptions,
   - deferred items,
   - demo notes.
3. Implement incrementally in small, testable steps.
4. After each meaningful milestone, update `notes/TODO.md`.
5. Add tests alongside core logic.
6. Prefer a readable, modular structure matching the spec.
7. If you need scratch/design notes, create additional markdown files under `notes/`.

Required MVP behavior:
- `python -m src.main` should run the audit workflow.
- Discovery must work.
- Fallback checks must work even without Lynis.
- Findings must be normalized.
- User approval flow must exist.
- Safe remediations must be implemented for a small allowlist only.
- Verification/re-run must happen after approved changes.
- Output artifacts and a final markdown report must be produced.

Required files/modules to implement or refine:
- notes/TODO.md
- scripts/discover_env.sh
- scripts/run_lynis.sh
- scripts/verify.sh
- scripts/maybe_install_lynis.sh (optional but recommended)
- src/main.py
- src/models.py
- src/discovery.py
- src/checks.py
- src/parser.py
- src/planner.py
- src/approval.py
- src/remediation.py
- src/report.py
- src/orchestration.py
- tests/* for core logic

Guardrails:
- Never use arbitrary LLM-generated shell commands for remediation.
- Only support explicit allowlisted remediation action types.
- Do not auto-modify PAM, firewall rules, kernel sysctls, users/passwords, or broad filesystem permissions.
- Be conservative in containers and limited-permission environments.
- If a tool is missing, degrade gracefully and continue when possible.
- If root privileges are unavailable, still produce findings/report and explain limitations.

Suggested implementation order:
1. create/update repo structure
2. create/update notes/TODO.md
3. implement data models
4. implement discovery script + Python wrapper/parser
5. implement fallback checks
6. implement finding normalization
7. implement remediation planner
8. implement approval CLI flow
9. implement safe remediation functions
10. implement verification
11. implement report generation
12. wire main orchestration
13. add/refine tests
14. refine README and security_audit.md if needed to match implementation

Code quality expectations:
- Write clear, maintainable code.
- Keep functions small and focused.
- Use dataclasses unless a stronger modeling approach is clearly needed.
- Add docstrings where useful.
- Avoid unnecessary dependencies and frameworks.
- Ensure tests do not require root and do not edit real system files.

Execution behavior:
- Start by summarizing your implementation plan.
- Then begin making changes.
- Show concise progress updates.
- Prefer finishing a thin vertical slice before adding extras.

Definition of done:
- The CLI runs the complete flow.
- Core tests pass.
- The repo contains the required docs, scripts, source files, and artifacts structure.
- The implementation matches the intent of docs/development_spec.md and security_audit.md.

Begin now by:
1. reviewing the repository state,
2. producing a concise implementation plan,
3. creating/updating `notes/TODO.md`,
4. implementing the first vertical slice of the MVP.