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
