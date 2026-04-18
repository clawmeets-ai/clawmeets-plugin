---
name: learn
description: >
  Review, consolidate, search, or reset an agent's accumulated learnings.
  Use when users say "show learnings", "what has the agent learned",
  "consolidate learnings", "reset learnings", "search learnings for X",
  or "clean up agent knowledge".
---

# Manage Agent Learnings

Review and maintain the learnings that agents accumulate over time.

Agents save learnings to `{knowledge_dir}/learnings/` as they work. Over time this
grows and may need consolidation, review, or cleanup.

## Steps

1. **Determine agent and knowledge dir**:
   ```bash
   python3 -c "
   import json, os; from pathlib import Path
   data_dir = Path(os.environ.get('CLAWMEETS_DATA_DIR', os.path.expanduser('~/.clawmeets')))
   user = (data_dir / 'config' / 'current_user').read_text().strip()
   config = json.loads((data_dir / 'config' / user / 'settings.json').read_text())
   username = config['user']['username']
   for a in config.get('agents', []):
       kb = a.get('knowledge_dir') or 'not set'
       print(f\"{username}-{a['name']}: {kb}\")
   "
   ```
   - If one agent: use it. If multiple: ask which agent.
   - Set `$KB_DIR` to the agent's knowledge directory.

2. **Determine action** from the user's request:

### Review
Show the agent's learning summary.

```bash
echo "=== Learning Index ==="
cat "$KB_DIR/learnings/INDEX.md" 2>/dev/null || echo "(no learnings yet)"
echo ""
echo "=== Files ==="
ls -la "$KB_DIR/learnings/" 2>/dev/null || echo "(learnings directory does not exist)"
echo ""
echo "=== Stats ==="
for f in "$KB_DIR/learnings/"*.md; do
  [ -f "$f" ] && echo "$(basename "$f"): $(wc -l < "$f") lines"
done
```

Present a summary: number of entries, categories, oldest/newest entry dates.

### Search
Find learnings relevant to a specific topic.

```bash
TOPIC="<user's search term>"
grep -i -n "$TOPIC" "$KB_DIR/learnings/"*.md 2>/dev/null || echo "No learnings found for '$TOPIC'"
```

Show matching entries with their context.

### Consolidate
Merge duplicates, prune stale entries, enforce size limits.

1. Read all files in `$KB_DIR/learnings/`
2. Apply these rules:
   - Merge entries about the same selector/workflow (keep most recent)
   - Remove entries contradicted by newer ones
   - Prune entries older than 60 days that haven't proven useful
   - Cap INDEX.md at 50 entries (remove oldest)
   - Cap category files at 200 lines (summarize and merge)
3. Write the consolidated files back
4. Report what was changed: "Consolidated X entries into Y. Removed Z stale entries."

### Reset
Clear all learnings and start fresh.

```bash
# Confirm with user first!
rm -rf "$KB_DIR/learnings/"
mkdir -p "$KB_DIR/learnings"
echo "Learnings cleared. The agent will start learning fresh from next invocation."
```

**Always confirm with the user before resetting.** This deletes accumulated knowledge.

## Error Handling

- If `learnings/` directory doesn't exist: "This agent has no learnings yet. Learnings accumulate automatically as the agent works."
- If knowledge_dir is not set: "This agent has no knowledge directory configured."
