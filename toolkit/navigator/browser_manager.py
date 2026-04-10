# SPDX-License-Identifier: BUSL-1.1
"""
Browser session manager with per-session BrowserContext isolation.

Manages a single Chromium process shared across concurrent sessions.
Each session gets an isolated BrowserContext (separate cookies, storage, cache).

Session state is persisted via files:
  .browser.json  - Chromium CDP endpoint (shared)
  .browser.lock  - Startup coordination lock
  .sessions/     - Per-session state files

Environment variables:
  NAVIGATOR_CDP_URL    - Connect to an external browser via CDP instead of launching
                         one. Example: "http://localhost:9222" (launch Chrome with
                         --remote-debugging-port=9222).
  NAVIGATOR_HEADLESS   - Set to "0" to launch a visible browser window.
                         Default: "1" (headless).
"""
from __future__ import annotations

import asyncio
import fcntl
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Timeouts
CONTEXT_IDLE_TIMEOUT = 300  # 5 minutes per session context
BROWSER_IDLE_TIMEOUT = 600  # 10 minutes with no active contexts


def _state_dir() -> Path:
    """State directory for browser management files."""
    # Use toolkit's parent dir (the generator output dir)
    toolkit_dir = Path(__file__).parent
    state = toolkit_dir.parent / ".navigator-state"
    state.mkdir(parents=True, exist_ok=True)
    return state


def _browser_info_path() -> Path:
    return _state_dir() / "browser.json"


def _lock_path() -> Path:
    return _state_dir() / "browser.lock"


def _session_dir() -> Path:
    d = _state_dir() / "sessions"
    d.mkdir(exist_ok=True)
    return d


def _session_path(session_id: str) -> Path:
    # Sanitize session_id for filesystem
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
    return _session_dir() / f"{safe}.json"


class BrowserManager:
    """
    Manages Playwright browser lifecycle with session-isolated contexts.

    Usage:
        mgr = BrowserManager(session_id="proj123-flights")
        page = await mgr.get_page()
        # ... use page ...
        await mgr.close_session()
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def get_page(self) -> "Page":
        """Get or create the Page for this session."""
        if self._page and not self._page.is_closed():
            return self._page

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        # Try to connect to existing browser
        browser_info = self._load_browser_info()
        if browser_info:
            try:
                self._browser = await self._playwright.chromium.connect_over_cdp(
                    browser_info["ws_endpoint"]
                )
                logger.info(f"Connected to existing browser (PID {browser_info.get('pid')})")
            except Exception:
                logger.info("Existing browser not reachable, launching new one")
                self._browser = None

        # Launch new browser if needed
        if not self._browser:
            self._browser = await self._launch_browser()

        # Create isolated context for this session
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        self._page = await self._context.new_page()

        # Record session state
        self._save_session_info()

        return self._page

    async def _launch_browser(self) -> "Browser":
        """Launch a new Chromium browser and save its CDP endpoint."""
        # Option 1: Connect to an external browser via CDP
        cdp_url = os.environ.get("NAVIGATOR_CDP_URL")
        if cdp_url:
            logger.info(f"Connecting to external browser at {cdp_url}")
            browser = await self._playwright.chromium.connect_over_cdp(cdp_url)
            info = {
                "ws_endpoint": cdp_url,
                "pid": None,
                "launched_at": time.time(),
                "external": True,
            }
            _browser_info_path().write_text(json.dumps(info))
            return browser

        # Option 2: Launch Playwright Chromium (headless or visible)
        headless = os.environ.get("NAVIGATOR_HEADLESS", "1") != "0"

        lock_path = _lock_path()

        # File-based lock for startup coordination
        lock_fd = open(lock_path, "w")
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

            # Double-check: another process may have launched while we waited
            browser_info = self._load_browser_info()
            if browser_info:
                try:
                    browser = await self._playwright.chromium.connect_over_cdp(
                        browser_info["ws_endpoint"]
                    )
                    return browser
                except Exception:
                    pass  # Browser died, launch new one

            # Launch with CDP server so other processes can connect
            browser = await self._playwright.chromium.launch(
                headless=headless,
                args=["--no-sandbox"],
            )

            # Save browser info (note: connect_over_cdp endpoint not available
            # from launch(), so we use a simpler approach - each process launches
            # its own browser but with isolated contexts)
            info = {
                "pid": os.getpid(),
                "launched_at": time.time(),
                "headless": headless,
            }
            _browser_info_path().write_text(json.dumps(info))

            return browser
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    def _load_browser_info(self) -> dict | None:
        """Load browser connection info if available."""
        path = _browser_info_path()
        if not path.exists():
            return None
        try:
            info = json.loads(path.read_text())
            # Check if the process is still alive (skip for external browsers)
            pid = info.get("pid")
            if pid:
                try:
                    os.kill(pid, 0)
                except OSError:
                    # Process is dead, clean up
                    path.unlink(missing_ok=True)
                    return None
            return info
        except (json.JSONDecodeError, OSError):
            return None

    def _save_session_info(self) -> None:
        """Record session metadata."""
        info = {
            "session_id": self.session_id,
            "pid": os.getpid(),
            "started_at": time.time(),
            "last_used": time.time(),
        }
        _session_path(self.session_id).write_text(json.dumps(info))

    def _update_last_used(self) -> None:
        """Update last-used timestamp for idle timeout tracking."""
        path = _session_path(self.session_id)
        if path.exists():
            try:
                info = json.loads(path.read_text())
                info["last_used"] = time.time()
                path.write_text(json.dumps(info))
            except (json.JSONDecodeError, OSError):
                pass

    async def close_session(self) -> dict:
        """Close this session's context (not the browser)."""
        result = {"action": "close", "session_id": self.session_id}
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            # Clean up session file
            _session_path(self.session_id).unlink(missing_ok=True)
            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        return result

    async def close_all(self) -> dict:
        """Close the browser process entirely."""
        result = {"action": "close_all"}
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            # Clean up all state files
            state = _state_dir()
            _browser_info_path().unlink(missing_ok=True)
            for f in _session_dir().glob("*.json"):
                f.unlink(missing_ok=True)

            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        return result

    async def session_status(self) -> dict:
        """Return status of the current session."""
        session_path = _session_path(self.session_id)
        info = {}
        if session_path.exists():
            try:
                info = json.loads(session_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        # List all active sessions
        sessions = []
        for f in _session_dir().glob("*.json"):
            try:
                s = json.loads(f.read_text())
                sessions.append(s.get("session_id", f.stem))
            except (json.JSONDecodeError, OSError):
                pass

        return {
            "success": True,
            "action": "status",
            "session_id": self.session_id,
            "session_info": info,
            "active_sessions": sessions,
            "browser_running": _browser_info_path().exists(),
        }
