# JRG-CRM — Master Build Plan (The Constitution)

**Owner:** Jorge Ramirez (jorgeramirez76@gmail.com)
**Repo:** `TheJorgeRamirezGroup2` — CRM code lives in `crm/`
**Written by:** Fable 5 (planning pass, 2026-07-03)
**Executed by:** Sonnet 5 in Claude Code, one phase per session (see `crm/HANDOFF_PROMPTS.md`)

This document is the single source of truth. Any implementing model must read this file
FIRST, follow it exactly, and never redesign decisions marked **LOCKED**. If something is
genuinely impossible as specified, implement the closest working alternative and record the
deviation in `crm/DECISIONS.md`.

---

## 1. What we are building (one paragraph)

A self-hosted real estate CRM that runs 24/7 on Jorge's Mac Studio. It captures leads from
thejorgeramirezgroup.com and manual imports, then **autonomously nurtures each lead over
iMessage (sent from Jorge's real phone number via the Mac's Messages app) and email (sent
from Jorge's real Gmail)**. Every message in and out is stored, so the AI has full
conversational memory and always replies in context, in Jorge's voice, with real NJ market
knowledge pulled from the 440-page website content already in this repo. It follows the
**Lazy Agent methodology** (automation does the follow-up; Jorge only talks to
hand-raisers). When a lead shows interest after a few touches, the system generates a
**personalized AI video of Jorge (his face + cloned voice) via higgsfield.ai** and sends it.
Incoming iMessage replies are detected **instantly** (webhook from the Messages database
watcher), incoming emails within ~30 seconds. A local web dashboard ("Mission Control")
shows pipeline, conversations, approvals, and analytics.

---

## 2. What already exists in this repo (reuse, don't rebuild)

| Asset | Path | How the CRM uses it |
|---|---|---|
| Live website (Vercel) | root `*.html`, `towns/`, `blog/`, `es/` | Lead source + behavioral tracking target + AI knowledge base |
| Serverless lead endpoint (deployed, unwired) | `api/lead.js` | Already supports `CRM_WEBHOOK_URL` env var → point it at the CRM's inbound webhook. Wire the site forms to `/api/lead` in Phase 6 |
| Property lead scoring system (Python/SQLite) | `property-leads-system/` | Seller-lead scoring logic (7-factor, 0–100) — port the scoring weights into the CRM's TypeScript scorer; keep the Python system as a batch import source |
| Feature specs (marketing-level) | `docs/aisalespipeline-feature-*.md` | Product intent for AI SMS / email / clone video / custom AI brain / seller & buyer workflows — the sequences and copy angles in these files are the seed content for workflow templates |
| Seller workflow sequences (FSBO / Expired / Downsizer day-by-day cadences) | `docs/aisalespipeline-feature-seller-workflows.md` | Encode verbatim as the three seller workflow templates |
| Legal texting guide | `docs/legal-texting-expired-fsbo-guide.md` | Source for the compliance rules in §12 |
| Town/market data | `town_data.py`, `towns/*.html`, calculators | Extract into the AI knowledge base (Phase 4) |
| Old architecture sketch | `SYSTEM_ARCHITECTURE.md` | Superseded by this document for the CRM; still valid for the property-prediction side |

---

## 3. Feature parity targets (GoHighLevel + Ylopo) and scoping

We are one operator, not a SaaS. Build the features that produce conversations and
appointments; stub or skip pure-SaaS plumbing. **This scoping is LOCKED.**

### Build fully (core value)
| Feature | Parity source |
|---|---|
| Contacts + smart lists + tags + custom fields | GHL |
| Pipelines with drag-drop stages (Buyer + Seller) | GHL |
| **Unified conversation inbox** (iMessage + email + notes in one thread per lead) | GHL Conversations |
| **Workflow/automation engine** (triggers → wait/branch/action) | GHL Workflows |
| **AI conversational nurture** — 2-way, context-aware, books appointments | Ylopo RAIYA |
| Behavioral triggers from website activity (viewed valuation page, calculator, town pages) | Ylopo behavioral marketing |
| Listing/market alerts as nurture content (link to site pages, market reports) | Ylopo listing alerts (adapted — no IDX yet) |
| Lead scoring incl. engagement scoring | Ylopo priority alerts + GHL |
| **AI clone video generation + delivery** (Higgsfield) | Beyond both (Ylopo has video texts; ours is personalized AI clone) |
| Appointment scheduling (Google Calendar; propose slots in-conversation) | GHL Calendars |
| Long-term nurture / re-engagement campaigns | Lazy Agent core |
| Mission Control dashboard + reporting (response rates, funnel, per-source ROI) | Ylopo Mission Control / GHL dashboard |
| Opt-out/DNC/suppression handling, quiet hours | Both (compliance) |

### Build minimal (v1 = simplest working version)
- **Email marketing/bulk sends:** simple templated sends to a smart list via Gmail with per-recipient personalization and throttling (no drag-drop email builder — Markdown/HTML templates in repo).
- **Forms:** the site's existing forms are the form builder. `api/lead.js` is the ingestion path.
- **Call tracking / AI voice calls:** log-only in v1 (manual call logging button). Twilio voice + AI voice agent is Phase 9+ (post-v1), interfaces stubbed.
- **Facebook/Google dynamic ads (Ylopo's ad engine):** out of scope to automate; the CRM captures `utm_*`/source so paid traffic is attributed. Ad launching stays manual per `docs/facebook-retargeting-ad-templates.md`.

### Explicitly skip (record in DECISIONS.md, do not build)
White-label/multi-tenant, memberships/courses, invoicing/payments, social planner,
reputation-management review funnels (v1 sends a manual review-ask template instead),
website/funnel builder (the site already exists), IDX home search portal (big separate
project; the site's town pages serve this role in v1).

---

## 4. System architecture (LOCKED)

```
                    ┌──────────────────────────────────────────────┐
                    │                MAC STUDIO (24/7)             │
                    │                                              │
 Website (Vercel)   │  ┌────────────┐   ┌───────────────────────┐  │
 api/lead.js ───────┼─▶│  Fastify   │   │  Worker loop (same    │  │
 (CRM_WEBHOOK_URL   │  │  HTTP API  │──▶│  process, setInterval)│  │
  via Cloudflare    │  │  :4820     │   │  - due scheduled msgs │  │
  Tunnel)           │  └─────┬──────┘   │  - workflow engine    │  │
                    │        │          │  - Gmail poller (30s) │  │
 tracker.js on ─────┼───────▶│          │  - video job poller   │  │
 site pages         │        │          └──────────┬────────────┘  │
                    │        ▼                     │               │
                    │  ┌────────────┐              ▼               │
                    │  │  SQLite    │◀──── AI Engine (Claude API)  │
                    │  │  crm.db    │      Haiku = classify/route  │
                    │  └────────────┘      Sonnet = compose        │
                    │        ▲                                     │
                    │        │ webhook (instant)      ┌──────────┐ │
                    │  ┌─────┴──────────┐  AppleScript│ Messages │ │
                    │  │ BlueBubbles    │────────────▶│ .app     │─┼──▶ iMessage
                    │  │ server (:1234) │◀────────────│ chat.db  │ │    (Jorge's
                    │  └────────────────┘   reads     └──────────┘ │     number)
                    │                                              │
                    │  React dashboard (Vite, served by Fastify)   │
                    └──────────────────────────────────────────────┘
                             │                │
                             ▼                ▼
                        Gmail API        Higgsfield API
                        (Jorge's         (voice clone +
                         real inbox)      avatar video)
```

**Why the Mac Studio:** iMessage can only be sent legitimately from a signed-in macOS
Messages app. Jorge's iPhone has Text Message Forwarding → Mac Studio, so messages send
from **his real number** and replies hit the Mac's `chat.db` instantly. Everything else
co-locates there to keep the system single-box, zero-hosting-cost, and private.

### Components
1. **`crm/server`** — one Node.js (TypeScript) process: Fastify HTTP API + background worker
   loop + static serving of the built dashboard. Managed by `launchd` (auto-start, auto-restart).
2. **BlueBubbles server** (free, open-source macOS app) — the iMessage bridge. REST API to
   send; fires a webhook to `localhost:4820/webhooks/bluebubbles` on every new message
   (**this is the instant reply detection**). Fallback if BlueBubbles breaks: a `chokidar`
   watcher on `~/Library/Messages/chat.db` + AppleScript sender (implement as the
   `imessage-applescript` driver behind the same interface).
3. **Gmail integration** — googleapis Node SDK, OAuth2 (offline refresh token), `history.list`
   polling every 30s for new inbound; send via `users.messages.send` with proper `In-Reply-To`
   /`References` threading so conversations stay in one Gmail thread.
4. **AI Engine** — Anthropic API (`@anthropic-ai/sdk`). Two tiers, **LOCKED**:
   - `claude-haiku-4-5-20251001` for classification, intent detection, routing, scoring.
   - `claude-sonnet-5` for reply composition, video scripts, summaries.
5. **Higgsfield video pipeline** — Higgsfield API: one-time voice clone + avatar character;
   per-lead talking-head video jobs; poll to completion; deliver link.
6. **Dashboard** — React + Vite SPA under `crm/dashboard`, served at `http://localhost:4820`.
7. **Cloudflare Tunnel** (free) — exposes exactly two public paths to the Mac:
   `/webhooks/site-lead` and `/t.gif` (tracker). Everything else stays localhost-only.

### Tech stack (LOCKED)
- Node.js 22 + TypeScript, Fastify, better-sqlite3 (WAL mode) + Drizzle ORM, Zod for all
  I/O validation, node-cron for schedules, pino logging (file + pretty console).
- No Redis, no Postgres, no Docker, no external queue. SQLite tables ARE the queue.
- Tests: Vitest. Every phase lands with tests for its core logic (not UI).
- Single `.env` at `crm/.env` (gitignored), `crm/.env.example` committed and exhaustive.

---

## 5. Data model (LOCKED — Drizzle schema in `crm/server/src/db/schema.ts`)

```sql
-- People
contacts(id, first_name, last_name, phones JSON, emails JSON, address, town, county,
  source, source_detail, utm JSON, timezone DEFAULT 'America/New_York',
  imessage_handle,            -- resolved chat GUID / handle for BlueBubbles
  preferred_channel,          -- 'imessage' | 'email' | null(auto)
  consent_sms INT, consent_email INT, consent_source TEXT, consent_at,
  do_not_contact INT DEFAULT 0, archived INT DEFAULT 0, created_at, updated_at)

tags(id, name UNIQUE); contact_tags(contact_id, tag_id)
custom_fields(contact_id, key, value)   -- budget, beds, pre-approval, timeline, etc.

-- Pipeline
pipelines(id, name)                      -- seed: 'Buyer', 'Seller'
stages(id, pipeline_id, name, position)  -- see §8 for seeded stages
leads(id, contact_id, pipeline_id, stage_id, intent TEXT, -- 'buy'|'sell'|'both'
  score INT, score_breakdown JSON, temperature TEXT, -- HOT/WARM/COLD
  assigned_autonomy TEXT DEFAULT 'approval', -- 'approval'|'guarded'|'full' (§7.5)
  stage_entered_at, next_touch_at, last_inbound_at, last_outbound_at,
  video_sent_at, appointment_at, closed_reason, created_at, updated_at)

-- Conversations (the memory)
messages(id, contact_id, channel TEXT,   -- 'imessage'|'email'|'note'|'call_log'|'video'
  direction TEXT,                        -- 'in'|'out'
  body TEXT, subject TEXT, attachments JSON,
  external_id TEXT, thread_key TEXT,     -- BlueBubbles GUID / Gmail threadId
  status TEXT,      -- 'queued'|'awaiting_approval'|'sent'|'delivered'|'read'|'failed'|'received'
  generated_by TEXT, -- 'ai'|'human'|'workflow_template'
  model_used TEXT, tokens_in INT, tokens_out INT, error TEXT, sent_at, created_at)
-- UNIQUE(channel, external_id) — dedupes webhook/poll double-delivery

conversation_summaries(contact_id, summary TEXT, facts JSON, last_message_id, updated_at)
  -- rolling summary regenerated when un-summarized history > ~3000 tokens; `facts` is
  -- structured extraction (budget, timeline, family, objections, promises made)

-- Automation
workflows(id, name, trigger JSON, enabled INT)     -- definitions stored as JSON DSL (§8.3)
workflow_steps(id, workflow_id, position, step JSON)
enrollments(id, workflow_id, lead_id, current_step, state TEXT, -- active/paused/completed/exited
  wake_at, context JSON, created_at)
-- rule: enrolling in a new nurture workflow exits prior nurture enrollments for that lead

scheduled_actions(id, lead_id, kind TEXT, payload JSON, run_at, status, attempts,
  last_error, created_at)  -- THE queue. kind: send_message|generate_video|escalate|recompute_score|...

events(id, contact_id NULL, kind TEXT, payload JSON, created_at)
-- kinds: page_view, form_submit, valuation_view, calculator_use, link_click, video_watch,
--        email_open, stage_change, opt_out, escalation, error — feeds triggers + scoring

-- Video
videos(id, lead_id, script TEXT, higgsfield_job_id, status, -- scripted/queued/rendering/ready/sent/failed
  video_url, thumb_url, watch_events JSON, created_at, updated_at)

-- Ops
suppressions(id, kind TEXT, value TEXT, reason, created_at) -- phone/email hard blocks
settings(key PRIMARY KEY, value JSON) -- quiet hours, autonomy defaults, daily caps, profile
audit_log(id, actor, action, entity, entity_id, detail JSON, created_at)
```

---

## 6. Channel layer

### 6.1 iMessage (primary channel) — via BlueBubbles
**Human setup (Jorge, documented in `crm/SETUP.md`):** Mac signed into his Apple ID;
iPhone → Settings → Messages → Text Message Forwarding → enable Mac Studio; install
BlueBubbles server; set server password; add webhook `http://localhost:4820/webhooks/bluebubbles`
(events: new-messages, updated-messages); disable Mac sleep (`caffeinate`/Energy settings).

**Code (`crm/server/src/channels/imessage.ts`)** implements the `Channel` interface:
```ts
interface Channel {
  send(msg: OutboundMessage): Promise<{externalId: string}>;
  // inbound arrives via webhook/poller and is normalized to InboundMessage
}
```
- **Send:** `POST http://localhost:1234/api/v1/message/text?password=…` with
  `{chatGuid, message, method: 'apple-script'}`. Create chat first if none exists
  (`/api/v1/chat/new`). Support attachments (video thumbnail) via the attachment endpoint.
- **Receive (instant):** webhook handler validates payload, ignores `isFromMe`, dedupes on
  message GUID, resolves handle → contact (create a shell contact for unknown senders,
  flagged `needs_review` — do NOT auto-nurture unknown numbers), inserts `messages` row,
  emits `inbound_message` → AI engine. Target latency: < 2 seconds from tap-to-send on the
  lead's phone to AI engine invocation.
- **Delivery/read receipts:** consume `updated-messages` webhook events → update status.
- **Green-bubble fallback:** if BlueBubbles reports the handle is SMS-only, still send (it
  goes as SMS from Jorge's number via forwarding). If send fails entirely → fall back to
  email if available → else task for Jorge.
- **Health:** ping BlueBubbles `/api/v1/ping` every 5 min; on failure, alert Jorge (email +
  dashboard banner) and pause iMessage sends (queue holds).

### 6.2 Email — Gmail API (Jorge's real account)
- OAuth2 desktop flow, scopes `gmail.modify` + `gmail.send`; refresh token in `.env`;
  one-time `npm run setup:gmail` CLI does the browser dance.
- **Send:** RFC 2822 via `users.messages.send`. Always thread: store Gmail `threadId` as
  `thread_key`; set `In-Reply-To`/`References` on replies. Plain, personal-looking emails
  (light HTML, no marketing chrome) — deliverability comes from being a real 1:1 Gmail.
- **Receive:** worker polls `users.history.list` (startHistoryId cursor) every 30s; new
  inbound → match `From` to contact emails → insert + emit `inbound_message`. Unmatched
  mail is ignored (it's Jorge's personal inbox — filter to threads the CRM started OR
  senders that are contacts).
- **Open tracking:** 1px `/t.gif?m=<messageId>` via the tunnel → `email_open` event (soft
  signal only).
- **Bulk/nurture sends:** throttle ≤ 1 msg/20s, daily cap in `settings` (default 100/day)
  to protect the Gmail account. CAN-SPAM footer on campaign (non-1:1) emails.

### 6.3 Channel selection policy (LOCKED)
`preferred_channel` if set; else: has mobile phone + consent → iMessage first; email as
secondary/long-form. Mirror important sends (e.g., video) on both when both exist. All
outbound passes the **send gate**: suppression check → consent check → quiet hours
(default 8:30am–8:30pm America/New_York, configurable) → daily per-lead cap (max 2
outbound/day unless replying) → global daily caps. Blocked sends reschedule to next
allowed window, never silently drop.

---

## 7. AI conversation engine (`crm/server/src/ai/`)

### 7.1 Inbound flow
```
inbound_message
  → Haiku classify: {intents:[reply|question|interest|objection|scheduling|opt_out|wrong_person|spam],
                     sentiment, urgency, extracted_facts{}}
  → hard rules FIRST (regex, before AI): STOP/UNSUBSCRIBE/"stop texting" → opt-out flow
  → update lead: last_inbound_at, merge extracted_facts into custom_fields, recompute score
  → cancel pending queued outbound for this lead (never send a scheduled blast after a human reply)
  → workflow engine: pause active drip enrollment (lead is now in live conversation)
  → escalation check (§7.4) — if hot, notify Jorge AND still draft a reply
  → compose reply (Sonnet) with full context (§7.2) → autonomy gate (§7.5) → send gate → send
```

### 7.2 Context assembly for composition (order matters)
1. **System prompt = Jorge persona** (`crm/server/prompts/persona.md`, built in Phase 4 from
   `why-jorge-ramirez.html`, the aisalespipeline docs, and a questionnaire Jorge fills in
   `crm/knowledge/jorge-profile.md`): voice/tone (warm, direct, bilingual EN/ES — reply in
   the lead's language), credentials, objection-handling style, hard rules (never invent
   listings/prices/appointments; never discuss commission cuts; never give legal/tax advice
   — refer out; texts ≤ ~2 sentences unless answering a question; one emoji max; no
   corporate-speak).
2. **Lead card:** profile, stage, score, source, custom fields, extracted facts.
3. **Conversation:** rolling summary + last 20 raw messages verbatim (both channels interleaved).
4. **Knowledge:** top-k market facts retrieved from the knowledge base (§7.3) matching the
   lead's town/intent + current message.
5. **Task instruction:** what this message must accomplish (from workflow step or reply goal)
   + channel constraints (iMessage: short; email: subject + medium).

### 7.3 Knowledge base ("Custom AI Brain")
`crm/knowledge/` — markdown facts files generated in Phase 4 by a script that extracts from
`town_data.py` + town pages (median price, DOM, schools, commute, taxes per town) plus
Jorge's own answers (process, fees approach, testimonials, service area). Retrieval v1 =
keyword/BM25 over chunks (no vector DB — LOCKED for v1; it's 100-ish towns, BM25 is
plenty). Each fact chunk carries `as_of` date; prompt instructs the model to hedge stale
numbers ("as of early 2026").

### 7.4 Escalation to Jorge ("hand-raiser" detection — the Lazy Agent hinge)
Escalate when: lead asks to talk/meet/see a property; mentions selling timeline ≤ 90 days;
pre-approved buyer; score crosses HOT; sentiment angry; AI is uncertain (self-reported
confidence < threshold); or any message the AI classifies as `scheduling`.
Escalation = iMessage **to Jorge's own number** from the system (a dedicated "JRG CRM"
contact/chat) with lead name, one-line summary, suggested action, and dashboard deep link
+ dashboard task. The AI still handles the immediate reply unless autonomy says otherwise.

### 7.5 Autonomy levels (per lead; global default in settings) — LOCKED rollout
- **`approval`** (default for weeks 1–2): AI drafts; message sits `awaiting_approval`;
  Jorge approves/edits in dashboard or by replying to the escalation iMessage with
  "ok"/edited text. Drafts auto-expire after 4h with a reminder.
- **`guarded`**: AI auto-sends replies + workflow messages; first-touch to a brand-new lead
  and anything involving pricing commitments/appointment confirmations still need approval.
- **`full`**: AI sends everything within send-gate rules; Jorge gets the escalations only.
This staged rollout is the safety story: no fully autonomous messages until the drafts
have proven trustworthy in `approval` mode.

### 7.6 Outbound (workflow-initiated) messages
Workflow steps say `{action:'ai_message', goal:'…', template_hint:'…'}` — Sonnet composes
fresh from goal + context (personalized, never mail-merge-stale). Templates from the
seller-workflow docs are style/goal hints, not literal sends.

### 7.7 Cost + robustness
Prompt-cache the persona+knowledge prefix. Log tokens per message (columns exist). Budget
expectation: Haiku classify ≈ $0.001, Sonnet reply ≈ $0.01–0.03 → even 1,000 AI messages/mo
≈ $20–40 API spend. Retries with exponential backoff; on repeated AI failure → escalate,
never send unreviewed fallback text.

---

## 8. Lazy Agent workflow engine

### 8.1 Doctrine (encoded, from Ylopo/Barry Jenkins methodology)
1. The system, not the agent, does 100% of routine follow-up — **forever** (leads nurture
   for years, not 10 days).
2. Jorge only enters when a lead **raises their hand** (reply/behavior/score).
3. Behavior beats declared intent: a lead hitting the home-valuation page 3× this week is
   hot regardless of what they said last month.
4. Every touch offers value (market data, listings, answers) — never "just checking in"
   twice in a row.
5. Speed-to-lead: first touch < 60 seconds from capture, 24/7 (send gate may hold to
   morning during quiet hours — that's correct behavior).

### 8.2 Seeded pipelines & stages (LOCKED)
**Buyer:** New → Attempting Contact → Engaged (AI) → Hot / Hand-Raiser → Appointment Set →
Active Client → Under Contract → Closed → Long-Term Nurture
**Seller:** New → Attempting Contact → Engaged (AI) → Valuation Delivered → Hot /
Hand-Raiser → Listing Appt → Listed → Under Contract → Closed → Long-Term Nurture
Stage transitions are event-driven (reply → Engaged; escalation accepted → Hot;
appointment booked → Appointment Set; 3 signals → auto-suggest stage moves in dashboard).

### 8.3 Workflow DSL (JSON, stored in `workflows`/`workflow_steps`)
```jsonc
{ "name": "New Buyer Lead — Speed to Lead",
  "trigger": {"kind": "lead_created", "filter": {"intent": "buy"}},
  "steps": [
    {"action": "ai_message", "channel": "auto",
     "goal": "Warm intro, reference the exact page/form they came from, ask ONE qualifying question (timeline or area)."},
    {"wait": {"hours": 4, "until_no_reply": true}},
    {"action": "ai_message", "channel": "email",
     "goal": "Send value: link the matching town guide from the site; ask about must-haves."},
    {"wait": {"days": 1, "until_no_reply": true}},
    {"action": "ai_message", "goal": "Light nudge with a market stat for their town."},
    {"wait": {"days": 2, "until_no_reply": true}},
    {"branch": {"if": "lead.score >= 60", "then": [{"action": "generate_video"}],
                "else": [{"action": "ai_message", "goal": "Video-less touch 4"}]}},
    {"wait": {"days": 4, "until_no_reply": true}},
    {"action": "enroll", "workflow": "Long-Term Nurture — Buyer"}
  ]}
```
Engine rules: `until_no_reply` waits auto-exit the sequence into "Engaged" handling when
the lead replies; enrolling into a new nurture exits the old one; all waits materialize as
`enrollments.wake_at` scanned by the worker every 30s; every action passes the send gate.

### 8.4 Seeded workflow templates (Phase 5 — encode all of these)
1. **New Buyer Lead** (above). 2. **New Seller / Valuation Lead** — intro + "want the full
number?" → CMA offer → equity angle → video at interest. 3. **FSBO**, 4. **Expired**,
5. **Downsizer** — day-by-day cadences exactly as written in
`docs/aisalespipeline-feature-seller-workflows.md` (voice-call days become call-tasks for
Jorge in v1). 6. **Long-Term Nurture (Buyer & Seller variants)** — every 3–4 weeks, rotating
value types (market update / new blog post / seasonal tax angle / anniversary of inquiry),
**runs indefinitely**. 7. **Behavioral: Valuation Revisit** — trigger `page_view
url~home-valuation, 2+ in 7d` → AI text "noticed you're keeping an eye on values…".
8. **Behavioral: Calculator Use** → relevant nudge. 9. **Post-Video Follow-Up** — watched:
strike while warm; unwatched 48h: resend other channel. 10. **Re-Engagement / Win-Back** —
no inbound in 90d → "market changed" video or text. 11. **Post-Appointment** →
confirmation, reminder, no-show recovery. 12. **Past Client** → anniversary, review ask
(manual template), referral touch.

### 8.5 Scoring (port + extend `property-leads-system/scorer.py`)
`score = base(source quality) + intent decl. + engagement (replies, opens, page views w/
7-day half-life decay) + recency + fit`. HOT ≥ 70 / WARM 40–69 / COLD < 40. Recompute on
every event; crossing HOT fires escalation trigger. Keep the 7-factor property-side scorer
for seller-lead imports.

---

## 9. Higgsfield AI video pipeline (`crm/server/src/video/`)

### 9.1 One-time setup (Jorge, in `crm/SETUP.md`)
Record ~3–5 min of clean talking-head footage (good light, quiet room, eye contact) + read
the provided 2-min voice script. In Higgsfield: create **voice clone** (from the audio) and
an **avatar character** (from the footage/still) — via Higgsfield's app or MCP tools
(`create_voice`, character creation). Store `HIGGSFIELD_API_KEY`, `HIGGSFIELD_VOICE_ID`,
`HIGGSFIELD_CHARACTER_ID` in `.env`.

### 9.2 Trigger (the user's exact requirement — LOCKED)
`generate_video` fires when **all** hold: lead has ≥ 1 inbound reply (interest shown);
≥ 3 total outbound touches across email+iMessage; no appointment yet; no video in last
30 days; consent OK. Reachable from workflow branches (§8.3) and manually from the
dashboard ("Send video now" button on any lead).

### 9.3 Flow
1. **Script (Sonnet):** 45–75 words, natural spoken register, references lead by name +
   their situation from conversation facts, one clear CTA, **includes a brief AI
   disclosure** ("this video message was generated with my AI — but the offer's all me").
   In `approval`/`guarded` autonomy the script needs Jorge's one-tap approval.
2. **Render:** submit talking-avatar job (character + voice + script) to Higgsfield API;
   store job id; worker polls (~30s) until `ready`; download/copy `video_url`.
   Build behind a `VideoProvider` interface; implement `higgsfield` driver first;
   note HeyGen as a contingency driver in DECISIONS.md if Higgsfield's avatar-speech API
   turns out not to support this shape — interface stays identical.
3. **Host:** copy the mp4 into the website repo `videos/leads/<slug>.mp4` → auto-deployed
   by Vercel; landing page `videos/leads/<slug>.html` (video + Calendly-style CTA buttons
   + tracker pixel → `video_watch` events). Unguessable slug (nanoid).
4. **Deliver:** iMessage — send the mp4 directly as an attachment when ≤ ~15 MB (plays
   inline in the bubble; the money shot) else send the landing link; email — thumbnail
   image linking to landing page, subject like "Made you a quick video, {name}".
5. **Follow-up:** enroll in Post-Video workflow (§8.4 #9).

---

## 10. Website integration (Phase 6)
1. **Wire forms:** flip form `action`s to `/api/lead` (per the note in `api/lead.js`), set
   `CRM_WEBHOOK_URL` in Vercel to the Cloudflare-Tunnel URL → `/webhooks/site-lead`
   (HMAC-signed with shared secret). CRM ingests → create/merge contact (match on
   email/phone) → create lead (intent inferred from source page) → enroll in matching
   workflow → **first touch within 60s** (subject to send gate).
2. **Behavior tracker:** tiny `js/crm-tracker.js` (queue-batched `navigator.sendBeacon` to
   tunnel `/track`): page URL, referrer, anon visitor id (localStorage). Identity stitch:
   on any form submit, tie visitor id → contact; all past anon events re-attribute. Only
   high-signal pages get workflow triggers (valuation, calculators, sell-*, town pages).
3. **Manual import:** CSV importer (dashboard + CLI) with column mapping, dedupe,
   `consent_source` required field; direct importer for `property-leads-system` SQLite.

---

## 11. Mission Control dashboard (React/Vite, served by Fastify)
Pages: **Inbox** (unified threads, approval queue with edit-in-place, send-as-Jorge
composer) · **Pipeline** (kanban per pipeline, drag stage, temperature colors) · **Lead
detail** (profile, facts, score breakdown, timeline of every message/event, actions: send
video / enroll / pause AI / DNC) · **Workflows** (list, enable/disable, enrollment counts,
per-step drop-off) · **Videos** (queue, previews, watch stats) · **Reports** (speed-to-lead,
reply rate by channel/workflow, funnel conversion, source ROI, AI cost) · **Settings**
(quiet hours, caps, autonomy default, persona editor, channel health lights).
Auth: single shared password → session cookie (it's localhost + tunnel-less; fine — LOCKED).
Live updates via SSE (`/api/stream`). Mobile-friendly CSS is required (Jorge will approve
drafts from his phone via the tunnel-protected dashboard… v1: approvals also work by
replying to the escalation iMessage, which covers mobile).

---

## 12. Compliance & safety rails (non-negotiable, enforced in code)
- **TCPA:** texting only contacts with a consent basis recorded (`consent_source`): website
  form submit (put consent language on forms in Phase 6), existing relationship, or manual
  attestation on import. FSBO/expired cold texts: follow `docs/legal-texting-expired-fsbo-guide.md`
  — identify yourself, honor immediate opt-out; **default posture: no cold texting of
  scraped lists via automation; property-leads mailing lists stay direct-mail**. Automated
  quiet hours. `STOP` regex handled before AI, adds suppression, confirms once, halts all
  workflows for that contact.
- **CAN-SPAM:** identification + unsubscribe link on campaign emails; 1:1 conversational
  replies exempt but honor any opt-out language.
- **AI disclosure:** videos disclose (§9.3); if a lead directly asks "is this a bot/AI?"
  the persona must answer honestly ("You're talking with my AI assistant — I see
  everything, want me to have Jorge call you?") and escalate. No exceptions.
- **Never fabricate:** no invented listings, prices, buyers ("I have 3 buyers" only if
  Jorge marks it true in settings), availability, or credentials. Template claims from the
  marketing docs must be toned to truth.
- **Rate limits:** per-lead ≤ 2 outbound/day (replies exempt), global daily caps, iMessage
  ≥ 45s between sends (human-ish pacing, protects the Apple ID).
- **Data:** DB is local; nightly `sqlite3 .backup` to `crm/backups/` + optional
  off-machine copy. `.env`, `crm.db`, backups gitignored.
- **Kill switch:** `settings.global_pause` — one dashboard toggle + `npm run pause` stops
  all outbound instantly.

---

## 13. Build phases (each = one Sonnet 5 session; prompts in HANDOFF_PROMPTS.md)

| # | Phase | Delivers | Acceptance criteria (must demo before commit) |
|---|---|---|---|
| 1 | Skeleton + DB + Inbox core | `crm/` scaffold, schema, migrations, contacts/leads/messages CRUD API, seed script, Vitest setup | `npm run dev` boots; API CRUD round-trips; tests green |
| 2 | iMessage channel | BlueBubbles driver, webhook inbound, send gate, quiet hours, suppressions, health check, `launchd` plist | Loopback test vs mock BlueBubbles; STOP flow; dedupe proven |
| 3 | Gmail channel | OAuth CLI, poller, threaded send, open pixel, bulk throttle | Mock-based tests; real-account smoke test doc |
| 4 | AI engine + knowledge base | Haiku classifier, Sonnet composer, persona builder script, KB extraction from town data, context assembler, autonomy gates, escalation | Golden-transcript tests (fixture conversations → sane drafts); opt-out precedes AI; token logging |
| 5 | Workflow engine + Lazy Agent templates | DSL executor, enrollments, waits, branches, all 12 seeded workflows, scoring engine | Simulated clock tests: full New-Buyer sequence executes; reply exits drip; HOT escalates |
| 6 | Website wiring + tracking | site-lead webhook, tracker.js + identity stitch, form flips, CSV import, Cloudflare Tunnel doc | Form submit → contact → first touch queued < 60s (in test harness) |
| 7 | Higgsfield video pipeline | provider interface + higgsfield driver, script gen, poll worker, hosting page, delivery, post-video workflow | Mocked-render e2e: trigger → script → "ready" → landing page exists → iMessage queued |
| 8 | Dashboard | all §11 pages, SSE, approval queue, reports | Approve-edit-send loop works; kanban drag persists; reports query real data |
| 9 | Hardening + go-live | backups, log rotation, error alerting, SETUP.md walkthrough, end-to-end dry run with Jorge's real accounts in `approval` mode | Full pipeline demo on a test lead (Jorge's own second number) |

Post-v1 backlog (record only): Twilio AI voice calls, IDX search portal, FB ads API,
review funnels, Spanish-first workflow variants (persona already replies in ES), ML scoring.

## 14. Rules for the implementing model (Sonnet 5)
1. Read this file + `DECISIONS.md` fully before writing code. Do not re-architect LOCKED items.
2. One phase per session. Finish the phase's acceptance criteria, run tests, commit with
   `crm phase N: <what>`, push to the working branch. Do not start the next phase.
3. Never put secrets in git. Keep `.env.example` current.
4. When blocked by a real-world unknown (an API shape, a Higgsfield endpoint), build behind
   the interface, mock it, mark `TODO(jorge-verify)` and list it at the end of the session
   summary — do not stall the phase.
5. Append every deviation/decision to `crm/DECISIONS.md` (date, what, why).
6. Keep each session's final summary short: what shipped, how to test it, what Jorge must
   do by hand before the next phase.
