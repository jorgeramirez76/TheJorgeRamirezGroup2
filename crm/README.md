# JRG-CRM

Self-hosted real estate CRM for The Jorge Ramirez Group. The locked product spec is `MASTER_BUILD_PLAN.md`; implementation decisions/deviations are recorded in `DECISIONS.md`.

## Phase 1 commands

```bash
cd crm
npm install
npm run migrate
npm run seed
npm run dev
npm test
npm run build
```

The API defaults to `http://127.0.0.1:4820` and SQLite defaults to `crm/crm.db`.

## Phase 2 — iMessage channel

BlueBubbles driver, inbound webhook, send gate (suppressions/consent/quiet hours/caps/
pacing), STOP/opt-out flow, and the `launchd` service. Human-side Mac setup (Apple ID,
Text Message Forwarding, BlueBubbles install, no-sleep) is in `SETUP.md`.

## Phase 3 — Gmail channel

OAuth2 desktop flow (`npm run setup:gmail`), `users.history.list` inbound polling every 30s
with a persisted cursor (`settings.gmail_history_id`), threaded send (`In-Reply-To`/
`References`/Gmail `threadId`), the `/t.gif` open-tracking pixel, campaign-send throttling
(20s+ spacing, daily cap, CAN-SPAM footer) on top of the existing send gate, and the
iMessage→email channel-selection/fallback policy (§6.3). Google Cloud Console setup is in
`SETUP.md`.
