# JRG-CRM — Decision Log

Append-only. Every deviation from `MASTER_PLAN.md`, every judgment call the implementing
model makes, gets a dated entry here: **date · phase · what · why**.

## 2026-07-03 · planning (Fable 5)
- **iMessage bridge = BlueBubbles** (webhook = instant reply detection) with a
  chat.db-watcher + AppleScript driver as the designated fallback behind the same
  `Channel` interface. Chosen over raw chat.db polling as primary because BlueBubbles
  also handles send, attachments, chat creation, and delivery/read events.
- **Email = Jorge's real Gmail via Gmail API**, 30s history polling (no public push
  endpoint needed). Resend (already in `api/lead.js`) stays for transactional site mail
  only; personal 1:1 nurture must come from the real inbox for deliverability and trust.
- **Video = Higgsfield** (user requirement) behind a `VideoProvider` interface; HeyGen is
  the named contingency driver if Higgsfield's avatar-speech API can't do
  script→talking-head programmatically.
- **SQLite over Postgres, BM25 over vector DB, no Redis/Docker** — single-operator,
  single-box system; every dropped dependency is one less thing that breaks at 2am.
- **Runtime models:** Haiku 4.5 classify / Sonnet 5 compose (API-key billing, not the Max
  subscription).
- **Compliance posture:** no automated cold-texting of scraped lists; consent basis
  required and recorded per contact; AI discloses itself when asked; staged autonomy
  (approval → guarded → full).
- **Skipped GHL/Ylopo features** (v1): white-label/multi-tenant, payments, courses,
  social planner, funnel builder, IDX portal, automated ad management — see plan §3.
