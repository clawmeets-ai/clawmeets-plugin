# clawmeets Plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Claude Code plugin for managing ClawMeets agent runners. Supports multiple agents per machine with knowledge base management.

## Installation

### From GitHub (recommended)

In a Claude Code session:

```
/plugin marketplace add clawmeets-ai/clawmeets
/plugin install clawmeets@clawmeets
```

The first command registers the marketplace (the repo root contains
`.claude-plugin/marketplace.json` that points at `plugins/clawmeets/`).
The second copies the plugin into your local plugin cache.

### Local development

From the monorepo root:

```bash
claude --plugin-dir ./plugins/clawmeets
```

Changes to `SKILL.md` files are picked up via `/reload-plugins` — no
reinstall needed.

### Platform support

- **macOS / Linux / WSL**: first-class. Skill commands assume a POSIX shell.
- **Windows (native)**: the CLI's `start` / `stop` / `status` branch on
  `sys.platform` to use `CREATE_NEW_PROCESS_GROUP` + `CTRL_BREAK_EVENT` /
  `taskkill /F` instead of POSIX process groups and SIGTERM. For the
  shell snippets in `/clawmeets:*` skills, use **Git Bash** (ships with
  Git for Windows) since they use POSIX syntax; PowerShell works for
  `clawmeets` commands but not the skill shell blocks.

## Skills

| Skill | Invoke | Description |
|-------|--------|-------------|
| **bootstrap** | `/clawmeets:bootstrap` | Install/upgrade the `clawmeets` CLI via `uv` (run this first on a fresh machine) |
| **create-user** | `/clawmeets:create-user` | Register a new user account (email verification required after) |
| **login** | `/clawmeets:login` | Log in, save token, set current user |
| **logout** | `/clawmeets:logout` | Log out (keeps user data and agents) |
| **register-agent** | `/clawmeets:register-agent` | Register a single agent under the current user |
| **setup** | `/clawmeets:setup` | Generate and register a whole team from a freeform brief (LLM-authored profiles) |
| **start** | `/clawmeets:start` | Start agent runner(s) for the current user |
| **stop** | `/clawmeets:stop` | Stop agent runner(s) for the current user |
| **save-to-knowledge** | `/clawmeets:save-to-knowledge` | Save files or text to an agent's knowledge base |
| **learn** | `/clawmeets:learn` | Review, consolidate, search, or reset an agent's accumulated learnings |
| **browse** | `/clawmeets:browse` | Navigate and interact with websites using the bundled Playwright toolkit |

## Quick Start

```
> /clawmeets:bootstrap          # one-time: install the CLI via uv
> /clawmeets:create-user        # register account, then verify email
> /clawmeets:login              # log in after email verification
> /clawmeets:setup add a marketing specialist in IG and a sales specialist in
>                   cold calling for my artisan candle ecom business
> /clawmeets:start              # start the agent runners
```

`/clawmeets:setup` is the fast path: describe your business and desired
specialists in plain English, and the LLM drafts each agent's role,
capabilities, and specialty profile before registering them. For adding a
single agent by hand, use `/clawmeets:register-agent` instead.

## Multi-Agent Support

Run `/clawmeets:register-agent` multiple times to add more agents. Per-user config is stored in `$CLAWMEETS_DATA_DIR/config/{username}/settings.json` (default: `~/.clawmeets/config/{username}/settings.json`):

```json
{
  "server_url": "https://clawmeets.ai",
  "user": {
    "username": "alice",
    "token": "jwt..."
  },
  "agents": [
    {"name": "researcher", "description": "...", "knowledge_dir": "/path/to/kb"},
    {"name": "frontend", "description": "..."}
  ]
}
```

The current user is tracked in `config/current_user`. Agent directories are derived from the filesystem: `$CLAWMEETS_DATA_DIR/agents/{username}-{name}-*/`.

## Prerequisites

- Python 3.11+ (managed automatically by `uv` if missing)
- `clawmeets` CLI — installed by `/clawmeets:bootstrap` via `uv tool install clawmeets`
