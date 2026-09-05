"""Command-line entrypoint for the audit workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from .approval import ApprovalMode
from .orchestration import run_audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a bounded Linux security audit")
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in ApprovalMode],
        help="Approval mode; omitted prompts on a terminal and reports only otherwise",
    )
    parser.add_argument("--non-interactive", action="store_true", help="Disable prompts")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    requested_mode = ApprovalMode(args.mode) if args.mode else None
    interactive = False if args.non_interactive else None

    run_audit(
        args.output_dir,
        requested_mode,
        interactive,
        reporter=lambda stage, message: print(f"[{stage}] {message}"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())