# Agent Learning Protocol

A generic protocol for agents to incrementally learn from their interactions. Agents improve their workflows, remember what works, and avoid repeating failures across invocations.

## How It Works

Each agent invocation is a fresh process, but the knowledge directory persists on disk. The agent reads past learnings at the start and writes new learnings at the end.

## Learning Loop

### Phase 1: Check (before starting work)

Read `learnings/INDEX.md` in your knowledge directory. Scan for entries relevant to the current task. If you find relevant learnings:
- Prefer learned selectors/workflows over CLAUDE.md defaults
- Avoid approaches listed in `failures.md`
- If a learning is older than 30 days, verify it still works before relying on it

### Phase 2: Execute (during work)

Work normally. When something fails:
- Note the failure (selector, URL, approach, error message)
- Try an alternative
- If the alternative works, note what succeeded

### Phase 3: Record (after completing work)

If you learned something new, save it. Write learnings using the Write tool to files in your knowledge directory under `learnings/`.

**When to record:**
- A selector or locator you discovered that works better than the default
- A workflow that required extra steps not in your CLAUDE.md recipes
- A failure that should be avoided in the future
- An extraction pattern that produces cleaner results

**When NOT to record:**
- One-off transient errors (network timeout, temporary server error)
- User-specific preferences (these belong in the project, not agent knowledge)
- Information already in your static knowledge (site_profile.json, CLAUDE.md)
- Trivial observations that won't help future invocations

### Phase 4: Consolidate (when learnings grow large)

When `INDEX.md` exceeds 50 entries or a category file exceeds 200 lines:
- Merge duplicate insights (keep the most recent version)
- Remove entries contradicted by newer learnings
- Prune entries older than 60 days that haven't been referenced
- Rewrite consolidated entries more concisely

## File Structure

```
{knowledge_dir}/learnings/
├── INDEX.md        ← one-line summaries, max 50 entries
├── workflows.md    ← refined step-by-step recipes
├── selectors.md    ← working selectors/locators (navigator agents)
└── failures.md     ← what didn't work and why
```

### INDEX.md Format

One line per entry. Most recent first. Max 50 lines.

```markdown
# Learnings Index

- [2026-04-10] selectors: Redfin search results use `.HomeViews` not `.HomeCardContainer` since March 2026
- [2026-04-09] workflow: Austin market page requires scrolling to load trend charts before extracting
- [2026-04-08] failure: `.MarketSummary` selector returns empty on city pages, use `[data-rf-test-id="market-summary"]` instead
```

### Category File Format (workflows.md, selectors.md, failures.md)

Each entry is a block with date, context, and takeaway.

```markdown
## [2026-04-10] Redfin search results selector changed

**Context**: Searching for homes in Austin, TX
**Default**: `.HomeCardContainer` (from CLAUDE.md)
**Actual**: `.HomeViews .HomeCardContainer` -- the outer wrapper changed
**Takeaway**: Use `.HomeViews .HomeCardContainer` or fall back to `[data-rf-test-id="home-card"]`

---
```

## Rules

1. **Be concise** -- each INDEX entry is one line; each category entry fits in 5-8 lines
2. **Be specific** -- include the exact selector, URL, or command that works
3. **Date everything** -- use ISO date format (YYYY-MM-DD)
4. **Prefer updates over appends** -- if a learning supersedes an older one, replace it
5. **Don't duplicate static knowledge** -- if your CLAUDE.md already says it, don't repeat it in learnings
6. **Learnings are hypotheses** -- they worked at one point but may become stale. Always verify old entries when relying on them.
