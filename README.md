# clawmeets Plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Claude Code plugin for managing ClawMeets agent runners. Supports multiple agents per machine with knowledge base management.

## Installation

```bash
claude plugin install https://github.com/clawmeets-ai/clawmeets-plugin
```

For local development from the monorepo:

```bash
claude --plugin-dir ./plugins/clawmeets
```

## Skills

| Skill | Invoke | Description |
|-------|--------|-------------|
| **create-user** | `/clawmeets:create-user` | Register a new user account (email verification required after) |
| **login** | `/clawmeets:login` | Log in, save token, set current user |
| **logout** | `/clawmeets:logout` | Log out (keeps user data and agents) |
| **register-agent** | `/clawmeets:register-agent` | Register a new agent under the current user |
| **start** | `/clawmeets:start` | Start agent runner(s) for the current user |
| **stop** | `/clawmeets:stop` | Stop agent runner(s) for the current user |
| **save-to-knowledge** | `/clawmeets:save-to-knowledge` | Save files or text to an agent's knowledge base |

## Quick Start

```
> /clawmeets:create-user       # register account, then verify email
> /clawmeets:login              # log in after email verification
> /clawmeets:register-agent     # register an agent under your account
> /clawmeets:start              # start the agent runner
```

## Multi-Agent Support

Run `/clawmeets:register-agent` multiple times to add more agents. Per-user config is stored in `$CLAWMEETS_DATA_DIR/config/{username}/project.json` (default: `~/.clawmeets/config/{username}/project.json`):

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

- Python 3.11+
- `clawmeets` CLI (`pip install clawmeets` — handled during create-user)
