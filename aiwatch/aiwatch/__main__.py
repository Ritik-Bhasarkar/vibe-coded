"""CLI entry point.

Usage
-----
    aiwatch run <command> [args...]
    aiwatch test

Examples
--------
    aiwatch run aider .
    aiwatch run claude .
    aiwatch run interpreter
    aiwatch test              # verify bell + window focus
    aiwatch run --debug claude .
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aiwatch",
        description="Notify you (bell + window focus) when your AI CLI needs approval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version="aiwatch 0.1.0")

    subparsers = parser.add_subparsers(dest="command", metavar="<subcommand>")

    run_p = subparsers.add_parser(
        "run",
        help="Run a command and watch for approval prompts",
    )
    run_p.add_argument(
        "--debug",
        action="store_true",
        help="Print debug diagnostics to stderr",
    )
    run_p.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Command and arguments to run",
    )

    subparsers.add_parser(
        "test",
        help="Test bell sound and window focus",
    )

    args = parser.parse_args()

    if args.command == "run":
        if not args.cmd:
            run_p.print_help()
            sys.exit(1)
        from .watcher import run_watcher
        sys.exit(run_watcher(args.cmd, debug=args.debug))
    elif args.command == "test":
        from .watcher import run_test
        run_test()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
