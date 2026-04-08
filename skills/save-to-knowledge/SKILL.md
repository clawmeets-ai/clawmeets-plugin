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

1. **Check config**: Read `~/.clawmeets/config.json`.
   - If it doesn't exist, tell the user to run setup first (invoke `/clawmeets:setup`).

2. **Determine which agent**:
   ```bash
   python3 -c "
   import json; from pathlib import Path
   config = json.loads((Path.home() / '.clawmeets' / 'config.json').read_text())
   agents = config.get('agents', {})
   for name, info in agents.items():
       kb = info.get('knowledge_dir') or 'not set'
       print(f'{name} (knowledge: {kb})')
   "
   ```
   - If **one agent**: use it.
   - If **multiple**: ask which agent.

3. **Verify knowledge_dir**:
   - If the selected agent has no `knowledge_dir` set (null):
     - Ask the user for the knowledge directory path
     - Create the directory if needed: `mkdir -p "$KB_DIR"`
     - Update `~/.clawmeets/config.json` with the new path
     - Set up CLAUDE.md in the knowledge dir if it doesn't exist (see setup skill for template)

4. **Determine what to save**:
   - If the user specified a file path in their request, use that file directly
   - Otherwise ask: "What would you like to save?"
     - **"A file from a chatroom"** → go to step 5a
     - **"A local file"** → ask for the file path, go to step 6
     - **"Text content"** → go to step 5b

5a. **Browse chatroom files**:
   ```bash
   AGENT_DIR="<agent_dir>"

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
- If config.json doesn't exist, direct user to run `/clawmeets:setup` first
