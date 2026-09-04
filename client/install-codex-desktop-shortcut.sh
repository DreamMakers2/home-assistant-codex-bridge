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
NO_APPROVAL_STARTER="$BIN_DIR/start-ha-codex-no-approval"
YOLO_STARTER="$BIN_DIR/start-ha-codex-yolo"

if command -v xdg-user-dir >/dev/null 2>&1; then
  DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
else
  DESKTOP_DIR=""
fi
DESKTOP_DIR="${DESKTOP_DIR:-$HOME/Desktop}"
LAUNCHER="$DESKTOP_DIR/Home Assistant Codex.desktop"
NO_APPROVAL_LAUNCHER="$DESKTOP_DIR/Home Assistant Codex (no approval).desktop"
YOLO_LAUNCHER="$DESKTOP_DIR/Home Assistant Codex (yolo).desktop"

mkdir -p "$BIN_DIR" "$DESKTOP_DIR"
chmod 700 "$BIN_DIR"

cat > "$STARTER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd '$WORKSPACE'
exec '$CODEX_BIN' -c mcp_servers.playwright.default_tools_approval_mode=approve
EOF

cat > "$NO_APPROVAL_STARTER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd '$WORKSPACE'
exec '$CODEX_BIN' --sandbox workspace-write --ask-for-approval never -c sandbox_workspace_write.network_access=true -c mcp_servers.playwright.default_tools_approval_mode=approve
EOF

cat > "$YOLO_STARTER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd '$WORKSPACE'
exec '$CODEX_BIN' --dangerously-bypass-approvals-and-sandbox -c mcp_servers.playwright.default_tools_approval_mode=approve
EOF

chmod 700 "$STARTER" "$NO_APPROVAL_STARTER" "$YOLO_STARTER"

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

cat > "$NO_APPROVAL_LAUNCHER" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Home Assistant Codex (no approval)
Comment=Start Codex without prompts, retaining workspace isolation and HTTPS access
Icon=utilities-terminal
Exec=$NO_APPROVAL_STARTER
Path=$WORKSPACE
Terminal=true
Categories=Development;
StartupNotify=true
EOF

cat > "$YOLO_LAUNCHER" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Home Assistant Codex (yolo)
Comment=Start Codex without sandboxing or approval prompts
Icon=utilities-terminal
Exec=$YOLO_STARTER
Path=$WORKSPACE
Terminal=true
Categories=Development;
StartupNotify=true
EOF

chmod +x "$LAUNCHER" "$NO_APPROVAL_LAUNCHER" "$YOLO_LAUNCHER"

gio set "$LAUNCHER" metadata::trusted true 2>/dev/null || true
gio set "$NO_APPROVAL_LAUNCHER" metadata::trusted true 2>/dev/null || true
gio set "$YOLO_LAUNCHER" metadata::trusted true 2>/dev/null || true

echo "Installed desktop launcher:"
echo "  $LAUNCHER"
echo "  $NO_APPROVAL_LAUNCHER"
echo "  $YOLO_LAUNCHER"
echo
echo "Double-click it to start a fresh Codex session in:"
echo "  $WORKSPACE"
echo
echo "If GNOME marks it untrusted, right-click it once and choose Allow Launching."
echo
echo "WARNING: The yolo launcher disables the Codex sandbox and approval prompts."
