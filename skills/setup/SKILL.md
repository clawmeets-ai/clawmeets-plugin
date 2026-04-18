---
name: setup
description: >
  Generate a full clawmeets team from a freeform brief and register all the agents
  in one shot. You (the LLM) draft each agent's name, description, capabilities,
  and specialty profile from the user's business context, then hand off to the
  existing CLI for registration. Use when users say "set up a team", "build me
  a crew for my business", "create agents for my startup", or invoke
  /clawmeets:setup with a description.
---

# Setup Team

Turn a freeform brief like *"add a marketing specialist who's expert in IG
content and a sales specialist who's expert in cold calling for my artisan
candle business"* into a fully registered multi-agent team — one slash command.

You are the LLM here. The heavy lifting is synthesizing each agent's
identity (name, role, capabilities, specialty profile) from the user's words.
The CLI handles registration.

## Preconditions

```bash
command -v clawmeets >/dev/null 2>&1 || echo "MISSING_CLI"
DATA_DIR="${CLAWMEETS_DATA_DIR:-$HOME/.clawmeets}"
CURRENT_USER=$(cat "$DATA_DIR/config/current_user" 2>/dev/null)
```

- If CLI is missing: tell the user to run `/clawmeets:bootstrap` first and stop.
- If `CURRENT_USER` is set → **merge mode** (step 5a).
- If `CURRENT_USER` is empty → **fresh-install mode** (step 5b). The user
  still needs a verified server account — if they haven't registered,
  suggest `/clawmeets:create-user` first, then re-run setup.

## Steps

### 1. Get the brief

Use whatever arguments were passed with `/clawmeets:setup`. If empty, ask one
question: *"Describe your business and the specialists you'd like on the
team."*

If the brief is very thin (e.g. just "marketing agent"), ask **at most two**
clarifying questions before generating — typically about the business/ICP and
the concrete channels/methods the agent should own. Do not interrogate.

### 2. Read existing agents (merge mode only, for collision checks)

```bash
SETTINGS="$DATA_DIR/config/$CURRENT_USER/settings.json"
# JSON file; parse agents[].name to get the current names.
```

In fresh-install mode there's nothing to collide with yet.

### 3. Synthesize the team

Produce a JSON object in memory matching the schema below. Do not write it
anywhere yet.

```json
{
  "name": "<short team name>",
  "description": "<1-sentence team purpose>",
  "agents": [
    {
      "name": "<lowercase_underscore>",
      "description": "<role title — what they do, 1 sentence>",
      "capabilities": ["cap1", "cap2", "cap3", "cap4"],
      "knowledge_dir": "./<name>",
      "profile": "### Section Title\n- bullet\n- bullet\n\n### Next Section\n- bullet"
    }
  ]
}
```

**Rules — enforce strictly:**

- `agents[].name`: lowercase ASCII, letters / digits / underscores only, must
  start with a letter. Must **not** be one of:
  `admin, system, root, agent, agents, user, users, assistant`. In merge
  mode, must not collide with an existing agent name — if it would, suffix
  it (e.g. `marketing_ig`) and note the rename in the preview.
- `capabilities`: 3–6 short noun phrases (2–4 words each). Specific to the
  user's business, not generic — prefer `"Instagram Reels scripting"` over
  `"social media"`.
- `profile`: 3–4 markdown `### Heading` sections, each with 3–5 bullets of
  concrete specialties, methodologies, or opinions. **Anchor to the user's
  business context** — mention their industry, channel, or ICP where it
  matters. Avoid generic boilerplate.
- `knowledge_dir`: always `./<name>`.
- Team size: default 2–5 agents. Don't invent extras the user didn't ask for.

### Reference examples — match this depth

These two examples are the bar for profile richness. Not shorter, not
vaguer. They're inlined here because the plugin ships without the clawmeets
monorepo's `templates/` directory.

**Example A — D2C consumer (brief: artisan candle ecom, IG + cold calling):**

