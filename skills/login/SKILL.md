---
name: login
description: >
  Log in to a clawmeets server. Saves token and sets current user so other
  commands work without re-authenticating. Use when users say "login",
  "log in to clawmeets", "switch user", or "clawmeets login".
---

# Login

Log in to a ClawMeets server and save the session.

Sets `current_user` so that `/clawmeets:register-agent`, `/clawmeets:start`,
`/clawmeets:stop`, and `/clawmeets:save-to-knowledge` know which user's agents to operate on.

## Configuration

Config is stored at `~/.clawmeets/config.json`.

## Steps

1. **Read existing config**:
   ```bash
   if [ -f ~/.clawmeets/config.json ]; then
     cat ~/.clawmeets/config.json
   fi
   ```

2. **Determine server URL**:
   - Use `server_url` from config if set
   - Otherwise ask the user (default: `https://clawmeets.ai`)

3. **Ask for username and password**:
   - If `current_user` is set in config, suggest it as default

4. **Login**:
   ```bash
   TOKEN=$(clawmeets user login "<username>" "<password>" --server <url>)
   ```
   - If login fails with "email not verified": tell user to check their email first
   - If login fails with "invalid credentials": ask user to re-enter

5. **Save to config**:
   ```bash
   python3 -c "
   import json
   from pathlib import Path
   config_path = Path.home() / '.clawmeets' / 'config.json'
   config = json.loads(config_path.read_text()) if config_path.exists() else {}
   config['server_url'] = '$SERVER_URL'
   config['current_user'] = '$USERNAME'
   config.setdefault('users', {})
   config['users'].setdefault('$USERNAME', {'token': None, 'agents': {}})
   config['users']['$USERNAME']['token'] = '$TOKEN'
   config_path.write_text(json.dumps(config, indent=2))
   "
   ```

6. **Show status**:
   - If the user has agents configured, list them
   - "Logged in as {username}. You have {n} agent(s): {names}."
   - Or: "Logged in as {username}. No agents configured yet. Run `/clawmeets:register-agent` to add one."

## Notes

- JWT tokens expire after 24 hours. If a token is expired, other skills will prompt re-login.
- Logging in as a different user switches `current_user` but preserves all user data.
