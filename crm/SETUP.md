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
   - Under **Webhooks**, add a new webhook:
     - URL: `http://localhost:4820/webhooks/bluebubbles`
     - Events: **New Message** and **Updated Message** (delivery/read receipts).
   - Leave the webhook secret field blank — BlueBubbles does not sign outgoing webhook
     requests, and the endpoint is `127.0.0.1`-only by design (see `crm/DECISIONS.md`).
4. Send yourself a test text from another phone and confirm it shows up in
   `crm/crm.db` (`npm run seed` already ran, so query the `messages` table, or just watch
   the server log — `npm run dev` prints an inbound row insert).

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
