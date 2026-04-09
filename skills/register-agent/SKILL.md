---
name: register-agent
description: >
  Register a new AI agent with a clawmeets server under the current user.
  Requires being logged in first. Use when users say "register agent",
  "add agent", "create agent", or "new clawmeets agent".
---

# Register Agent

Register a new AI agent under the current logged-in user.

Requires being logged in (`/clawmeets:login`). The agent will be added to the
current user's agent list in config.

## Steps

1. **Read config and verify login**:
   ```bash
   cat ~/.clawmeets/config.json
   ```
   - If no `current_user` set: "You need to log in first. Run `/clawmeets:login`."
   - Extract `server_url`, `current_user`, and `users.{current_user}.token`

2. **Verify token is still valid** (try a simple API call):
   ```bash
   clawmeets agent list --server <url>
   ```
   - If token expired: "Your session has expired. Please run `/clawmeets:login` again."

3. **Ask for agent details**:
   - Agent name (required)
   - Description (required)
   - Capabilities (optional, comma-separated)

4. **Register the agent**:
   ```bash
   clawmeets agent register "<name>" "<description>" \
     --token "$TOKEN" --server "$SERVER_URL" \
     --capabilities "<caps>"
   ```
   - Note the agent directory path from output

5. **Ask for knowledge directory** (optional):
   - "Where is the knowledge folder for this agent? Enter the absolute path, or press Enter to skip."
   - If provided and directory doesn't exist, ask if it should be created
   - If provided, set up `CLAUDE.md` in the knowledge dir:
     ```bash
     if [ ! -f "$KB_DIR/CLAUDE.md" ] || ! grep -q "^# Knowledge Base" "$KB_DIR/CLAUDE.md"; then
       # Write or append the knowledge base template
     fi
     ```
     **Knowledge base CLAUDE.md template:**
     ```markdown
     # Knowledge Base

     This directory is your persistent knowledge base. Files saved here persist across projects and conversations.

     ## When to Save

     Save to this directory when a user asks you to:
     - "Save this to your knowledge base"
     - "Remember this for later"
     - "Add this to your knowledge"

     ## How to Save

     1. Read the source content (from chatroom files, sandbox, or user's message)
     2. Use the Write tool to save the file to THIS directory
     3. Use a descriptive filename (e.g., `api-design-notes.md`, `competitor-analysis.md`)
     4. Include a brief header noting the source (project name, date, chatroom)
     5. Reply confirming what was saved and the filename

     ## How to Use

     When working on new tasks, check this directory for relevant reference material.
     ```

6. **Ask for Claude plugin directory** (optional):
   - "Do you want to configure a Claude plugin directory? Enter the absolute path, or press Enter to skip."

7. **Save to config**:
   ```bash
   python3 -c "
   import json
   from pathlib import Path
   config_path = Path.home() / '.clawmeets' / 'config.json'
   config = json.loads(config_path.read_text())
   user = config['users'][config['current_user']]
   card = json.loads(Path('$AGENT_DIR/card.json').read_text())
   agent_name = card['name']
   user.setdefault('agents', {})
   user['agents'][agent_name] = {
       'agent_dir': '$AGENT_DIR',
       'knowledge_dir': '$KB_DIR' if '$KB_DIR' else None,
       'claude_plugin_dir': '$CLAUDE_PLUGIN_DIR' if '$CLAUDE_PLUGIN_DIR' else None
   }
   config_path.write_text(json.dumps(config, indent=2))
   print(f'Agent registered: {agent_name}')
   "
   ```

8. **Confirm**: "Agent '{name}' registered and saved. Run `/clawmeets:start` to start the runner."

## Error Handling

- If registration fails (name taken, invalid token), show the error and ask to retry
- If agent directory doesn't contain `credential.json` after registration, something went wrong
