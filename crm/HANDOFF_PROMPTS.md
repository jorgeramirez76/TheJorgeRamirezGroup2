# JRG-CRM — Handoff Prompts & Usage Strategy

How to get this built with the Claude usage you have left. Written by Fable 5; the prompts
below are designed to be pasted into **Sonnet 5** sessions verbatim.

---

## Usage strategy (read this first)

**Use Sonnet 5 for all nine phases. Do not use Fable 5 or Opus 4.8 for implementation.**

Why: the expensive part of a build like this is *deciding* — architecture, scoping, data
model, workflow design, compliance posture. That's done: `crm/MASTER_PLAN.md` locks every
decision. What remains is disciplined execution against a spec, which Sonnet 5 does
extremely well, and Sonnet burns your Max subscription several times slower than
Opus/Fable per session. Nine Sonnet sessions will cost you far less than three
Opus sessions and produce the same code because the spec removes the judgment calls.

Reserve whatever Fable/Opus budget you have left for exactly two things:
1. **A design review after Phase 5** (one short session: "read crm/MASTER_PLAN.md and the
   code in crm/, list the top issues that will bite at go-live, don't fix anything").
2. **Debugging a problem Sonnet gets stuck on twice.** If Sonnet fails the same
   acceptance criterion in two attempts, escalate that one narrow question to Opus 4.8.

Session discipline (this is what actually saves usage):
- **One phase per session, always a fresh session** (`/clear` or new session). Context
  re-reading is the silent usage killer.
- Every prompt below starts by pointing at the plan file — never re-explain the project.
- Let each session end with a commit + push. If a session dies mid-phase, start a new one
  with: *"Read crm/MASTER_PLAN.md §13 Phase N and `git log`/`git diff` — finish the
  incomplete Phase N work and its acceptance criteria."*
- Don't ask Sonnet to write long explanations back to you. The code + short summary is
  the deliverable.
- Runtime note: the CRM itself calls the **Anthropic API with an API key** (pay-per-token,
  separate from your Max subscription). Expect roughly $20–40/month at ~1,000 AI messages.
  Your Max plan is only spent while *building* in Claude Code.

Your human tasks (do these in parallel while Sonnet builds — they gate phases 2, 3, 7, 9):
- [ ] Phase 2 gate: Mac Studio signed into your Apple ID; iPhone Text Message Forwarding →
      Mac Studio ON; install BlueBubbles server; Mac set to never sleep.
- [ ] Phase 3 gate: create a Google Cloud project, enable Gmail API, create OAuth desktop
      credentials (Sonnet's SETUP.md from Phase 3 will walk you through the exact clicks).
- [ ] Phase 4 gate: fill in `crm/knowledge/jorge-profile.md` (the Phase 4 session creates
      the questionnaire — answer it honestly; it becomes your AI's personality).
- [ ] Phase 7 gate: record 3–5 min of talking-head video + 2 min of clean voice audio;
      create your Higgsfield voice clone + avatar character; get an API key.
- [ ] Phase 9 gate: an Anthropic API key, a Cloudflare account (free tunnel), and a test
      phone number that isn't yours (a friend's, for the live dry run).

---

## Phase prompts (paste verbatim, one per fresh Sonnet 5 session)

### Phase 1 — Skeleton, database, core API
```
Read crm/MASTER_PLAN.md in full — it is the locked spec for everything you build; also
read crm/DECISIONS.md. Execute Phase 1 from §13: scaffold the crm/ project (Node 22 +
TypeScript + Fastify + better-sqlite3 + Drizzle + Zod + Vitest + pino, per §4), implement
the complete schema from §5 with migrations, CRUD API for contacts/tags/custom
fields/pipelines/stages/leads/messages, the settings table with defaults from §6.3 and
§12 (quiet hours, caps, global_pause), a seed script (2 pipelines + stages from §8.2, a
few fake contacts/leads/messages), and .env.example. Meet every Phase 1 acceptance
criterion, run the tests, then commit ("crm phase 1: skeleton, schema, core API") and
push with -u to the current branch. End with a ≤10-line summary: what shipped, how I test
it, what I must do by hand before Phase 2 (per the plan: BlueBubbles + Text Message
Forwarding setup). Do not start Phase 2.
```

### Phase 2 — iMessage channel (BlueBubbles)
```
Read crm/MASTER_PLAN.md (§4, §6.1, §6.3, §12) and crm/DECISIONS.md, then skim the Phase 1
code in crm/server. Execute Phase 13 §Phase 2: the Channel interface, the BlueBubbles
driver (send text + attachment, create chat, ping health check every 5 min with alert +
send-pause on failure), the /webhooks/bluebubbles inbound handler (normalize, dedupe on
GUID, isFromMe filter, unknown-sender shell contact flagged needs_review, delivery/read
status updates), the full send gate (suppressions → consent → quiet hours → per-lead and
global caps → 45s iMessage pacing), the STOP/opt-out regex flow that runs before anything
else, and the launchd plist + install script for the server process. Write a mock
BlueBubbles server for tests and prove: inbound webhook → message row exactly once even
when delivered twice; STOP → suppression + workflows halted + one confirmation; quiet-hours
send reschedules instead of dropping. Write crm/SETUP.md sections for the human-side Mac
setup (Apple ID, Text Message Forwarding, BlueBubbles install + webhook config, no-sleep).
Commit "crm phase 2: iMessage channel via BlueBubbles" and push. ≤10-line summary. Do not
start Phase 3.
```

### Phase 3 — Gmail channel
```
Read crm/MASTER_PLAN.md (§6.2, §6.3, §12) and crm/DECISIONS.md, skim crm/server. Execute
Phase 3 from §13: googleapis OAuth2 desktop flow as an interactive `npm run setup:gmail`
CLI that saves a refresh token to .env; inbound via users.history.list polling every 30s
with a persisted cursor, matching senders to contacts and ignoring non-contact mail;
threaded send (RFC 2822, In-Reply-To/References, store threadId as thread_key); the
/t.gif open-tracking pixel route emitting email_open events; campaign-send throttling
(≥20s spacing, daily cap from settings) with CAN-SPAM footer for non-1:1 sends; channel
selection policy from §6.3 including iMessage→email fallback. Tests against a mocked
Gmail client covering threading, cursor resume after restart, and dedupe. Extend
crm/SETUP.md with the exact Google Cloud console steps. Commit "crm phase 3: Gmail
channel" and push. ≤10-line summary. Do not start Phase 4.
```

### Phase 4 — AI engine + knowledge base (the brain)
```
Read crm/MASTER_PLAN.md §7 word-for-word plus §12, and crm/DECISIONS.md; skim crm/server.
Execute Phase 4 from §13 using @anthropic-ai/sdk with claude-haiku-4-5-20251001 for
classification and claude-sonnet-5 for composition, with prompt caching on the stable
prefix. Build: the inbound pipeline from §7.1 (hard-rule opt-out first, Haiku classify,
fact extraction into custom_fields, cancel pending outbound on reply, pause drip
enrollments); the context assembler from §7.2; rolling conversation summaries per §5;
the knowledge extraction script that turns town_data.py + towns/*.html into
crm/knowledge/facts/*.md with as_of dates, plus BM25 retrieval (no vector DB); the
persona builder that compiles crm/server/prompts/persona.md from why-jorge-ramirez.html,
docs/aisalespipeline-feature-custom-ai-brain.md, and a generated
crm/knowledge/jorge-profile.md questionnaire for me to fill in (bilingual EN/ES rule:
reply in the lead's language); escalation detection per §7.4 including the
iMessage-to-Jorge notifier; and the three autonomy gates from §7.5 with the
awaiting_approval flow (approve/edit via API; 4h expiry reminder). Honesty rails from
§12 go in the persona (AI discloses if asked, never fabricates listings/buyers/prices).
Golden-transcript tests: fixture conversations in EN and ES that must produce a
classification, correct escalation decisions, and a draft that passes shape checks
(length limits per channel, no forbidden claims). Log tokens per message. Commit "crm
phase 4: AI conversation engine + knowledge base" and push. ≤10-line summary including
where I fill in jorge-profile.md. Do not start Phase 5.
```

### Phase 5 — Workflow engine + Lazy Agent templates + scoring
```
Read crm/MASTER_PLAN.md §8 word-for-word plus §7.6, and crm/DECISIONS.md; skim crm/server.
Execute Phase 5 from §13: the JSON workflow DSL and executor (triggers: lead_created,
event, score_crossed, no_inbound_for; steps: ai_message with goal, wait with
until_no_reply, branch on lead/score/custom-field conditions, enroll, generate_video stub
that enqueues a scheduled_action, task-for-Jorge); enrollments with wake_at scanning every
30s; the rules that a reply exits until_no_reply waits into Engaged handling and that new
nurture enrollment exits old nurture; stage auto-transitions from §8.2. Seed ALL 12
workflows from §8.4 — take the FSBO/Expired/Downsizer day-by-day cadences verbatim from
docs/aisalespipeline-feature-seller-workflows.md (voice-call days become Jorge tasks), and
make Long-Term Nurture genuinely indefinite with rotating value types. Implement the
scoring engine from §8.5 (port weights from property-leads-system/scorer.py, add
engagement scoring with 7-day half-life decay), recomputed on every event, with HOT
crossing firing escalation. Tests with a simulated clock: the New Buyer sequence executes
end-to-end with correct timing; a mid-sequence reply cancels the pending drip message;
score decay works. Commit "crm phase 5: workflow engine + Lazy Agent templates + scoring"
and push. ≤10-line summary. Do not start Phase 6.
```

### Phase 6 — Website wiring + behavior tracking + imports
```
Read crm/MASTER_PLAN.md §10 plus §12 consent rules, and crm/DECISIONS.md; also read
api/lead.js and one form-bearing page (contact.html) to see the current form pattern.
Execute Phase 6 from §13: the HMAC-verified /webhooks/site-lead endpoint (create-or-merge
contact on email/phone, infer intent from source page, record consent_source from the
form, enroll in the matching workflow, first touch queued within 60s subject to the send
gate); js/crm-tracker.js (sendBeacon batching, localStorage visitor id, only ship events
for the high-signal pages listed in §10) plus the /track endpoint and identity stitching
that re-attributes anonymous history on form submit; flip the site form actions to
/api/lead and add TCPA consent language next to phone fields; CSV importer (CLI + API)
with column mapping, dedupe, required consent_source, plus a direct importer for
property-leads-system/property_leads.db; document the Cloudflare Tunnel setup in
crm/SETUP.md (only /webhooks/site-lead, /track, /t.gif exposed). Test: fake form POST →
contact + lead + enrollment + queued first touch, and anon page views correctly stitched
after the form submit. Commit "crm phase 6: website wiring, tracking, imports" and push.
≤10-line summary listing the Vercel env vars I must set. Do not start Phase 7.
```

### Phase 7 — Higgsfield AI video pipeline
```
Read crm/MASTER_PLAN.md §9 word-for-word plus §12 AI-disclosure rules, and
crm/DECISIONS.md; skim crm/server. Execute Phase 7 from §13: the VideoProvider interface
with a higgsfield driver (voice id + character id + script → job id → poll ~30s → video
url; consult Higgsfield's public API docs for the talking-avatar/speak endpoint shapes —
if an endpoint shape is unverifiable from docs, build it behind the interface with your
best-documented guess, mock it in tests, and mark TODO(jorge-verify)); the §9.2 trigger
condition exactly (≥1 inbound reply AND ≥3 outbound touches AND no appointment AND no
video in 30 days AND consent) wired to the Phase 5 generate_video action plus a manual
API trigger; Sonnet script generation per §9.3 (45–75 words, personalized from
conversation facts, CTA, brief AI disclosure) honoring autonomy approval; hosting into
videos/leads/<nanoid>.mp4 + a landing page template with CTA buttons and the tracking
pixel wired to video_watch events; delivery per §9.4 (iMessage attachment when ≤15MB else
link; email thumbnail + link) and auto-enrollment into the Post-Video workflow. Mocked
end-to-end test: eligible lead → script → render-complete → landing page file exists →
delivery queued on both channels. Extend crm/SETUP.md with my one-time Higgsfield steps
(recording checklist, voice clone, character, API key). Commit "crm phase 7: Higgsfield
AI video pipeline" and push. ≤10-line summary. Do not start Phase 8.
```

### Phase 8 — Mission Control dashboard
```
Read crm/MASTER_PLAN.md §11 and crm/DECISIONS.md; skim the crm/server API surface.
Execute Phase 8 from §13: React + Vite SPA in crm/dashboard, built output served by
Fastify at :4820, single-password session auth, SSE live updates via /api/stream. Pages:
Inbox (unified per-lead threads across channels, the approval queue with edit-in-place
approve/reject, manual send-as-Jorge composer); Pipeline kanban with drag-to-stage;
Lead detail (profile, extracted facts, score breakdown, full timeline, buttons: send
video now, enroll in workflow, pause AI, mark DNC); Workflows (enable/disable, enrollment
counts, per-step drop-off); Videos (queue, preview, watch stats); Reports (speed-to-lead,
reply rate by channel and by workflow, funnel conversion by stage, source ROI, AI token
cost); Settings (quiet hours, caps, autonomy default, persona editor writing to
persona source files, channel health lights, the global_pause kill switch). Mobile-usable
CSS. Keep the design clean and dense — this is an operator tool, not a marketing site.
Verify the approve-edit-send loop and kanban drag persistence against the real dev
server. Commit "crm phase 8: Mission Control dashboard" and push. ≤10-line summary.
Do not start Phase 9.
```

### Phase 9 — Hardening + go-live
```
Read crm/MASTER_PLAN.md §12–§14 and crm/DECISIONS.md; skim the whole crm/ tree. Execute
Phase 9 from §13: nightly sqlite backup job to crm/backups/ with 14-day retention; pino
log rotation; error alerting (repeated worker/channel failures → iMessage to Jorge +
dashboard banner); npm run pause / resume; a doctor command (npm run doctor) that checks
every dependency (BlueBubbles ping, Gmail token, Anthropic key, Higgsfield key, tunnel,
disk space) with clear fix hints; finalize crm/SETUP.md into a single ordered go-live
walkthrough ending with the live dry run: import one test contact (a real second phone
number), run the New Buyer workflow in approval mode, approve each draft, confirm iMessage
send + instant reply detection + escalation + video generation + dashboard visibility.
Fix anything the dry-run script reveals as untestable. Update README.md in crm/ with a
one-page operator guide. Commit "crm phase 9: hardening + go-live" and push. Summary:
the exact ordered checklist I follow to go live, and the recommendation to run 2 weeks
in approval mode before switching to guarded (per §7.5).
```

---

## After go-live (cheap Sonnet sessions, as needed)
- "Read crm/MASTER_PLAN.md. Here are 5 real conversations where the AI's draft was off:
  <paste>. Tune persona.md and the composer instructions; add golden tests capturing each."
- "Add workflow: <describe>. Follow the §8.3 DSL and seed it like the Phase 5 templates."
- Backlog items from §13 (AI voice calls, IDX portal) — each is its own planned mini-spec
  first; ask for a plan-only session before a build session.
