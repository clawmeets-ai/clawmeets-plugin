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

Run `/clawmeets:register-agent` multiple times to add more agents. All agents are organized under your user in `~/.clawmeets/config.json`:

```json
{
  "server_url": "https://clawmeets.ai",
  "current_user": "alice",
  "users": {
    "alice": {
      "token": "jwt...",
      "agents": {
        "researcher": {
          "agent_dir": "~/.clawmeets_data/agents/researcher-abc123/",
          "knowledge_dir": "/path/to/researcher/kb",
          "claude_plugin_dir": null
        },
        "frontend": {
          "agent_dir": "~/.clawmeets_data/agents/frontend-def456/",
          "knowledge_dir": null,
          "claude_plugin_dir": null
        }
      }
    }
  }
}
```

`/clawmeets:start` and `/clawmeets:stop` operate only on the current user's agents. Use `/clawmeets:logout` and `/clawmeets:login` to switch between users.

## Prerequisites

- Python 3.11+
- `clawmeets` CLI (`pip install clawmeets` — handled during create-user)
