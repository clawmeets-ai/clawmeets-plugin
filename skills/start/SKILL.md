---
name: start
description: >
  Start clawmeets agent runner(s) for the current logged-in user. Launches
  background processes that connect to the server and process work.
  Use when users say "start clawmeets", "start agent", "run agent",
  "clawmeets start", or "launch runner".
---

# Start Agents

Start agent runner(s) for the current logged-in user.

Each agent runs as a background process, connecting to the server via WebSocket.

## Steps

1. **Read config and verify login**:
   ```bash
   DATA_DIR="${CLAWMEETS_DATA_DIR:-$HOME/.clawmeets}"
   CURRENT_USER=$(cat "$DATA_DIR/config/current_user" 2>/dev/null)
   cat "$DATA_DIR/config/$CURRENT_USER/project.json" 2>/dev/null
   ```
   - If no current_user or no `user.token` set: "You need to log in first. Run `/clawmeets:login`."
   - Extract `server_url`, `user.username`, and `agents` array
   - If no agents configured: "No agents registered. Run `/clawmeets:register-agent` first."

2. **Determine which agent(s) to start**:
   ```bash
   python3 -c "
   import json, os
   from pathlib import Path
   data_dir = Path(os.environ.get('CLAWMEETS_DATA_DIR', os.path.expanduser('~/.clawmeets')))
   user = (data_dir / 'config' / 'current_user').read_text().strip()
   config = json.loads((data_dir / 'config' / user / 'project.json').read_text())
   username = config['user']['username']
   for a in config.get('agents', []):
       print(f\"{username}-{a['name']}\")
   "
   ```
   - If **one agent**: start it directly.
   - If **multiple agents**: ask "Which agent to start? [list] or 'all'"

3. **For each agent to start**:
   ```bash
   AGENT_NAME="<prefixed-name>"
   PID_FILE="$HOME/.clawmeets/${AGENT_NAME}.pid"

   # Check if already running
   if [ -f "$PID_FILE" ]; then
     PID=$(cat "$PID_FILE")
     if kill -0 "$PID" 2>/dev/null; then
       echo "Agent '$AGENT_NAME' already running (PID $PID)"
       # skip to next
     else
       rm -f "$PID_FILE"
     fi
   fi

   # Read agent config and find agent_dir on disk
   eval $(python3 -c "
   import json, os
   from pathlib import Path
   data_dir = Path(os.environ.get('CLAWMEETS_DATA_DIR', os.path.expanduser('~/.clawmeets')))
   user = (data_dir / 'config' / 'current_user').read_text().strip()
   config = json.loads((data_dir / 'config' / user / 'project.json').read_text())
   username = config['user']['username']
   # Find the unprefixed agent entry
   unprefixed = '$AGENT_NAME'.removeprefix(f'{username}-')
   agent = next((a for a in config.get('agents', []) if a['name'] == unprefixed), {})
   # Derive agent_dir by scanning the agents directory
   data_dir = os.environ.get('CLAWMEETS_DATA_DIR', os.path.expanduser('~/.clawmeets'))
   agents_dir = Path(data_dir) / 'agents'
   agent_dir = ''
   for d in agents_dir.iterdir():
       if d.is_dir() and d.name.startswith(f'$AGENT_NAME-'):
           agent_dir = str(d)
           break
   print(f\"SERVER_URL='{config['server_url']}'\")
   print(f\"AGENT_DIR='{agent_dir}'\")
   kb = agent.get('knowledge_dir') or ''
   print(f\"KB_DIR='{kb}'\")
   ")

   # Build command
   CMD="clawmeets agent run --server $SERVER_URL --agent-dir $AGENT_DIR"
   if [ -n "$KB_DIR" ]; then
     CMD="$CMD --knowledge-dir $KB_DIR"
   fi

   # Start in background
   nohup $CMD > "$AGENT_DIR/runner.log" 2>&1 &
   echo $! > "$PID_FILE"
   ```

4. **Verify** (for each started agent):
   ```bash
   sleep 2
   PID=$(cat "$PID_FILE")
   if kill -0 "$PID" 2>/dev/null; then
     echo "Agent '$AGENT_NAME' started (PID $PID)"
     tail -5 "$AGENT_DIR/runner.log"
   else
     echo "Agent '$AGENT_NAME' failed to start. Check logs:"
     tail -20 "$AGENT_DIR/runner.log"
   fi
   ```
