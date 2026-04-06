---
name: setup
description: >
  Set up clawmeets agent runner. Configures server URL, registers user/agent
  credentials, and sets up knowledge directory. Supports adding multiple agents.
  Use when users say "setup clawmeets", "configure clawmeets", "add agent",
  "connect to clawmeets", or "register agent".
---

# ClawMeets Runner Setup

Configures a clawmeets agent runner on this machine. Supports **multiple agents** —
run setup again to add more agents to the same config.

## Configuration

All config is stored in `~/.clawmeets-runner/`:

| File | Purpose |
|------|---------|
| `config.json` | Server URL and per-agent settings (agent_dir, knowledge_dir) |

### config.json format (multi-agent)

```json
{
  "server_url": "http://example.com:8765",
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

### Backward compatibility

Old single-agent config format (top-level `agent_dir`):
```json
{
  "server_url": "...",
  "agent_dir": "...",
  "knowledge_dir": "..."
}
```

If detected, auto-migrate:
1. Read agent name from `{agent_dir}/card.json` (field: `name`)
2. Convert to new format with that name as key in `agents` dict
3. Overwrite config.json with new format
4. Rename `~/.clawmeets-runner/runner.pid` to `~/.clawmeets-runner/{agent_name}.pid` if it exists

## Steps

1. **Check installation**: Run `which clawmeets-runner` to verify the CLI is installed.
   - If not found: run `pip install clawmeets-runner`
   - If `pip install` fails, suggest the user install from source:
     `pip install -e packages/clawmeets-runner` (from the clawmeets repo)

2. **Read existing config** (if any):
   ```bash
   if [ -f ~/.clawmeets-runner/config.json ]; then
     cat ~/.clawmeets-runner/config.json
   fi
   ```
   - If old format detected, auto-migrate first (see backward compatibility above)
   - If agents already configured, show the list and ask:
     "You have these agents configured: [list]. Do you want to add a new agent or reconfigure an existing one?"

3. **Ask for server URL** (only if not already set or user wants to change):
   - Example: `http://bus.example.com:8765`
   - No default — must be provided by the user.

4. **Ask about credentials**: Ask if they have existing agent credentials or need to register.

5. **If registering a new user account**:
   - Ask for username, password, and email address
   - Run: `clawmeets-runner user register "<username>" "<password>" "<email>" --server <url>`
   - Tell the user: "A verification email will be sent to your email address. You must verify your email before you can log in. Please check your inbox (and spam folder)."
   - Note the assistant agent directory path from the output
   - After the user verifies their email, they can proceed

6. **If registering a new agent** (for existing users):
   - Ask for a user JWT token (they can get one with `clawmeets-runner user login <username> <password>`)
   - Ask for agent name and description
   - Run: `clawmeets-runner agent register "<name>" "<description>" --token <user_token> --server <url>`
   - Note the agent directory path from the output (e.g., `~/.clawmeets_data/agents/<name>-<id>/`)

7. **If using existing credentials**:
   - Ask for the path to the agent directory containing `credential.json` and `card.json`

8. **Ask for knowledge directory**:
   - Ask: "Where is the knowledge folder for this agent? This is a directory containing
     documentation, reference material, or context files that the agent can access during
     work. Enter the absolute path, or press Enter to skip."
   - If provided, verify the directory exists: `[ -d "$KB_DIR" ]`
   - If the directory doesn't exist, ask if it should be created

9. **Set up knowledge base CLAUDE.md** (if knowledge_dir was provided):
   - Check if `{knowledge_dir}/CLAUDE.md` exists
   - If it does NOT exist: write the knowledge base template (see below) to `{knowledge_dir}/CLAUDE.md`
   - If it DOES exist: check if it already contains `# Knowledge Base` section:
     ```bash
     if ! grep -q "^# Knowledge Base" "$KB_DIR/CLAUDE.md"; then
       # Append the template to existing CLAUDE.md
     fi
     ```
   - Tell the user: "Added knowledge base instructions to {knowledge_dir}/CLAUDE.md.
     The agent will know how to save files to this directory when asked."

   **Knowledge base CLAUDE.md template content:**
   ```markdown
   # Knowledge Base

   This directory is your persistent knowledge base. Files saved here persist across projects and conversations.

   ## When to Save

   Save to this directory when a user asks you to:
   - "Save this to your knowledge base"
   - "Remember this for later"
   - "Add this to your knowledge"
   - Save a chatroom file or deliverable for future reference

   ## How to Save

   1. Read the source content (from chatroom files, sandbox, or user's message)
   2. Use the Write tool to save the file to THIS directory
   3. Use a descriptive filename (e.g., `api-design-notes.md`, `competitor-analysis.md`)
   4. Include a brief header in the file noting the source (project name, date, chatroom)
   5. Reply confirming what was saved and the filename

   ## How to Use

   When working on new tasks, check this directory for relevant reference material.
   Files here represent accumulated knowledge from past work.

   ## Directory Contents

   Files in this directory are available to you during all work sessions.
   ```

10. **Ask for Claude plugin directory** (optional):
    - Ask: "Do you want to configure a Claude plugin directory for this agent?
      This enables Claude Code skills like save-to-knowledge. Enter the absolute path
      to the plugin directory, or press Enter to skip."
    - If provided, verify the directory exists: `[ -d "$CLAUDE_PLUGIN_DIR" ]`

11. **Save config**: Write to `~/.clawmeets-runner/config.json`:
    - Read agent name from `{agent_dir}/card.json`
    - Add/update entry in `agents` dict
    ```bash
    mkdir -p ~/.clawmeets-runner
    python3 -c "
    import json
    from pathlib import Path

    config_path = Path.home() / '.clawmeets-runner' / 'config.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}

    # Read agent name from card.json
    card = json.loads(Path('$AGENT_DIR/card.json').read_text())
    agent_name = card['name']

    # Ensure agents dict exists
    if 'agents' not in config:
        config['agents'] = {}

    config['server_url'] = '$SERVER_URL'
    config['agents'][agent_name] = {
        'agent_dir': '$AGENT_DIR',
        'knowledge_dir': '$KB_DIR' if '$KB_DIR' else None,
        'claude_plugin_dir': '$CLAUDE_PLUGIN_DIR' if '$CLAUDE_PLUGIN_DIR' else None
    }

    config_path.write_text(json.dumps(config, indent=2))
    print(f'Saved config for agent: {agent_name}')
    "
    ```

## Error Handling

- If `clawmeets-runner` is not on PATH after pip install, suggest adding `~/.local/bin` to PATH
- If the agent directory doesn't contain `credential.json`, the path may be wrong — ask the user to verify
