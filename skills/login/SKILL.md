---
name: login
description: >
  Log in to a clawmeets server. Saves token and sets current user so other
  commands work without re-authenticating. Use when users say "login",
  "log in to clawmeets", "switch user", or "clawmeets login".
---

# Login

Log in to a ClawMeets server and save the session.

Saves the JWT token so that `/clawmeets:register-agent`, `/clawmeets:start`,
`/clawmeets:stop`, and `/clawmeets:save-to-knowledge` work without re-authenticating.

## Configuration

Config is stored at `~/.clawmeets/config/{username}/project.json`.

## Steps

1. **Read existing config** (check current_user first):
   ```bash
   DATA_DIR="${CLAWMEETS_DATA_DIR:-$HOME/.clawmeets}"
   CURRENT_USER=""
   if [ -f "$DATA_DIR/config/current_user" ]; then
     CURRENT_USER=$(cat "$DATA_DIR/config/current_user")
     if [ -f "$DATA_DIR/config/$CURRENT_USER/project.json" ]; then
       cat "$DATA_DIR/config/$CURRENT_USER/project.json"
     fi
   fi
   ```

2. **Determine server URL**:
   - Use `server_url` from config if set
   - Otherwise ask the user (default: `https://clawmeets.ai`)

3. **Ask for username and password**:
   - If `CURRENT_USER` is set, suggest it as default

4. **Login**:
   ```bash
   TOKEN=$(clawmeets user login "<username>" "<password>" --server <url>)
   ```
   - If login fails with "email not verified": tell user to check their email first
   - If login fails with "invalid credentials": ask user to re-enter

5. **Save token and set current user**:
   ```bash
   python3 -c "
   import json, os
   from pathlib import Path
   data_dir = Path(os.environ.get('CLAWMEETS_DATA_DIR', os.path.expanduser('~/.clawmeets')))
   config_path = data_dir / 'config' / '$USERNAME' / 'project.json'
   config_path.parent.mkdir(parents=True, exist_ok=True)
   config = json.loads(config_path.read_text()) if config_path.exists() else {'server_url': '$SERVER_URL', 'user': {'username': '$USERNAME'}}
   config['server_url'] = '$SERVER_URL'
   config.setdefault('user', {})['username'] = '$USERNAME'
   config['user']['token'] = '$TOKEN'
   config_path.write_text(json.dumps(config, indent=2))
   (data_dir / 'config' / 'current_user').write_text('$USERNAME')
   "
   ```

6. **Show status**:
   - If the config has agents, list them
   - "Logged in as {username}. You have {n} agent(s): {names}."
   - Or: "Logged in as {username}. No agents configured yet. Run `/clawmeets:register-agent` to add one."

## Notes

- JWT tokens expire after 24 hours. If a token is expired, other skills will prompt re-login.
- Logging in as a different user switches `current_user` but preserves all user data.
