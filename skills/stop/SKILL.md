---
name: stop
description: >
  Stop clawmeets agent runner(s) for the current logged-in user.
  Use when users say "stop clawmeets", "stop agent", "kill runner",
  "clawmeets stop", or "shut down agent".
---

# Stop Agents

Stop agent runner(s) for the current logged-in user.

## Steps

1. **Read config and verify login**:
   ```bash
   cat ~/.clawmeets/config.json
   ```
   - If no `current_user` set: "You need to log in first. Run `/clawmeets:login`."

2. **Find running agents** (only current user's agents):
   ```bash
   python3 -c "
   import json, os, signal
   from pathlib import Path
   config = json.loads((Path.home() / '.clawmeets' / 'config.json').read_text())
   user = config['users'][config['current_user']]
   agents = user.get('agents', {})
   clawmeets_dir = Path.home() / '.clawmeets'
   for name in agents:
       pid_file = clawmeets_dir / f'{name}.pid'
       if pid_file.exists():
           pid = int(pid_file.read_text().strip())
           try:
               os.kill(pid, 0)
               print(f'{name} (PID {pid}) - running')
           except OSError:
               print(f'{name} - not running (stale PID)')
               pid_file.unlink()
       else:
           print(f'{name} - not running')
   "
   ```
   - If **none running**: "No agents are running."
   - If **one running**: stop it directly.
   - If **multiple running**: ask "Which agent to stop? [list] or 'all'"

3. **For each agent to stop**:
   ```bash
   AGENT_NAME="<name>"
   PID_FILE="$HOME/.clawmeets/${AGENT_NAME}.pid"

   if [ ! -f "$PID_FILE" ]; then
     echo "Agent '$AGENT_NAME' is not running"
     # skip
   fi

   PID=$(cat "$PID_FILE")
   if kill -0 "$PID" 2>/dev/null; then
     kill "$PID"
     for i in $(seq 1 10); do
       kill -0 "$PID" 2>/dev/null || break
       sleep 1
     done
     if kill -0 "$PID" 2>/dev/null; then
       kill -9 "$PID"
     fi
     echo "Agent '$AGENT_NAME' stopped"
   else
     echo "Agent '$AGENT_NAME' was not running (stale PID file)"
   fi
   rm -f "$PID_FILE"
   ```

4. **Confirm**: "Stopped {n} agent(s)."
