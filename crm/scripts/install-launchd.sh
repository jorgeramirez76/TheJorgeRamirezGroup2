#!/usr/bin/env bash
# Installs and loads the JRG-CRM server as a launchd user agent so it survives logout/reboot
# and auto-restarts on crash. Re-run any time after `npm install` to rebuild + reload.
set -euo pipefail

CRM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.jrgcrm.server"
TEMPLATE="$CRM_DIR/ops/launchd/$LABEL.plist.template"
PLIST_DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
NODE_BIN="$(command -v node || true)"

if [ -z "$NODE_BIN" ]; then
  echo "node not found on PATH — install Node 22 first (see crm/SETUP.md)." >&2
  exit 1
fi

if [ ! -f "$TEMPLATE" ]; then
  echo "Missing plist template at $TEMPLATE" >&2
  exit 1
fi

echo "Building crm server ($CRM_DIR)..."
(cd "$CRM_DIR" && npm run build)

mkdir -p "$CRM_DIR/logs"
mkdir -p "$HOME/Library/LaunchAgents"

sed -e "s#__NODE_BIN__#$NODE_BIN#g" -e "s#__WORKDIR__#$CRM_DIR#g" "$TEMPLATE" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load -w "$PLIST_DEST"

echo "Installed and loaded $LABEL from $PLIST_DEST"
echo "Logs:         $CRM_DIR/logs/server.out.log , $CRM_DIR/logs/server.err.log"
echo "Check status: launchctl list | grep $LABEL"
echo "Restart:      launchctl kickstart -k gui/$(id -u)/$LABEL"
echo "Uninstall:    launchctl unload \"$PLIST_DEST\" && rm \"$PLIST_DEST\""
