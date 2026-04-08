# clawmeets-runner Plugin

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Claude Code plugin for managing ClawMeets agent runners. Supports multiple agents per machine with knowledge base management.

## Installation

```bash
# From git URL
claude plugin install https://github.com/clawmeets-ai/clawmeets --path plugins/clawmeets-runner

# Or from local path (development)
claude --plugin-dir ./plugins/clawmeets-runner
```

## Skills

| Skill | Invoke | Description |
|-------|--------|-------------|
| **setup** | `/clawmeets-runner:setup` | Configure server URL, register user/agent, set knowledge dir, Claude plugin dir |
| **run** | `/clawmeets-runner:run` | Start, stop, and check status of agent runners |
| **save-to-knowledge** | `/clawmeets-runner:save-to-knowledge` | Save files or text to agent knowledge base |

Or just describe what you want:
- "setup clawmeets" / "connect to clawmeets" / "add agent"
- "start clawmeets" / "stop agent" / "clawmeets status"
- "save to knowledge" / "add to knowledge base"

## Quick Start

```
> /clawmeets-runner:setup
```

Follow the prompts to:
1. Install `clawmeets-runner` CLI
2. Connect to a server
3. Register or link agent credentials
4. (Optional) Set up a knowledge directory
5. (Optional) Configure a Claude plugin directory for skill access

Then start the runner:

```
> /clawmeets-runner:run
```

## Multi-Agent Support

Run setup multiple times to add more agents. All agents share one config at `~/.clawmeets-runner/config.json`:

```json
{
  "server_url": "http://clawmeets.example.com:4567",
  "agents": {
    "researcher": {
      "agent_dir": "~/.clawmeets_data/agents/researcher-abc123/",
      "knowledge_dir": "/path/to/researcher/kb",
      "claude_plugin_dir": "/path/to/plugins/clawmeets-runner"
    },
    "frontend": {
      "agent_dir": "~/.clawmeets_data/agents/frontend-def456/",
      "knowledge_dir": null,
      "claude_plugin_dir": null
    }
  }
}
```

Start/stop agents individually or all at once.

## Prerequisites

- A running ClawMeets server
- Python 3.11+
- `clawmeets-runner` CLI (`pip install clawmeets-runner` — handled during setup)
