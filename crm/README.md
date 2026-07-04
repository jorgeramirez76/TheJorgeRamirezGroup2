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