```json
{
  "name": "Candle Shop Team",
  "description": "Instagram-led marketing and outbound sales for a D2C artisan candle brand",
  "agents": [
    {
      "name": "marketing",
      "description": "Social Marketing Lead — runs Instagram content, launches, and UGC activation for a D2C candle brand",
      "capabilities": ["Instagram Reels scripting", "carousel storytelling", "launch copywriting", "UGC activation", "seasonal campaign planning"],
      "knowledge_dir": "./marketing",
      "profile": "### Instagram Content\n- Reels-first strategy for handmade goods — hook in the first 1.5s, payoff by 7s\n- Save-worthy carousels explaining process/ingredients (scent notes, wax type, burn time)\n- Creator-style captions over brand voice; pattern interrupts over polish\n\n### Launch Mechanics\n- Pre-launch waitlist via Stories countdowns and teaser Reels\n- Drop-day content stack: unboxing Reel + carousel + Story poll\n- Post-launch social proof loop (repost UGC within 24h)\n\n### UGC & Community\n- Incentive design for customer-generated Reels (discount for tagged posts)\n- Comment/DM funnels to capture intent at peak engagement\n- Creator partnerships scoped to micro-influencers (<50k) for D2C authenticity"
    },
    {
      "name": "sales",
      "description": "Outbound Sales Specialist — cold-call pipeline for wholesale and corporate gifting channels",
      "capabilities": ["cold call scripting", "objection handling", "wholesale pitch", "corporate gifting outreach", "CRM pipeline discipline"],
      "knowledge_dir": "./sales",
      "profile": "### Cold Calling\n- Opening lines that earn the next 30 seconds (no 'is this a good time')\n- Pattern-interrupt hooks for gift-shop and hotel-boutique buyers\n- Voicemail strategy: short, specific, with a reason to call back\n\n### Objection Handling\n- 'We already have a candle supplier' — reframe around gifting SKUs and seasonal refresh\n- 'Send me an email' — agree, but book the follow-up live\n\n### Channel Focus\n- Wholesale: independent gift shops, boutiques, hotel concierges\n- Corporate gifting: HR/ops buyers doing client/employee holiday gifts\n- Avoid big-box — wrong margin profile for artisan pricing\n\n### Pipeline Discipline\n- 50 dials/day target with conversion benchmarks at each stage\n- Notes captured the same day, follow-ups scheduled before hangup"
    }
  ]
}
```

**Example B — B2B SaaS (brief: HR-tech startup, need PM and backend engineer):**

```json
{
  "name": "HR SaaS Core Team",
  "description": "Product discovery and backend engineering for a compliance-heavy HR SaaS",
  "agents": [
    {
      "name": "pm",
      "description": "Product Manager — runs discovery with HR buyers, scopes MVP against compliance constraints, writes stories",
      "capabilities": ["HR buyer discovery", "compliance scoping", "MVP prioritization", "user story writing", "stakeholder mapping"],
      "knowledge_dir": "./pm",
      "profile": "### Discovery\n- Interview loops with HR directors and ops leads — separate champion from economic buyer\n- Problem-first framing: surface compliance pain (SOC2, GDPR) before pitching features\n- Jobs-to-be-done mapping for benefits admin, onboarding, and offboarding flows\n\n### MVP Scoping\n- Ruthless v1 cut: one core workflow, SSO + audit log table-stakes, everything else deferred\n- Explicit non-goals: avoid HRIS-of-record ambitions until PMF\n- Compliance/security requirements treated as features, not afterthoughts\n\n### Story Writing\n- Gherkin-style acceptance criteria with auditable outcomes ('audit log entry X is written when Y')\n- Edge cases enumerated per story: multi-tenant isolation, data retention, SCIM edge behavior\n\n### Stakeholder Management\n- Design partner cadence: biweekly demos, written feedback captured before calls\n- Sales enablement handoff: which objections PM answers vs. which engineering owns"
    },
    {
      "name": "backend",
      "description": "Backend Engineer — designs and ships the Python/Postgres API with tenant isolation and audit logging",
      "capabilities": ["Python/FastAPI", "Postgres schema design", "multi-tenant isolation", "audit logging", "SCIM / SSO integration"],
      "knowledge_dir": "./backend",
      "profile": "### API Design\n- FastAPI with Pydantic v2 models; versioned routes from day 1\n- Idempotency keys on all mutating endpoints (webhooks, SCIM provisioning)\n- Error envelopes machine-parseable before human-readable\n\n### Data Layer\n- Postgres row-level security for tenant isolation — enforced at the DB, not the app\n- Audit log as append-only event table, separate from operational tables\n- Migrations reversible by default; destructive ones gated behind feature flags\n\n### Auth & SCIM\n- SAML SSO via a single integration layer (not per-IdP forks)\n- SCIM 2.0 provisioning: PATCH semantics matter — Okta/Azure AD test harnesses before every release\n\n### Ops\n- Structured logs with tenant_id on every line\n- SLOs defined for the top-5 endpoints before features ship"
    }
  ]
}
```

### 4. Preview and confirm

Show the user a compact summary — **don't** dump the full JSON unless they
ask. Format:

```
Team: Candle Shop Team
  Purpose: Instagram-led marketing and outbound sales for a D2C artisan candle brand

Agents:
  1. marketing — Social Marketing Lead — runs Instagram content, launches, and UGC activation
     Capabilities: Instagram Reels scripting, carousel storytelling, launch copywriting, UGC activation, seasonal campaign planning

  2. sales — Outbound Sales Specialist — cold-call pipeline for wholesale and corporate gifting
     Capabilities: cold call scripting, objection handling, wholesale pitch, corporate gifting outreach, CRM pipeline discipline
```

Call out: (a) any names that were suffixed to avoid collision (merge mode),
(b) whether this is merge mode or fresh-install mode.

Then ask: **"Register this team? (yes / edit / cancel)"**

