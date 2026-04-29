---
name: reflect
description: >
  Maintain durable agent memory + your private skill hub. The
  reflect-trigger DM kicks off three modes in one cycle: Reflect (distill
  recent activity into learnings), Promote (codify a recurring procedure
  as a `/personal:<name>` skill), and Correct (patch a personal skill
  that misfired). The lint-trigger DM runs Lint (audit existing memory
  for contradictions, stale claims, orphans, missing cross-refs). The
  bootstrap-trigger DM runs Bootstrap (one-time first-fill of USER.md
  for the assistant or learnings/ for a worker, sourced from an inlined
  dump produced by `clawmeets bootstrap`). Invoked when you receive a
  DM message tagged with one of `<!-- clawmeets:reflect-trigger -->`,
  `<!-- clawmeets:lint-trigger -->`, or `<!-- clawmeets:bootstrap-trigger -->`.
---

# Reflect

You receive scheduled trigger messages in your DM. Each carries an
HTML-comment marker that tells you which trigger fired:

| Marker in message body                          | Modes to run                |
|-------------------------------------------------|-----------------------------|
| `<!-- clawmeets:reflect-trigger -->`            | Reflect, Promote, Correct   |
| `<!-- clawmeets:lint-trigger -->`               | Lint                        |
| `<!-- clawmeets:bootstrap-trigger -->`          | Bootstrap (first-fill)      |

The reflect-trigger fires all three of Reflect, Promote, and Correct in
one cycle — they share the same inlined transcript and the same
`learnings/log.md` cursor. Run only when one of these markers is
present. Do **not** write memory or author personal skills during normal
turns — chat history preserves anything worth keeping until the next
reflection cycle.

## Memory layout

Your `knowledge_dir` holds your durable memory:

```
USER.md                  # ONLY if you are the user's personal assistant
learnings/
  INDEX.md               # one-line lessons + links to topic pages
  log.md                 # append-only "## [YYYY-MM-DD] event | title" entries
  <topic>.md             # drill-down pages, cross-linked from INDEX.md
```

You also have a personal skill hub at the **agent root** (one level up
from `knowledge_dir`):

```
personal-skill-hub/
  skills/
    INDEX.md             # one line per skill: "<name> — when to invoke"
    <name>/
      SKILL.md           # frontmatter (name, description) + procedure body
```

Each `<name>/SKILL.md` is auto-registered as a `/personal:<name>`
slash-command on your next invocation — no sync, no server round-trip.
Personal skills are agent-private and never leave your runner.

## Sources of truth

Your distillation source depends on the mode:

- **Reflect / Promote / Correct modes**: the inlined `== Recent activity ==
  (last N messages) ==` transcript is your canonical source. You may
  *peek* at `shared-context/PLAN.md` (or other project files quoted in the
  transcript) when you need context to understand what was actually said
  in chat — that's fine. What you must **not** do is promote PLAN.md's
  "Learnings" section verbatim into your durable `knowledge_dir/learnings/`.
  Those two layers are deliberately separate.
- **Lint mode**: your own `learnings/` files (and `USER.md` if assistant)
  are the source. You don't need to read project files for lint —
  lint operates on the wiki, not on the project's shared context.
- **Bootstrap mode**: the inlined dump in the trigger DM is your
  *only* source. The orchestrator (`clawmeets bootstrap`) already ran
  Gmail/Calendar (Phase 1) or web research (Phase 2) — do **not**
  re-run those tools yourself. Re-running burns budget and produces
  drift between the dump and what you write.

### Why the two layers are separate

PLAN.md "Learnings" is **project-scoped** — the coordinator's in-project
pivoting log. It lives in `shared-context`, dies with the project, and is
deliberately framed in project-specific terms (acceptance criteria, milestone
numbers). Mirroring it into `knowledge_dir/learnings/` would couple your
durable memory to per-project framing and create drift between two stores
that mean different things.

