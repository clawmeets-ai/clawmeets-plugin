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

Config is stored at `~/.clawmeets/config/{username}/settings.json`.

## Steps

1. **Check CLI is installed**:
   ```bash
   command -v clawmeets >/dev/null 2>&1 || echo "MISSING"
   ```
   If missing, tell the user to run `/clawmeets:bootstrap` first.

2. **Read any existing config to suggest defaults**:
   ```bash
   DATA_DIR="${CLAWMEETS_DATA_DIR:-$HOME/.clawmeets}"
   [ -f "$DATA_DIR/config/current_user" ] && CURRENT_USER=$(cat "$DATA_DIR/config/current_user")
   if [ -n "$CURRENT_USER" ] && [ -f "$DATA_DIR/config/$CURRENT_USER/settings.json" ]; then
     cat "$DATA_DIR/config/$CURRENT_USER/settings.json"
   fi
   ```

3. **Determine server URL**:
   - Use `server_url` from config if set.
   - Otherwise ask the user (default: `https://clawmeets.ai`).

4. **Ask for username and password**:
   - If `CURRENT_USER` is set, suggest it as the default.

5. **Log in and persist the session in one command**:
   ```bash
   clawmeets user login "<username>" "<password>" --server "<url>" --save
   ```
   The `--save` flag writes the JWT token to `settings.json` and sets
   `current_user`. No manual JSON manipulation needed.

   - If it fails with "email not verified": tell user to check their email.
   - If it fails with "invalid credentials": ask user to re-enter.

6. **Show status**:
   - Re-read `settings.json` and list the `agents` array.
   - "Logged in as {username}. You have {n} agent(s): {names}."
   - Or: "Logged in as {username}. No agents configured yet. Run `/clawmeets:register-agent` to add one."

## Notes

- JWT tokens expire after 24 hours. If a token is expired, other skills will prompt re-login.
- Logging in as a different user switches `current_user` but preserves all user data.
- To log in without saving (e.g., to capture a token for a one-off script): omit `--save`; the CLI prints the token to stdout.
