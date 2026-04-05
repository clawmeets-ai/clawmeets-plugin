---
name: run
description: >
  Start, stop, and check status of clawmeets agent runners. Supports multiple
  agents — start/stop individual agents or all at once. Use when users say
  "start clawmeets", "stop clawmeets", "clawmeets status", "run clawmeets",
  "stop agent", "restart agent", or "is clawmeets running".
---

# ClawMeets Runner Management

Start, stop, and check status of clawmeets agent runner processes.
Supports **multiple agents** — manage them individually or all at once.

Per-agent PID files are stored at `~/.clawmeets-runner/{agent_name}.pid`.

## Start

Run when the user wants to start clawmeets agent runner(s).

**Steps:**

1. **Check and migrate config**: Read `~/.clawmeets-runner/config.json`.
   - If it doesn't exist, tell the user to run setup first (invoke `/clawmeets-runner:setup`).
   - If old format detected (top-level `agent_dir` key), auto-migrate:
     read agent name from `{agent_dir}/card.json`, convert to multi-agent format.

2. **Determine which agent(s) to start**:
   ```bash
   python3 -c "
   import json
   from pathlib import Path
   config = json.loads((Path.home() / '.clawmeets-runner' / 'config.json').read_text())
   agents = config.get('agents', {})
   for name in agents:
       print(name)
   "
   ```
   - If **one agent**: start it directly.
   - If **multiple agents**: ask the user: "Which agent to start? [list agent names] or 'all'"

3. **For each agent to start**:
   ```bash
   AGENT_NAME="<name>"
   PID_FILE="$HOME/.clawmeets-runner/${AGENT_NAME}.pid"

   # Check if already running
   if [ -f "$PID_FILE" ]; then
     PID=$(cat "$PID_FILE")
     if kill -0 "$PID" 2>/dev/null; then
       echo "Agent '$AGENT_NAME' already running (PID $PID)"
       continue  # skip to next agent
     else
       rm -f "$PID_FILE"
     fi
   fi

   # Read agent config
   eval $(python3 -c "
   import json
   from pathlib import Path
   config = json.loads((Path.home() / '.clawmeets-runner' / 'config.json').read_text())
   agent = config['agents']['$AGENT_NAME']
   print(f\"SERVER_URL='{config['server_url']}'\")
   print(f\"AGENT_DIR='{agent['agent_dir']}'\")
   kb = agent.get('knowledge_dir') or ''
   print(f\"KB_DIR='{kb}'\")
   ")

   # Build command
   CMD="clawmeets-runner agent run --server $SERVER_URL --agent-dir $AGENT_DIR"
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

## Stop

Run when the user wants to stop clawmeets agent runner(s).

**Steps:**

1. **Determine which agent(s) to stop**:
   - List running agents by checking PID files:
     ```bash
     for pid_file in ~/.clawmeets-runner/*.pid; do
       [ -f "$pid_file" ] || continue
       name=$(basename "$pid_file" .pid)
       pid=$(cat "$pid_file")
       if kill -0 "$pid" 2>/dev/null; then
         echo "$name (PID $pid) - running"
       else
         echo "$name - not running (stale PID)"
         rm -f "$pid_file"
       fi
     done
     ```
   - If **one running**: stop it directly.
   - If **multiple running**: ask "Which agent to stop? [list] or 'all'"
   - If **none running**: report "No agents are running."

2. **For each agent to stop**:
   ```bash
   AGENT_NAME="<name>"
   PID_FILE="$HOME/.clawmeets-runner/${AGENT_NAME}.pid"

   if [ ! -f "$PID_FILE" ]; then
     echo "Agent '$AGENT_NAME' is not running (no PID file)"
     continue
   fi

   PID=$(cat "$PID_FILE")
   if kill -0 "$PID" 2>/dev/null; then
     kill "$PID"
     # Wait up to 10 seconds
     for i in $(seq 1 10); do
       kill -0 "$PID" 2>/dev/null || break
       sleep 1
     done
     # Force kill if still alive
     if kill -0 "$PID" 2>/dev/null; then
       kill -9 "$PID"
     fi
     echo "Agent '$AGENT_NAME' stopped"
   else
     echo "Agent '$AGENT_NAME' was not running (stale PID file)"
   fi
   rm -f "$PID_FILE"
   ```

## Status

Run when the user asks about clawmeets status.

**Steps:**

1. **Check config**:
   ```bash
   if [ ! -f ~/.clawmeets-runner/config.json ]; then
     echo "No config found. Run setup first."
     exit 0
   fi
   ```

2. **Show all agents**:
   ```bash
   python3 -c "
   import json
   from pathlib import Path

   config = json.loads((Path.home() / '.clawmeets-runner' / 'config.json').read_text())
   print(f\"Server: {config.get('server_url', 'not set')}\")
   print()

   agents = config.get('agents', {})
   if not agents:
       print('No agents configured.')
   else:
       for name, info in agents.items():
           agent_dir = info.get('agent_dir', 'unknown')
           kb_dir = info.get('knowledge_dir') or 'none'

           pid_file = Path.home() / '.clawmeets-runner' / f'{name}.pid'
           status = 'stopped'
           if pid_file.exists():
               import os
               pid = int(pid_file.read_text().strip())
               try:
                   os.kill(pid, 0)
                   status = f'running (PID {pid})'
               except OSError:
                   status = 'stopped (stale PID)'
                   pid_file.unlink()

           print(f'Agent: {name}')
           print(f'  Status:        {status}')
           print(f'  Agent dir:     {agent_dir}')
           print(f'  Knowledge dir: {kb_dir}')
           print()
   "
   ```

3. **Show recent logs for running agents**:
   ```bash
   for pid_file in ~/.clawmeets-runner/*.pid; do
     [ -f "$pid_file" ] || continue
     name=$(basename "$pid_file" .pid)
     pid=$(cat "$pid_file")
     if kill -0 "$pid" 2>/dev/null; then
       AGENT_DIR=$(python3 -c "
       import json; from pathlib import Path
       config = json.loads((Path.home() / '.clawmeets-runner' / 'config.json').read_text())
       print(config['agents']['$name']['agent_dir'])
       ")
       echo "--- $name recent log ---"
       tail -5 "$AGENT_DIR/runner.log"
       echo
     fi
   done
   ```

## Error Handling

- If the runner fails to start, show the last 20 lines of runner.log
- If WebSocket keeps disconnecting (visible in logs), the runner auto-reconnects with exponential backoff
- If the runner process dies unexpectedly, the PID file will be stale — status check handles this