Lessons that *genuinely* matter cross-project will surface in chat (because
someone said them out loud) and you'll pick them up from the transcript on
their merits — not because the coordinator filed them under PLAN.md
"Learnings" for in-project pivoting reasons.

## Role: are you the user's personal assistant?

The user's personal assistant is the agent named `{username}-assistant`.
If your own agent name matches that pattern, you are the assistant.
Check by looking at your name in the `== AGENT ID ==` block of your
prompt and comparing against `{username}-assistant`.

- **If you are the assistant**: maintain BOTH `USER.md` and `learnings/`.
- **If you are a worker**: maintain ONLY `learnings/`. Do not create or
  write `USER.md`. User-identity facts (general preferences, personal
  info) belong with the user's assistant.

## Write mechanics (all modes)

Use your native `Edit` / `Write` tools on `knowledge_dir/...` and
`personal-skill-hub/...` paths. Do **not** use the ClawMeets `update_file`
action — that broadcasts to the chatroom and would leak memory writes
(and personal-skill writes) as visible file events. Memory and personal
skills must stay invisible to the chat surface; only your reply (a
normal `reply` action) is chat-visible.

## Hot-cache discipline

- `INDEX.md` ≤ 6 KB.
- `USER.md` ≤ 4 KB (assistant only).
- One line per entry in `INDEX.md` ideally. When an entry grows past
  ~5 lines or starts cross-referencing other entries, **promote** it to
  its own `learnings/<topic>.md` and shrink the INDEX entry to a
  one-liner with a relative link.

---

## Reflect mode

The trigger message contains a `== Recent activity for <you> (since <iso>) ==`
block. Treat that as the **canonical** source for this cycle — do not
re-fetch chat history.

1. **Read** the existing `learnings/INDEX.md`, `learnings/log.md`, and
   (assistant only) `USER.md`.
2. **Extract lessons** from the recent activity:
   - User preferences, tone, pet peeves → `USER.md` (assistant only).
   - Domain facts, working approaches, failed approaches → `learnings/INDEX.md`,
     promoting to topic pages when entries grow.
3. **Update files** using Edit/Write:
   - Full-file overwrite for `INDEX.md` and `USER.md`.
   - Append-only for `log.md`: add a single
     `## [YYYY-MM-DD] reflect | <one-line summary>` entry.
4. **Reply in the DM** with a 3-bullet summary of what changed. Plain
   prose, no markdown headers — the user reads this on their phone.

### Idempotency (reflect)

If today's `log.md` already has a `## [YYYY-MM-DD] reflect` entry,
**skip** all three reflect-trigger modes (Reflect, Promote, Correct) and
reply with a single line: "Already reflected for today." A single `##`
entry per day covers the whole cycle — Promote and Correct are logged as
bullets *under* that day's `reflect` heading, not as separate `## [date]
promote` lines.

---

## Promote mode (runs in the same cycle as Reflect)

After Reflect finishes (or in the same pass), look at the **whole**
inlined transcript — not just the new portion since your last reflection
— and decide whether to codify a recurring procedure as a
`/personal:<name>` skill.

### When to Promote

Use your judgment. Good Promote candidates have **at least one** of:

- **Recurring procedure**: the same multi-step workflow appears across
  several conversations or projects in the transcript. Three-ish hits is
  a useful floor; one is too few; ten is well past time.
- **Multi-step with prereqs and checks**: the procedure has setup steps,
  ordered actions, and verifiable success conditions — i.e. it's an
  actual *procedure*, not a single tip. Single-tip lessons belong in
  `learnings/`, not the personal-skill hub.
- **Explicit user request**: the user said "remember how to do X" or
  "save this as a skill". Always honor — even for one-shot procedures.

**Bad** Promote candidates (don't):

- A one-off task with no obvious re-use ("plan my Tuesday").
- A simple tip or fact (lives in `learnings/INDEX.md`).
- Something that overlaps an existing personal skill or a system skill
  (e.g. `/clawmeets:reflect`) — patch the existing one instead.

### How to Promote

1. **Pick a name**: lowercase, hyphens or dots only, ≤ 40 chars,
   describes the procedure (e.g. `weekly-replan`,
   `competitor-doc-refresh`, `inbox-triage`).
2. **Check for collisions**: list `personal-skill-hub/skills/` — if a
   skill with that name already exists, switch to the Correct flow
   below (patch it) rather than overwriting.
3. **Write `personal-skill-hub/skills/<name>/SKILL.md`** with this shape:
   ```markdown
   ---
   name: <name>
   description: <one-line summary; agent reads this when deciding to invoke>
   ---

   # <Procedure title>

   ## When to use this
   <2-3 sentences. Concrete signals — what does the task look like?>

   ## Prerequisites
   - <inputs / context the procedure assumes>

   ## Steps
   1. <ordered, imperative>
   2. ...

   ## Success checks
   - <how you know it worked>

   ## Pitfalls
   - <gotchas you discovered while doing this>
   ```
   Use Edit/Write — **never** `update_file`.
4. **Update `personal-skill-hub/skills/INDEX.md`** with one new line:
   `- <name> — <when to invoke; one short clause>`. Sort alphabetically.
   Create the file if it doesn't exist yet.
5. **Log under today's `learnings/log.md` reflect entry**, as a bullet:
   `- promoted: /personal:<name>`. Don't create a separate
   `## [YYYY-MM-DD] promote` heading.

