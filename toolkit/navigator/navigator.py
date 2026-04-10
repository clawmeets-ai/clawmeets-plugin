# SPDX-License-Identifier: BUSL-1.1
#!/usr/bin/env python3
"""
Navigator toolkit CLI -- invoked by Claude at runtime to interact with websites.

All commands require --session <id> for browser context isolation.
Output is always JSON to stdout.

Usage:
    python navigator.py --session <id> goto <url>
    python navigator.py --session <id> fill <selector> <value>
    python navigator.py --session <id> click <selector>
    python navigator.py --session <id> select <selector> <value>
    python navigator.py --session <id> wait <selector> [--timeout <ms>]
    python navigator.py --session <id> extract <selector> [--format text|json|html]
    python navigator.py --session <id> type <selector> <text> [--delay <ms>]
    python navigator.py --session <id> press <key>
    python navigator.py --session <id> scroll [--direction up|down] [--amount <px>]
    python navigator.py --session <id> screenshot [--output <path>] [--full-page]
    python navigator.py --session <id> evaluate <js_expression>
    python navigator.py --session <id> status
    python navigator.py --session <id> close
    python navigator.py close --all
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

# Add toolkit parent to path so imports work when invoked standalone
_toolkit_dir = Path(__file__).parent
sys.path.insert(0, str(_toolkit_dir))


def _output(result: dict) -> None:
    """Print result as JSON to stdout."""
    print(json.dumps(result, indent=2, default=str))


async def _run(args: argparse.Namespace) -> dict:
    """Execute the requested action."""
    from browser_manager import BrowserManager
    import actions

    session_id = args.session

    # Handle close --all without a session
    if args.command == "close" and getattr(args, "all", False):
        mgr = BrowserManager(session_id=session_id or "_cleanup")
        return await mgr.close_all()

    if not session_id:
        return {
            "success": False,
            "error": "--session is required for all commands except 'close --all'",
        }

    mgr = BrowserManager(session_id=session_id)

    # Status doesn't need a page
    if args.command == "status":
        return await mgr.session_status()

    # Close this session
    if args.command == "close":
        return await mgr.close_session()

    # All other commands need a page
    page = await mgr.get_page()

    try:
        if args.command == "goto":
            result = await actions.action_goto(page, args.url, timeout=args.timeout)
        elif args.command == "fill":
            result = await actions.action_fill(
                page, args.selector, args.value, timeout=args.timeout
            )
        elif args.command == "click":
            result = await actions.action_click(page, args.selector, timeout=args.timeout)
        elif args.command == "select":
            result = await actions.action_select(
                page, args.selector, args.value, timeout=args.timeout
            )
        elif args.command == "wait":
            result = await actions.action_wait(page, args.selector, timeout=args.timeout)
        elif args.command == "extract":
            result = await actions.action_extract(
                page, args.selector, fmt=args.format, timeout=args.timeout
            )
        elif args.command == "type":
            result = await actions.action_type(
                page, args.selector, args.text, delay=args.delay, timeout=args.timeout
            )
        elif args.command == "press":
            result = await actions.action_press(page, args.key)
        elif args.command == "scroll":
            result = await actions.action_scroll(
                page, direction=args.direction, amount=args.amount
            )
        elif args.command == "screenshot":
            output_path = args.output or str(
                Path(tempfile.gettempdir()) / f"nav-{session_id}.png"
            )
            result = await actions.action_screenshot(
                page, output_path, full_page=args.full_page
            )
        elif args.command == "evaluate":
            result = await actions.action_evaluate(page, args.expression)
        else:
            result = {"success": False, "error": f"Unknown command: {args.command}"}
    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
            "command": args.command,
        }
    finally:
        # Don't close -- keep session alive for subsequent commands
        mgr._update_last_used()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Navigator toolkit for browser automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--session", "-s", type=str, default=None, help="Session ID for context isolation"
    )

    subparsers = parser.add_subparsers(dest="command", help="Action to perform")

    # goto
    p = subparsers.add_parser("goto", help="Navigate to a URL")
    p.add_argument("url", help="URL to navigate to")
    p.add_argument("--timeout", type=int, default=30000, help="Timeout in ms")

    # fill
    p = subparsers.add_parser("fill", help="Fill a text input")
    p.add_argument("selector", help="CSS selector for the input")
    p.add_argument("value", help="Value to fill")
    p.add_argument("--timeout", type=int, default=10000)

    # click
    p = subparsers.add_parser("click", help="Click an element")
    p.add_argument("selector", help="CSS selector to click")
    p.add_argument("--timeout", type=int, default=10000)

    # select
    p = subparsers.add_parser("select", help="Select dropdown option")
    p.add_argument("selector", help="CSS selector for <select>")
    p.add_argument("value", help="Option value to select")
    p.add_argument("--timeout", type=int, default=10000)

    # wait
    p = subparsers.add_parser("wait", help="Wait for element to appear")
    p.add_argument("selector", help="CSS selector to wait for")
    p.add_argument("--timeout", type=int, default=10000)

    # extract
    p = subparsers.add_parser("extract", help="Extract content from elements")
    p.add_argument("selector", help="CSS selector to extract from")
    p.add_argument(
        "--format", choices=["text", "json", "html"], default="text", help="Output format"
    )
    p.add_argument("--timeout", type=int, default=10000)

    # type (character by character)
    p = subparsers.add_parser("type", help="Type text character by character")
    p.add_argument("selector", help="CSS selector for the input")
    p.add_argument("text", help="Text to type")
    p.add_argument("--delay", type=int, default=50, help="Delay between keystrokes in ms")
    p.add_argument("--timeout", type=int, default=10000)

    # press
    p = subparsers.add_parser("press", help="Press a keyboard key")
    p.add_argument("key", help="Key to press (Enter, Tab, Escape, etc.)")

    # scroll
    p = subparsers.add_parser("scroll", help="Scroll the page")
    p.add_argument(
        "--direction", choices=["up", "down"], default="down", help="Scroll direction"
    )
    p.add_argument("--amount", type=int, default=500, help="Scroll amount in pixels")

    # screenshot
    p = subparsers.add_parser("screenshot", help="Take a screenshot")
    p.add_argument("--output", "-o", help="Output file path")
    p.add_argument("--full-page", action="store_true", help="Capture full page")

    # evaluate
    p = subparsers.add_parser("evaluate", help="Evaluate JavaScript")
    p.add_argument("expression", help="JavaScript expression to evaluate")

    # status
    subparsers.add_parser("status", help="Show session status")

    # close
    p = subparsers.add_parser("close", help="Close session or browser")
    p.add_argument("--all", action="store_true", help="Close the entire browser")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        result = asyncio.run(_run(args))
        _output(result)
        sys.exit(0 if result.get("success", False) else 1)
    except KeyboardInterrupt:
        _output({"success": False, "error": "Interrupted"})
        sys.exit(130)
    except Exception as e:
        _output({"success": False, "error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
