# SPDX-License-Identifier: BUSL-1.1
"""
Atomic browser actions for the navigator toolkit.

Each action operates on a Playwright Page and returns a structured dict
suitable for JSON serialization to stdout.
"""
from __future__ import annotations

import json


async def action_goto(page, url: str, timeout: int = 30000) -> dict:
    """Navigate to a URL."""
    try:
        await page.goto(url, timeout=timeout, wait_until="networkidle")
        title = await page.title()
        return {
            "success": True,
            "action": "goto",
            "url": page.url,
            "title": title,
        }
    except Exception as e:
        return {"success": False, "action": "goto", "url": url, "error": str(e)}


async def action_fill(page, selector: str, value: str, timeout: int = 10000) -> dict:
    """Fill a text input field."""
    try:
        await page.fill(selector, value, timeout=timeout)
        return {
            "success": True,
            "action": "fill",
            "selector": selector,
            "value": value,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "fill",
            "selector": selector,
            "error": str(e),
            "suggestion": "Try a different selector. Use 'extract' to inspect the page.",
        }


async def action_click(page, selector: str, timeout: int = 10000) -> dict:
    """Click an element."""
    try:
        await page.click(selector, timeout=timeout)
        # Wait briefly for navigation or dynamic content
        await page.wait_for_load_state("networkidle", timeout=5000)
        title = await page.title()
        return {
            "success": True,
            "action": "click",
            "selector": selector,
            "url": page.url,
            "title": title,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "click",
            "selector": selector,
            "error": str(e),
            "suggestion": "Element may not be visible or clickable. Try waiting first.",
        }


async def action_select(page, selector: str, value: str, timeout: int = 10000) -> dict:
    """Select an option from a <select> dropdown."""
    try:
        await page.select_option(selector, value, timeout=timeout)
        return {
            "success": True,
            "action": "select",
            "selector": selector,
            "value": value,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "select",
            "selector": selector,
            "error": str(e),
        }


async def action_wait(page, selector: str, timeout: int = 10000) -> dict:
    """Wait for an element to appear."""
    try:
        await page.wait_for_selector(selector, timeout=timeout, state="visible")
        return {
            "success": True,
            "action": "wait",
            "selector": selector,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "wait",
            "selector": selector,
            "error": str(e),
            "suggestion": "Element did not appear within timeout. The page may still be loading.",
        }


async def action_extract(
    page, selector: str, fmt: str = "text", timeout: int = 10000
) -> dict:
    """Extract content from elements matching a selector.

    Args:
        fmt: "text" for text content, "json" for structured element data, "html" for innerHTML
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout, state="attached")
        elements = await page.query_selector_all(selector)

        results = []
        for el in elements[:50]:  # Limit to prevent massive output
            if fmt == "json":
                data = await el.evaluate(
                    """(el) => {
                        const attrs = {};
                        for (const attr of el.attributes) {
                            attrs[attr.name] = attr.value;
                        }
                        return {
                            tag: el.tagName.toLowerCase(),
                            text: el.innerText?.trim().substring(0, 500),
                            attributes: attrs,
                        };
                    }"""
                )
                results.append(data)
            elif fmt == "html":
                html = await el.inner_html()
                results.append(html[:2000])
            else:
                text = await el.inner_text()
                results.append(text.strip()[:500])

        return {
            "success": True,
            "action": "extract",
            "selector": selector,
            "format": fmt,
            "count": len(results),
            "data": results,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "extract",
            "selector": selector,
            "error": str(e),
            "suggestion": "Selector not found. Use 'extract body --format json' to inspect the full page.",
        }


async def action_screenshot(page, output_path: str, full_page: bool = False) -> dict:
    """Take a screenshot of the current page."""
    try:
        await page.screenshot(path=output_path, full_page=full_page)
        return {
            "success": True,
            "action": "screenshot",
            "path": output_path,
            "url": page.url,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "screenshot",
            "error": str(e),
        }


async def action_scroll(page, direction: str = "down", amount: int = 500) -> dict:
    """Scroll the page."""
    try:
        delta = amount if direction == "down" else -amount
        await page.mouse.wheel(0, delta)
        await page.wait_for_timeout(500)  # Brief pause for content to load
        return {
            "success": True,
            "action": "scroll",
            "direction": direction,
            "amount": amount,
        }
    except Exception as e:
        return {"success": False, "action": "scroll", "error": str(e)}


async def action_evaluate(page, js_expression: str) -> dict:
    """Evaluate arbitrary JavaScript in the page context."""
    try:
        result = await page.evaluate(js_expression)
        # Ensure result is JSON-serializable
        json.dumps(result)
        return {
            "success": True,
            "action": "evaluate",
            "result": result,
        }
    except (TypeError, ValueError):
        return {
            "success": True,
            "action": "evaluate",
            "result": str(result),
        }
    except Exception as e:
        return {
            "success": False,
            "action": "evaluate",
            "error": str(e),
        }


async def action_type(page, selector: str, text: str, delay: int = 50, timeout: int = 10000) -> dict:
    """Type text character by character (for inputs that don't work with fill)."""
    try:
        await page.click(selector, timeout=timeout)
        await page.keyboard.type(text, delay=delay)
        return {
            "success": True,
            "action": "type",
            "selector": selector,
            "text": text,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "type",
            "selector": selector,
            "error": str(e),
        }


async def action_press(page, key: str) -> dict:
    """Press a keyboard key (Enter, Tab, Escape, etc.)."""
    try:
        await page.keyboard.press(key)
        await page.wait_for_timeout(300)
        return {
            "success": True,
            "action": "press",
            "key": key,
        }
    except Exception as e:
        return {"success": False, "action": "press", "error": str(e)}
