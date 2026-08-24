#!/usr/bin/env bash
set -euo pipefail

CODEX_BIN="$(command -v codex || true)"
if [[ -z "$CODEX_BIN" ]]; then
  echo "codex not found on PATH. Install/authenticate Codex first." >&2
  exit 1
fi

WORKSPACE="${CODEX_HA_WORKSPACE:-$HOME/homeassistant-workspace}"
if [[ ! -d "$WORKSPACE" ]]; then
  echo "Workspace not found: $WORKSPACE" >&2
  exit 1
fi

BIN_DIR="$HOME/bin"
STARTER="$BIN_DIR/start-ha-codex"

if command -v xdg-user-dir >/dev/null 2>&1; then
  DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
else
  DESKTOP_DIR=""
fi
DESKTOP_DIR="${DESKTOP_DIR:-$HOME/Desktop}"
LAUNCHER="$DESKTOP_DIR/Home Assistant Codex.desktop"

mkdir -p "$BIN_DIR" "$DESKTOP_DIR"
chmod 700 "$BIN_DIR"

cat > "$STARTER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd '$WORKSPACE'
exec '$CODEX_BIN'
EOF
chmod 700 "$STARTER"

cat > "$LAUNCHER" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Home Assistant Codex
Comment=Start a fresh Codex session for Home Assistant
Icon=utilities-terminal
Exec=$STARTER
Path=$WORKSPACE
Terminal=true
Categories=Development;
StartupNotify=true
EOF
chmod +x "$LAUNCHER"

gio set "$LAUNCHER" metadata::trusted true 2>/dev/null || true

echo "Installed desktop launcher:"
echo "  $LAUNCHER"
echo
echo "Double-click it to start a fresh Codex session in:"
echo "  $WORKSPACE"
echo
echo "If GNOME marks it untrusted, right-click it once and choose Allow Launching."
