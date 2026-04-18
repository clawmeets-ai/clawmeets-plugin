---
name: logout
description: >
  Log out of clawmeets. Clears the current user session but keeps all user
  data and agent configurations. Use when users say "logout", "log out",
  "clawmeets logout", or "switch account".
---

# Logout

Log out of the current ClawMeets session.

Clears the JWT token but keeps all user data and agent configurations intact.
To switch users, logout then run `/clawmeets:login`.

## Steps

1. **Read config**:
   ```bash
   DATA_DIR="${CLAWMEETS_DATA_DIR:-$HOME/.clawmeets}"
   if [ -f "$DATA_DIR/config/current_user" ]; then
     CURRENT_USER=$(cat "$DATA_DIR/config/current_user")
     cat "$DATA_DIR/config/$CURRENT_USER/project.json"
   fi
   ```
   - If no current_user or no `user.token` set: "You are not logged in."

2. **Clear token**:
   ```bash
   python3 -c "
   import json, os
   from pathlib import Path
   data_dir = Path(os.environ.get('CLAWMEETS_DATA_DIR', os.path.expanduser('~/.clawmeets')))
   user = (data_dir / 'config' / 'current_user').read_text().strip()
   config_path = data_dir / 'config' / user / 'project.json'
   config = json.loads(config_path.read_text())
   config.get('user', {}).pop('token', None)
   config_path.write_text(json.dumps(config, indent=2))
   "
   ```

3. **Confirm**: "Logged out. Run `/clawmeets:login` to log in again."