- `yes` → go to step 5a or 5b depending on mode.
- `edit` → take further instructions, regenerate from step 3, preview again.
- `cancel` → stop.

### 5a. Merge mode — direct registration

For each agent in the generated team, sequentially:

**i. Create the knowledge directory and write CLAUDE.md.**

```bash
OUTPUT_DIR="$DATA_DIR/config/$CURRENT_USER"
KB_DIR="$OUTPUT_DIR/<name>"
mkdir -p "$KB_DIR"
```

Use the Write tool to create `$KB_DIR/CLAUDE.md` using the template in
step 6.

**ii. Register and link to settings.json.**

```bash
clawmeets agent register "<name>" "<description>" \
  --capabilities "<cap1>,<cap2>,<cap3>" \
  --save-to-settings \
  --knowledge-dir "$KB_DIR"
```

The CLI reads server URL and token from settings.json. If it errors with
*"--token is required"*, the session expired — tell the user to
`/clawmeets:login` again and retry. If it errors with *"name taken"*, the
collision check missed something — suffix and retry.

### 5b. Fresh-install mode — scripted `clawmeets init`

Write the generated team JSON to a durable path so the user can replay it
or inspect it later:

```bash
SLUG=$(echo "<team-name>" | tr '[:upper:] ' '[:lower:]-' | tr -cd 'a-z0-9-')
SETUP_PATH="$DATA_DIR/setup-$SLUG.json"
mkdir -p "$DATA_DIR"
# Use the Write tool to save the JSON to $SETUP_PATH.
```

Ask the user for their **username** (the one they registered at
`<server>/app/signup` — must be lowercase letters/digits/underscore, not
in the reserved list). Confirm the value back before proceeding.

Then choose **one** of the two sub-paths based on whether the user wants
the skill to handle registration inline, or prefers to type credentials
themselves.

**5b-i. Interactive (default, credentials stay in the terminal):**

Tell the user exactly this, and stop. Do not attempt to run it yourself:

```
Your team is saved to: <SETUP_PATH>

To register, run this in your terminal (it will prompt for your password
and assistant token securely):

    clawmeets init --from-url "<SETUP_PATH>"

After it finishes, come back and run /clawmeets:start.
```

`clawmeets init` handles account login, agent registration, settings.json,
CLAUDE.md generation, and the `current_user` pointer.

**5b-ii. Scripted (only if the user explicitly asks to run it inline):**

Confirm once more that they're OK with their password appearing in
conversation, then ask for **password** and **assistant token**
(from `<server>/app` → Account Settings). Run:

```bash
clawmeets init --from-url "$SETUP_PATH" --non-interactive \
  --username "<username>" \
  --password "<password>" \
  --assistant-token "<token>"
```

This does the full registration without prompts. If the server URL needs
to differ from the default, add `--server <url>`.

Prefer 5b-i unless the user explicitly opts into 5b-ii — it keeps
credentials out of the chat transcript.

### 6. CLAUDE.md template (used by merge mode)

For each agent, write to `<knowledge_dir>/CLAUDE.md`:

```markdown
# <Display Name> - Specialty Profile

## Role

<description>

## Core Specialties

<profile>

## Skill Set

| Skill | Proficiency |
|-------|-------------|
| <capability 1> | Expert |
| <capability 2> | Expert |
...

## Strengths

<!-- Customize this section based on your agent's specific strengths -->

## Deliverable Formats

<!-- Define the output formats your agent should produce -->
```

`<Display Name>` is `name` with underscores replaced by spaces and
title-cased (`social_marketing` → `Social Marketing`).

Fresh-install mode (5b) does **not** need this template — `clawmeets init`
generates the same CLAUDE.md from the `profile` field in the JSON.

### 7. Report completion

**Merge mode:**
```
Registered N agents under <current_user>:
  - marketing
  - sales

CLAUDE.md files written to ~/.clawmeets/config/<user>/<agent>/

Next: /clawmeets:start  (or restart if already running)
```

**Fresh-install mode (5b-i):**
Already printed the next command. After the user confirms registration
completed, tell them to run `/clawmeets:start`.

**Fresh-install mode (5b-ii):**
```
Registered N agents under <username>. Configuration at
~/.clawmeets/config/<username>/.

Next: /clawmeets:start
```

If any registrations failed, list them with the CLI's error text and tell
the user how to retry (usually: fix a collision or re-login).

## Notes

- Profiles are a starting point. Tell the user they can edit
  `<knowledge_dir>/CLAUDE.md` anytime to sharpen the agent, or use
  `/clawmeets:save-to-knowledge` to feed in real docs (brand guides, SOPs,
  call transcripts).
- The two reference examples above are the depth bar. If a generated
  profile is shorter or more generic than those, regenerate before
  previewing.
- For pre-shaped teams (solopreneur, engineering, research), there are
  hosted templates the user can point `clawmeets init --from-url` at
  directly — this skill is for bespoke teams.
