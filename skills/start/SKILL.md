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
   cat ~/.clawmeets/config.json
   ```
   - If no `current_user` set: "You need to log in first. Run `/clawmeets:login`."
   - Extract `server_url` and `users.{current_user}.agents`
   - If no agents configured: "No agents registered. Run `/clawmeets:register-agent` first."

2. **Determine which agent(s) to start**:
   ```bash
   python3 -c "
   import json
   from pathlib import Path
   config = json.loads((Path.home() / '.clawmeets' / 'config.json').read_text())
   user = config['users'][config['current_user']]
   for name in user.get('agents', {}):
       print(name)
   "
   ```
   - If **one agent**: start it directly.
   - If **multiple agents**: ask "Which agent to start? [list] or 'all'"

3. **For each agent to start**:
   ```bash
   AGENT_NAME="<name>"
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

   # Read agent config
   eval $(python3 -c "
   import json
   from pathlib import Path
   config = json.loads((Path.home() / '.clawmeets' / 'config.json').read_text())
   agent = config['users'][config['current_user']]['agents']['$AGENT_NAME']
   print(f\"SERVER_URL='{config['server_url']}'\")
   print(f\"AGENT_DIR='{agent['agent_dir']}'\")
   kb = agent.get('knowledge_dir') or ''
   print(f\"KB_DIR='{kb}'\")
   cpd = agent.get('claude_plugin_dir') or ''
   print(f\"CLAUDE_PLUGIN_DIR='{cpd}'\")
   ")

   # Build command
   CMD="clawmeets agent run --server $SERVER_URL --agent-dir $AGENT_DIR"
   if [ -n "$KB_DIR" ]; then
     CMD="$CMD --knowledge-dir $KB_DIR"
   fi
   if [ -n "$CLAUDE_PLUGIN_DIR" ]; then
     CMD="$CMD --claude-plugin-dir $CLAUDE_PLUGIN_DIR"
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
