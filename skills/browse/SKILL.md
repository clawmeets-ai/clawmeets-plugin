---
name: browse
description: >
  Browse and interact with any website in real time using a browser toolkit.
  Navigate pages, fill forms, click buttons, extract data, and take screenshots.
  Use when agents need to visit a website, search for information on a web page,
  fill out a form, or extract data from a dynamically rendered site.
---

# Browse Website

Navigate and interact with websites in real time using the browser toolkit.

The toolkit lives at `${CLAUDE_PLUGIN_ROOT}/toolkit/navigator/`, where
`${CLAUDE_PLUGIN_ROOT}` is the absolute path to this plugin (set by Claude
Code for both installed and `--plugin-dir` plugins).

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT}/toolkit/navigator"
echo "Navigator toolkit: $PLUGIN_DIR"
[ -f "$PLUGIN_DIR/navigator.py" ] || echo "Navigator not found at $PLUGIN_DIR"
```

If `$CLAUDE_PLUGIN_ROOT` is empty (very old Claude Code builds), fall back to
searching the monorepo source checkout:
```bash
if [ -z "$PLUGIN_DIR" ] || [ ! -f "$PLUGIN_DIR/navigator.py" ]; then
  for d in plugins/clawmeets/toolkit/navigator ../../plugins/clawmeets/toolkit/navigator; do
    if [ -f "$d/navigator.py" ]; then PLUGIN_DIR="$(cd "$d" && pwd)"; break; fi
  done
fi
```

## Prerequisites

- Python 3.11+ with Playwright installed: `pip install playwright && playwright install chromium`

## Browser Modes

The toolkit supports three browser modes via environment variables:

| Mode | How to enable | Use case |
|------|--------------|----------|
| Headless (default) | Default, no env vars needed | Automated background tasks |
| Visible browser | `export NAVIGATOR_HEADLESS=0` | Debugging, watching navigation |
| External Chrome | `export NAVIGATOR_CDP_URL=http://localhost:9222` | Use real Chrome with your profile, extensions, logged-in sessions |

To use an external Chrome, launch it first with a remote debugging port. The
command varies by platform:

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222

# Windows (PowerShell)
& "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

## Commands

All commands require `--session <id>` for browser context isolation. Use a unique ID per task (e.g., project name, chatroom ID).

```bash
NAV="python $PLUGIN_DIR/navigator.py"

# Navigate to a URL
$NAV --session <id> goto "<url>"

# Fill a form field
$NAV --session <id> fill "<selector>" "<value>"

# Type text character by character (for dynamic/autocomplete inputs)
$NAV --session <id> type "<selector>" "<text>"

# Click an element
$NAV --session <id> click "<selector>"

# Select from dropdown
$NAV --session <id> select "<selector>" "<value>"

# Wait for element to appear
$NAV --session <id> wait "<selector>" --timeout 15000

# Extract content from elements
$NAV --session <id> extract "<selector>" --format json

# Press a key (Enter, Tab, Escape, etc.)
$NAV --session <id> press Enter

# Scroll the page
$NAV --session <id> scroll --direction down --amount 500

# Take a screenshot
$NAV --session <id> screenshot --output /tmp/page.png

# Run JavaScript
$NAV --session <id> evaluate "document.title"

# Check session status
$NAV --session <id> status

# Close session when done
$NAV --session <id> close
```

## Steps

1. **Locate the toolkit** using the script above. Store the path in `$PLUGIN_DIR`.

2. **Check learnings** (if a knowledge directory with learnings exists):
   - Read `learnings/INDEX.md` for relevant past experience with this site
   - Check `learnings/selectors.md` for known-working selectors
   - Check `learnings/failures.md` for approaches to avoid

3. **Navigate** to the target URL:
   ```bash
   python $PLUGIN_DIR/navigator.py --session mysession goto "https://example.com"
   ```

4. **Interact** with the page as needed (fill forms, click buttons, wait for content).

5. **Extract** the data you need:
   ```bash
   python $PLUGIN_DIR/navigator.py --session mysession extract ".results" --format json
   ```

6. **Close** the session when done:
   ```bash
   python $PLUGIN_DIR/navigator.py --session mysession close
   ```

7. **Save learnings** (if you have a knowledge directory with write access):
   If any selectors, workflows, or approaches differed from your defaults or previous learnings, save what you discovered:
   - New/changed selectors → append to `learnings/selectors.md`
   - Refined workflow steps → append to `learnings/workflows.md`
   - Failed approaches → append to `learnings/failures.md`
   - Update `learnings/INDEX.md` with a one-line summary

   Skip this step if nothing new was learned or if the interaction was routine.

## Guidelines

- **Start with `goto`** to navigate to the relevant page
- **Use `wait`** after clicking to ensure dynamic content loads
- **Use `extract`** to read results before responding
- **Use `type` instead of `fill`** for inputs with autocomplete or dynamic behavior
- **Take screenshots** to diagnose unexpected page states
- **Always close** the session when done

## Error Handling

- All commands return JSON with `success: true/false`
- If a selector fails, try `extract body --format json` to inspect the page
- If a page times out, try a shorter wait or check if the URL is correct
- If you encounter a CAPTCHA, inform the user that manual intervention is needed
- Take a screenshot to diagnose unexpected page states
