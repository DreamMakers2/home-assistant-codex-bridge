#!/usr/bin/env bash
set -euo pipefail

NPX="$(command -v npx || true)"
NODE="$(command -v node || true)"

if [[ -z "$NPX" || -z "$NODE" ]]; then
  echo "node/npx not found. Install Node.js first." >&2
  exit 1
fi

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "Run this installer from the logged-in Ubuntu graphical desktop session." >&2
  exit 1
fi

NODEBIN="$(dirname "$NODE")"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/playwright-mcp.service"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/playwright-mcp.desktop"
BIN_DIR="$HOME/bin"
STARTER="$BIN_DIR/start-playwright-mcp"
PROFILE="$HOME/.config/codex-ha/browser-profile"
MCP_PACKAGE="${PLAYWRIGHT_MCP_PACKAGE:-@playwright/mcp@latest}"

mkdir -p "$SERVICE_DIR" "$AUTOSTART_DIR" "$BIN_DIR" "$PROFILE"
chmod 700 "$BIN_DIR" "$HOME/.config/codex-ha" 2>/dev/null || true

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Visible Playwright MCP for Codex
After=graphical-session.target

[Service]
Type=simple
Environment=PATH=$NODEBIN:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$NPX -y $MCP_PACKAGE --port 8931 --browser=chrome --user-data-dir=%h/.config/codex-ha/browser-profile
Restart=always
RestartSec=3
EOF

cat > "$STARTER" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

for _ in {1..30}; do
  if [[ -n "${DISPLAY:-}" || -n "${WAYLAND_DISPLAY:-}" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  echo "No graphical DISPLAY or WAYLAND_DISPLAY is available." >&2
  exit 1
fi

VARS=(XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS)
if [[ -n "${DISPLAY:-}" ]]; then
  VARS+=(DISPLAY)
fi
if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
  VARS+=(WAYLAND_DISPLAY)
fi

systemctl --user import-environment "${VARS[@]}"
systemctl --user restart playwright-mcp.service
EOF
chmod 700 "$STARTER"

cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Playwright MCP
Comment=Start visible Playwright MCP after graphical login
Exec=$STARTER
Terminal=false
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF
chmod 600 "$AUTOSTART_FILE"

systemctl --user daemon-reload
systemctl --user disable playwright-mcp.service >/dev/null 2>&1 || true

"$STARTER"
sleep 3
systemctl --user --no-pager --full status playwright-mcp.service | head -20

echo
echo "Playwright MCP endpoint: http://localhost:8931/mcp"
echo "The graphical-login autostart entry restarts headed Playwright with the"
echo "real DISPLAY/Wayland environment after each login/reboot."
echo
echo "Configure Codex with:"
echo "  codex mcp remove playwright 2>/dev/null || true"
echo "  codex mcp add playwright --url http://localhost:8931/mcp"
echo
echo "For reproducible deployments, set PLAYWRIGHT_MCP_PACKAGE to a pinned"
echo "package version before running this installer."
