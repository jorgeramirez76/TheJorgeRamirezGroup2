# JRG-CRM — Human Setup

Steps only Jorge can do by hand, on the Mac Studio that runs the CRM 24/7. Do these once,
in order, before Phase 2's iMessage channel can send or receive for real.

## 1. Sign the Mac into Jorge's Apple ID

1. **System Settings → Apple ID** (or "Sign in with Apple ID" at the top of System Settings)
   → sign in with the same Apple ID/phone number Jorge uses on his iPhone.
2. **System Settings → Apple ID → iMessage** (or the **Messages** app → Settings →
   iMessage) → make sure iMessage is turned **on** and signed in with that same account.
3. Open **Messages.app** at least once and confirm it shows the same conversation history
   Jorge sees on his phone. This proves the Mac is fully synced before BlueBubbles touches it.

## 2. Turn on Text Message Forwarding (this is what makes texts send from Jorge's real number)

On **Jorge's iPhone**:
1. **Settings → Messages → Text Message Forwarding**.
2. Enable the toggle for **this Mac Studio** (it will appear by name once step 1 is done).
3. A 6-digit code appears on the iPhone — enter it in the popup that appears on the Mac.
4. Send yourself a test SMS/iMessage from another phone and confirm it appears in
   Messages.app on the Mac within a few seconds.

Without this step, green-bubble (SMS) replies from non-iPhone leads will never reach the Mac.

## 3. Install and configure BlueBubbles Server

1. Download the BlueBubbles **Server** app for macOS: https://bluebubbles.app/downloads/
   (Server, not Client — the Mac Studio is the server).
2. Open it, grant the Full Disk Access + Accessibility + Automation permissions it asks for
   (it needs these to read `chat.db` and drive Messages.app via AppleScript).
3. In BlueBubbles Server settings:
   - Set a **server password** — put the same value in `crm/.env` as `BLUEBUBBLES_PASSWORD`.
   - Confirm the server's local port (default `1234`) matches `BLUEBUBBLES_BASE_URL` in
     `crm/.env` (default `http://localhost:1234`).
   - Leave the webhook secret field blank — BlueBubbles does not sign outgoing webhook
     requests, and the endpoint is `127.0.0.1`-only by design (see `crm/DECISIONS.md`).
4. **Register the webhook — a fresh install has none, this is not optional.** Go to
   **API & Webhooks → Manage → Add Webhook** and enter:
   - URL: **`http://127.0.0.1:4820/webhooks/bluebubbles`** — use the literal IP, not
     `localhost`. On macOS `localhost` can resolve to `::1` (IPv6) first; the CRM server
     only listens on IPv4, so BlueBubbles' webhook dispatcher fails silently against
     `localhost` (logs `Status Text: undefined`) instead of falling back like `curl` does.
   - Events: **New Message** and **Updated Message** (or "All Events").
   - Confirm it saved: `curl -s "http://localhost:1234/api/v1/webhook?password=<BLUEBUBBLES_PASSWORD>"`
     should return your webhook in `data`, not `[]`.