### Idempotency (promote)

The "today's log already has a reflect entry → skip" check at the top of
the cycle covers Promote too. Within a single cycle, if you Promote and
the same skill name was already promoted today (visible as a `promoted:
/personal:<name>` bullet under today's entry), don't write the SKILL.md
twice — that's a sign you missed the dedup check.

---

## Correct mode (runs in the same cycle as Reflect)

Scan the inlined transcript for `/personal:<name>` invocations that
**misfired**: produced an error, got user pushback ("that's not what I
meant", "skip step X"), or led you to deviate from the documented steps.

### When to Correct

Trigger a patch when **any** of:

- The user explicitly told you a personal skill was wrong or out of date.
- A `/personal:<name>` invocation produced an error and you had to work
  around its instructions.
- You deviated from the SKILL.md steps because the world changed (a tool
  was renamed, a URL moved, a precondition no longer holds) and your
  workaround succeeded.

If a personal skill worked exactly as written, **don't touch it** — only
patch on observed failure.

### How to Correct

1. **Read** `personal-skill-hub/skills/<name>/SKILL.md`.
2. **Patch** with `Edit` — keep the change minimal. Targeted edits to a
   single step or pitfall are better than rewriting the whole skill.
   - If a step was wrong: edit the step in place.
   - If a pitfall was missing: add a bullet under "Pitfalls".
   - If the skill is broken beyond a small patch: rewrite it with `Write`.
3. **Log under today's `learnings/log.md` reflect entry**, as a bullet:
   `- patched: /personal:<name> — <one-line reason>`.

### Idempotency (correct)

Same day-level guard as Reflect — if today's log already has a `reflect`
entry and a `patched: /personal:<name>` bullet for this skill, skip.

---

## Lint mode

Lint operates on your existing wiki, not on chat history. There is no
inlined transcript — read your own `learnings/` files and audit them.

1. **Read** every file under `learnings/` (`INDEX.md`, `log.md`, every
   `<topic>.md`) and (assistant only) `USER.md`.
2. **Audit** for:
   - **Contradictions** between pages — find pairs of statements that
     disagree. Resolve by date when one is clearly newer (newer wins);
     **escalate** in the DM reply when the resolution isn't obvious.
   - **Stale claims** — entries referencing files, projects, agents, or
     APIs that no longer exist in the current chat history. Mark stale
     or remove.
   - **Orphan pages** — `learnings/<topic>.md` files with no inbound
     link from `INDEX.md` or other topic pages. Either link them in or
     fold them into a related topic.
   - **Missing cross-references** — important entities mentioned in
     INDEX without their own topic page; promote when the entry has
     grown past one line.
   - **INDEX hygiene** — entries that have grown to more than ~5 lines.
     Promote to a topic page; shrink the INDEX entry to a one-liner
     plus relative link.
3. **Fix** what's clearly safe (broken links, obvious bloat,
   one-newer-wins contradictions). **Escalate** what needs the user's
   call (semantic contradictions, ambiguous staleness) by surfacing it
   in your DM reply rather than silently changing it.
4. **Append** to `log.md`:
   `## [YYYY-MM-DD] lint | <N> changes / <M> escalations`.
5. **Reply in the DM** with a 3-bullet summary: what changed, what was
   escalated for the user's call, and what to confirm.

### Idempotency (lint)

If today's `log.md` already has a `## [YYYY-MM-DD] lint` entry,
**skip** writing files and reply with a single line: "Already linted
today."

---

## Bootstrap mode

A one-time first-fill triggered by `clawmeets bootstrap` after a fresh
install, so you start out with something other than empty files. The
orchestrator does the heavy lifting (gathering signal from Gmail +
Calendar in Phase 1, doing web research in Phase 2) and hands you the
result inline. Your job is *structuring*, not *gathering*.

### What you write (predicate-dispatched)

Same predicate as elsewhere — `name.endswith("-assistant")` decides:

- **Assistant** (`{username}-assistant`): write `USER.md` only. Do not
  touch `learnings/` from this trigger; ongoing reflection cycles will
  fill that in once chat activity gives you something worth recording.
- **Worker** (everyone else): write `learnings/INDEX.md` + 3–6 topic
  pages. Do not write `USER.md` — that belongs to the assistant.

If you receive a bootstrap-trigger but the predicate doesn't match what
the dump expects (e.g. a worker gets a trigger whose dump contains a
USER PROFILE block but no research dump), reply with one line saying
which trigger you'd expect and stop. The orchestrator routes by agent
name, so this should be rare.

### Hard rule: inlined dump is the only source

The trigger DM body, after the marker, contains everything you need. Do
**not**:

- Call Gmail / Calendar / WebFetch / WebSearch tools yourself.
- Read your own (empty) `learnings/` and try to re-derive what's there.
- Consult chat history.

The orchestrator already did all of that. Re-running burns budget and
introduces non-determinism between what was sent and what you write.

### First-run shape (workers only)

A bootstrap is the *only* time the agent goes from empty `learnings/` to
a multi-page bundle in one shot. Aim for:

- **3–6 topic pages**, each one a self-contained reference page (200–800
  words) on a distinct thing the agent will be asked to do. For a
  `career_coach`: JD decoding, resume tailoring, STAR stories,
  negotiation. For `finance` agents: budget framework, tax basics for
  the user's geography, investment one-pager, etc. Drop topics that
  the dump doesn't cover well — better fewer good pages than padded ones.
- **`learnings/INDEX.md` ≤ 6 KB**, one line per topic with a relative
  link. Optionally a short opening paragraph naming you and what your
  knowledge covers.
- **Lead each topic page** with a one-sentence "what this is for" line.
- **Cross-link liberally**: INDEX → topic, topic → topic.
- **Cite sources** inline (`[source: <url>]`) when the dump cited them
  — don't invent citations.

### Steps (assistant — Bootstrap to USER.md)

1. Read the inlined `== USER PROFILE DUMP ==` block from the trigger DM.
2. Distill into `USER.md` (≤ 4 KB) — concise prose, bullets fine.
   Cover: role + industry, geography, recurring contacts (who/what they
   do), current priorities, voice/tone, any "do not" preferences.
3. Append `## [YYYY-MM-DD] bootstrap | initial profile (rich|degraded)`
   to `learnings/log.md` (note "rich" if the dump came from Gmail+Cal,
   "degraded" if from the user-prompt fallback — the orchestrator
   labels the dump so you can tell).
4. Reply in the DM with a 3-bullet summary of what you captured. Plain
   prose. **Do not** quote raw email/event content in the reply.

### Steps (worker — Bootstrap to learnings/)

1. Read the inlined `== USER PROFILE (read-only context) ==` and
   `== DEEP-RESEARCH DUMP ==` blocks from the trigger DM.
2. Identify topic boundaries (3–6 things, distinct from each other,
   each something the agent will actually do). Decorate each with the
   user-profile signal — e.g. `career_coach` for a Bay Area senior IC
   biases comp data toward Bay Area senior bands, not generic.
3. Write each topic page (Edit/Write, NOT `update_file`). Lead with the
   one-line purpose; 2–6 sub-headings; concrete tactics > generic essays.
4. Compose `INDEX.md` with one line per topic + relative link.
5. Append `## [YYYY-MM-DD] bootstrap | initial domain knowledge`
   to `learnings/log.md`.
6. Reply in the DM with a 3-bullet summary: which topics you created,
   anything from the dump you intentionally dropped, anything the user
   should know to expect.

### Idempotency (bootstrap)

- **Assistant**: if `USER.md` already exists, **skip** the write and
  reply with a single line: "Already bootstrapped — re-run with
  `clawmeets bootstrap --force` to redo." Don't append to log.md.
- **Worker**: if `learnings/INDEX.md` already exists, same skip + reply.

`--force` on the orchestrator side just re-triggers — it doesn't delete
files. The skill is what gates the actual overwrite. To redo from
scratch, the user should `rm USER.md` (or `rm -rf learnings/`) before
re-running.

---

## Examples

`learnings/INDEX.md` (kept lean):

```markdown
# Learnings

- [migrations] Don't reorder migrations on Postgres 14 — see [postgres-migrations.md](./postgres-migrations.md)
- [voice] Brand voice is dry/technical, no exclamation marks
- [tooling] Use `uv` for Python deps in this repo, not `pip`
```

`learnings/postgres-migrations.md` (drill-down page):

```markdown
# Postgres migrations

## Don't reorder migrations on Postgres 14
**Context**: 2026-04-15 incident on the data-pipeline project.
**Default**: Migrations applied in alphabetical order.
**Failure**: Reordering broke FK constraints in production rollout.
**Takeaway**: Append-only — never rename or reorder existing migrations.
```

`learnings/log.md` (append-only, all cycles share one entry per day):

```markdown
# Reflection log

## [2026-04-25] reflect | learned brand voice + promoted weekly-replan
- promoted: /personal:weekly-replan
- patched: /personal:competitor-doc-refresh — Crunchbase URL moved
## [2026-04-24] reflect | first cycle — captured user's terse-status preference
## [2026-04-22] lint | 3 changes / 1 escalation
```

`personal-skill-hub/skills/INDEX.md`:

```markdown
# Personal skills

- competitor-doc-refresh — pull latest deck, diff against last quarter
- inbox-triage — when inbox > 50, sort sender → priority → deadline
- weekly-replan — reshuffle calendar when Monday's plan slips
```

`USER.md` (assistant only — concise):

```markdown
# User

- Cheng-Tao, founder of ClawMeets.
- Prefers terse status updates; no exclamation marks.
- Building agent self-improvement architecture (this conversation, 2026-04).
- Voice for marketing copy: dry, technical, no emoji.
```

## DM reply templates

**Reflect mode** (covers Reflect + Promote + Correct):

```
Reflected on the last 100 messages. Three things changed:
- Added "don't reorder Postgres 14 migrations" to learnings/INDEX.md (promoted to its own page).
- Codified weekly-replan as /personal:weekly-replan — invoke when Monday's plan slips.
- Patched /personal:competitor-doc-refresh: Crunchbase URL moved, fixed step 3.
```

**Lint mode**:

```
Linted my learnings/. Three things to flag:
- Removed a stale claim about the deleted `legacy_pipeline.py`.
- Promoted the bloated "auth" entry into auth.md and tightened the INDEX line.
- Found a contradiction between v2 and v3 of the deploy approach — both pages claim to be canonical. Which one should I keep?
```

That's it. Short, scannable, correctable.
