---
name: save-to-knowledge
description: >
  Save files or text to a clawmeets agent's knowledge base directory. Can save
  chatroom files from projects, local files, or text content. Use when users say
  "save to knowledge", "add to knowledge base", "save file to kb",
  "save to agent knowledge", or "add to agent kb".
---

# Save to Knowledge Base

Save a file or text content to a clawmeets agent's knowledge base directory.
The agent will have access to saved files in all future work sessions.

Supports saving:
- **Chatroom files** from agent projects
- **Local files** from disk
- **Text content** typed or pasted by the user

## Steps

1. **Check config and verify login**:
   ```bash
   DATA_DIR="${CLAWMEETS_DATA_DIR:-$HOME/.clawmeets}"
   CURRENT_USER=$(cat "$DATA_DIR/config/current_user" 2>/dev/null)
   cat "$DATA_DIR/config/$CURRENT_USER/settings.json" 2>/dev/null
   ```
   - If no current_user or no `user.token` set: "You need to log in first. Run `/clawmeets:login`."

2. **Determine which agent**:
   ```bash
   python3 -c "
   import json, os; from pathlib import Path
   data_dir = Path(os.environ.get('CLAWMEETS_DATA_DIR', os.path.expanduser('~/.clawmeets')))
   user = (data_dir / 'config' / 'current_user').read_text().strip()
   config = json.loads((data_dir / 'config' / user / 'settings.json').read_text())
   username = config['user']['username']
   for a in config.get('agents', []):
       kb = a.get('knowledge_dir') or 'not set'
       print(f\"{username}-{a['name']} (knowledge: {kb})\")
   "
   ```
   - If **one agent**: use it.
   - If **multiple**: ask which agent to save knowledge to.

3. **Verify knowledge_dir**:
   - If the selected agent has no `knowledge_dir` set (null):
     - Ask the user for the knowledge directory path
     - Create the directory if needed: `mkdir -p "$KB_DIR"`
     - Update the user's settings.json with the new path (under the agent's entry in `agents[]`)
     - Set up CLAUDE.md in the knowledge dir if it doesn't exist

4. **Determine what to save**:
   - If the user specified a file path in their request, use that file directly
   - Otherwise ask: "What would you like to save?"
     - **"A file from a chatroom"** → go to step 5a
     - **"A local file"** → ask for the file path, go to step 6
     - **"Text content"** → go to step 5b

5a. **Browse chatroom files**:
   ```bash
   # Derive agent_dir from filesystem
   DATA_DIR="${CLAWMEETS_DATA_DIR:-$HOME/.clawmeets}"
   AGENT_DIR=$(ls -d "$DATA_DIR/agents/${AGENT_NAME}-"* 2>/dev/null | head -1)

   # List projects
   echo "Available projects:"
   ls "$AGENT_DIR/projects/" 2>/dev/null || echo "(no projects)"

   # After user picks a project:
   echo "Available chatrooms:"
   ls "$AGENT_DIR/projects/<project>/chatrooms/" 2>/dev/null

   # After user picks a chatroom:
   echo "Available files:"
   ls "$AGENT_DIR/projects/<project>/chatrooms/<chatroom>/files/" 2>/dev/null
   ```
   - Let the user select file(s) to save.
   - Source path: `{agent_dir}/projects/{project}/chatrooms/{chatroom}/files/{filename}`

5b. **Save text content**:
   - Ask for a filename (e.g., `meeting-notes.md`)
   - Ask for the content (user types or pastes it)
   - Write directly to `{knowledge_dir}/{filename}`
   - Go to step 7.

6. **Copy file to knowledge dir**:
   ```bash
   cp "$SOURCE_FILE" "$KB_DIR/"
   # Or if user wants a different name:
   cp "$SOURCE_FILE" "$KB_DIR/$TARGET_NAME"
   ```

7. **Confirm**:
   ```bash
   echo "Saved: $KB_DIR/$FILENAME"
   ls -la "$KB_DIR/$FILENAME"
   ```
   Tell the user: "File saved to knowledge base. The agent will have access to this
   file in all future work sessions."

## Error Handling

- If knowledge_dir doesn't exist when saving, offer to create it
- If the source file doesn't exist, ask the user to verify the path
- If settings.json doesn't exist or no user logged in, direct user to run `/clawmeets:login` first