5. Send yourself a test text from another phone **after** finishing this whole section
   (BlueBubbles' new-message detection appears to key off "since this server session
   started" — a message sent before you last opened/restarted BlueBubbles Server won't
   retroactively fire the webhook even though it's visible in Messages.app). Confirm it
   shows up in `crm/crm.db` (`sqlite3 crm/crm.db "select * from messages order by id desc
   limit 5;"`, or watch `crm/logs/server.out.log` for an incoming `POST /webhooks/bluebubbles`).
   Detection is not instant without the Private API (see the note at the end of this file) —
   give it a minute or two before assuming it's broken.

## 4. Disable Mac sleep (the server must run 24/7)

1. **System Settings → Lock Screen** → set "Turn display off" to whatever you like, but
   set **"Start Screen Saver when inactive"** aside — the concern is *sleep*, not the display.
2. **System Settings → Energy** (Mac Studio, desktop power settings):
   - "Prevent automatic sleeping when the display is off" → **on**.
   - "Wake for network access" → **on**.
3. Belt-and-suspenders: run `sudo pmset -a sleep 0 disksleep 0` once, or add
   `caffeinate -dimsu &` to a login item. The launchd install script (below) does not
   itself prevent sleep — it only keeps the *process* alive across crashes/reboots.

## 5. Install the CRM server as a launchd service

Once `crm/.env` is filled in (`BLUEBUBBLES_BASE_URL`, `BLUEBUBBLES_PASSWORD`, and the rest
of `.env.example`):

```bash
cd crm
npm install
npm run migrate
npm run seed        # safe to skip on a real (non-empty) database — it no-ops past the first run
npm run launchd:install
```

This builds the server, writes `~/Library/LaunchAgents/com.jrgcrm.server.plist`, and loads
it with `launchctl`. It restarts automatically on crash and on every login/reboot.

- Check it's running: `launchctl list | grep com.jrgcrm.server`
- Logs: `crm/logs/server.out.log` and `crm/logs/server.err.log`
- Restart after a config change: `launchctl kickstart -k gui/$(id -u)/com.jrgcrm.server`
- Uninstall: `launchctl unload ~/Library/LaunchAgents/com.jrgcrm.server.plist && rm ~/Library/LaunchAgents/com.jrgcrm.server.plist`

## 6. Verify the whole loop once, for real

1. Text the Mac's forwarded number "hi" from a second phone (not suppressed, ideally a
   contact you've added with `consent_sms: true`).
2. Confirm it lands in `messages` within ~2 seconds (`sqlite3 crm/crm.db "select * from
   messages order by id desc limit 5;"`).
3. Text "STOP" from that same phone. Confirm: the contact's `do_not_contact` flips to 1, a
   single confirmation message row is queued, and a second "STOP" doesn't queue a second one.
4. Watch `settings.imessage_health` stay `{"ok": true, ...}` while BlueBubbles is running;
   quit BlueBubbles Server for 5+ minutes and confirm it flips to `{"ok": false, ...}` and an
   `audit_log` alert row appears.

If all four check out, Phase 2 is live end-to-end on real hardware.

## 7. Gmail (Phase 3) — Google Cloud Console + OAuth

Do this once, before `npm run setup:gmail`. It creates the OAuth client the CRM uses to send
and read Jorge's real Gmail as himself (not a service account, not "less secure apps").

1. **Create/select a Google Cloud project.** Go to
   https://console.cloud.google.com/projectcreate, sign in as **jorgeramirez76@gmail.com**
   (the account the CRM sends from), and create a project (e.g. "jrg-crm"). Any existing
   project Jorge already owns works too.
2. **Enable the Gmail API.** In that project: **APIs & Services → Library** → search
   "Gmail API" → **Enable**.
3. **Configure the OAuth consent screen.** **APIs & Services → OAuth consent screen**:
   - User type: **External** (Jorge's Gmail is a personal @gmail.com account, not Workspace).
   - App name: anything internal, e.g. "JRG CRM". Support email: jorgeramirez76@gmail.com.
   - Scopes: add `.../auth/gmail.modify` and `.../auth/gmail.send`.
   - **Test users:** add **jorgeramirez76@gmail.com**. While the app is in "Testing"
     publishing status (the default, and fine for this single-user CRM), only accounts
     listed here can complete the consent screen — refresh tokens for test users also don't
     expire after 7 days the way they otherwise would for unpublished apps.
4. **Create OAuth client credentials.** **APIs & Services → Credentials → Create Credentials
   → OAuth client ID**:
   - Application type: **Desktop app** (not "Web application" — this is a local CLI flow,
     no public redirect endpoint).
   - Name: anything, e.g. "jrg-crm-desktop".
   - After creation, copy the **Client ID** and **Client secret**.
5. **Fill in `crm/.env`:**
   ```
   GOOGLE_CLIENT_ID=<the client ID>.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=<the client secret>
   GOOGLE_REDIRECT_URI=http://localhost:4820/oauth/google/callback
   ```
   `GOOGLE_REDIRECT_URI` must stay a `localhost`/`127.0.0.1` address — `npm run setup:gmail`
   starts its own temporary local listener on this exact port+path to catch the redirect; it
   does not need to be reachable from anywhere but this Mac, and does **not** need to be
   registered in Cloud Console (Desktop-app OAuth clients accept any loopback redirect).
6. **Run the interactive setup:**
   ```bash
   cd crm
   npm run setup:gmail
   ```
   It prints a Google consent URL — open it in a browser signed into
   **jorgeramirez76@gmail.com**, approve the two Gmail scopes, and the CLI catches the
   redirect automatically and prints "Gmail connected as jorgeramirez76@gmail.com." It writes
   `GMAIL_REFRESH_TOKEN` and `GMAIL_FROM` into `crm/.env` for you — nothing to copy by hand.
7. **Restart the CRM server** (`launchctl kickstart -k gui/$(id -u)/com.jrgcrm.server`, or
   `npm run dev` in a foreground session) so it picks up the new `.env` values. Logs should
   stop warning about missing `GOOGLE_CLIENT_ID`/`GMAIL_REFRESH_TOKEN`, and the poller starts
   checking `users.history.list` every 30 seconds.
8. **Verify:**
   - Send yourself a test email addressed to a seeded/known contact's email address (or reply
     to one the CRM sent) and confirm it lands in `messages` within ~30s
     (`sqlite3 crm/crm.db "select * from messages where channel='email' order by id desc limit 5;"`).
   - Confirm `settings.gmail_history_id` is set and changes over time:
     `sqlite3 crm/crm.db "select value from settings where key='gmail_history_id';"`.
   - If you ever need to re-authorize (e.g. rotated credentials), first revoke prior access at
     https://myaccount.google.com/permissions, then re-run `npm run setup:gmail` — Google only
     issues a fresh `refresh_token` when consent is granted anew.

## Note: instant detection needs the Private API (optional, real trade-off)

Without BlueBubbles' **Private API** enabled (Settings → Private API — requires SIP disabled
via Recovery Mode), new-message detection runs on an internal polling cadence rather than
instant FSEvents-driven push, so the "<2 second" target in §6.1 of the master plan won't be
met — expect anywhere from several seconds to a couple minutes. It still works correctly
(verified end-to-end: a message sent, detected, webhook-dispatched, and landed in `crm.db`
with a correctly-flagged `needs-review` shell contact), just not at target latency. Disabling
SIP is a real macOS security trade-off — don't do this without deciding it's worth it
first; it's not required for Phase 2 to function.
