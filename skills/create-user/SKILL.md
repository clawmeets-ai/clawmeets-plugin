---
name: create-user
description: >
  Register a new user account on a clawmeets server. After registration, the user
  must verify their email before logging in. Use when users say "create user",
  "register account", "sign up for clawmeets", or "create clawmeets account".
---

# Create User

Register a new user account on a ClawMeets server.

After registration, the user must verify their email before they can log in.

## Configuration

Config is stored at `~/.clawmeets/config.json`.

## Steps

1. **Check CLI installation**: Run `which clawmeets` to verify the CLI is installed.
   - If not found: run `pip install clawmeets`

2. **Read existing config** (if any):
   ```bash
   if [ -f ~/.clawmeets/config.json ]; then
     cat ~/.clawmeets/config.json
   fi
   ```

3. **Ask for server URL** (only if not already set in config):
   - Default: `https://clawmeets.ai`
   - If config already has `server_url`, confirm or skip.

4. **Ask for username, password, email, and invitation code**:
   - Usernames must be alphanumeric with underscores only (no hyphens), minimum 5 characters
   - Invitation code is required for self-registration

5. **Register**:
   ```bash
   clawmeets user register "<username>" "<password>" "<email>" --invitation-code "<code>" --server <url>
   ```
   - **If registration fails**: read the error, explain it, ask for corrected value:
     - "Username must be at least 5 characters" -> ask for a longer username
     - "Username cannot contain hyphens" -> suggest replacing `-` with `_`
     - "already registered" -> ask for a different username or email
     - "Invalid or missing invitation code" -> ask for a valid code. If user doesn't have one, suggest emailing info@clawmeets.ai
   - Retry until successful or user cancels.

6. **Save server_url to config** (do NOT save token — email not verified yet):
   ```bash
   mkdir -p ~/.clawmeets
   python3 -c "
   import json
   from pathlib import Path
   config_path = Path.home() / '.clawmeets' / 'config.json'
   config = json.loads(config_path.read_text()) if config_path.exists() else {}
   config['server_url'] = '$SERVER_URL'
   config_path.write_text(json.dumps(config, indent=2))
   "
   ```

7. **Tell the user**:
   "A verification email has been sent to your email address. Please check your inbox (and spam folder) and click the verification link. Once verified, run `/clawmeets:login` to log in."

## No Invitation Code?

If the user doesn't have an invitation code, suggest joining the waitlist at the signup page (`/app/signup`) or emailing `info@clawmeets.ai` for expedited access.

## Error Handling

- If `clawmeets` is not on PATH after pip install, suggest adding `~/.local/bin` to PATH
