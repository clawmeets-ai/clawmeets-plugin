---
name: logout
description: >
  Log out of clawmeets. Clears the current user session but keeps all user
  data and agent configurations. Use when users say "logout", "log out",
  "clawmeets logout", or "switch account".
---

# Logout

Log out of the current ClawMeets session.

Clears `current_user` but keeps all user data and agent configurations intact.
To switch users, logout then run `/clawmeets:login`.

## Steps

1. **Read config**:
   ```bash
   cat ~/.clawmeets/config.json
   ```
   - If no config or no `current_user` set: "You are not logged in."

2. **Clear current_user**:
   ```bash
   python3 -c "
   import json
   from pathlib import Path
   config_path = Path.home() / '.clawmeets' / 'config.json'
   config = json.loads(config_path.read_text())
   config['current_user'] = None
   config_path.write_text(json.dumps(config, indent=2))
   "
   ```

3. **Confirm**: "Logged out. Run `/clawmeets:login` to log in again or switch to a different user."
