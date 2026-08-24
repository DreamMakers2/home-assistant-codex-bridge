# First-time setup from zero

This guide builds Home Assistant Codex Bridge from a fresh Ubuntu **desktop** VM and an existing Home Assistant OS installation.

Privileged bootstrap steps are performed by a human administrator. After setup, Codex operates through the restricted file bridge, Playwright, its local workspace, and the configured sandbox/exec-policy.

## 1. Choose local values

Do not commit the real values below to a public fork unless you intentionally want them public.

Record locally:

```text
HA_HOST=<Home Assistant LAN IP or hostname>
HA_URL=<full Home Assistant URL, including port if needed>
CODEX_VM_IP=<fixed/reserved Ubuntu VM IP>
CODEX_USER=codex
WORKSPACE=$HOME/homeassistant-workspace
```

Example documentation-only addresses:

```text
HA_HOST=192.0.2.10
CODEX_VM_IP=192.0.2.20
```

`192.0.2.0/24` is reserved for documentation. Replace it with your real network.

## 2. Security decisions before installation

Recommended design:

```text
Codex VM -> Home Assistant UI port    ALLOW
Codex VM -> Home Assistant TCP 8443  ALLOW
Codex VM -> Internet                 ALLOW
Codex VM -> SSH / unrelated LAN      DENY
```

Also:

- do not give Codex HAOS root/SSH credentials;
- do not expose bridge TCP 8443 to the Internet;
- use a fixed/reserved VM IP if you plan to use Home Assistant `trusted_networks`;
- use a dedicated Ubuntu runtime account;
- ideally keep the `codex` runtime account non-sudo after bootstrap;
- keep OS administration on a separate human-admin account;
- never put secret values, tokens, user IDs or browser cookies into prompts or Git.

## 3. Ubuntu sizing

A practical minimum:

```text
CPU:   2+ vCPU
RAM:   4+ GiB
Disk:  30+ GiB
GUI:   Ubuntu desktop session required for headed browser testing
```

ESPHome compilation and multiple browser tabs benefit from more RAM/CPU.

## 4. Prepare Ubuntu

Run as the human administrator:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  openssl \
  python3 \
  wget
```

### Install Chrome

For `amd64` Ubuntu:

```bash
wget -O /tmp/google-chrome-stable_current_amd64.deb \
  https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y /tmp/google-chrome-stable_current_amd64.deb
rm -f /tmp/google-chrome-stable_current_amd64.deb
google-chrome --version
```

If your architecture differs, use a browser supported by Playwright MCP and adjust the service command.

### Install Node.js

One option is NVM:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nvm install 24
nvm alias default 24
nvm use 24

node --version
npm --version
npx --version
```

Versions change. Check current upstream requirements when rebuilding.

### Create runtime directories

As the Codex runtime user:

```bash
mkdir -p \
  "$HOME/bin" \
  "$HOME/.config/codex-ha" \
  "$HOME/homeassistant-workspace"

chmod 700 \
  "$HOME/bin" \
  "$HOME/.config/codex-ha" \
  "$HOME/homeassistant-workspace"

if ! grep -Fq 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc"; then
  printf '\nexport PATH="$HOME/bin:$PATH"\n' >> "$HOME/.bashrc"
fi

export PATH="$HOME/bin:$PATH"
```

## 5. Prepare Home Assistant packages

The recommended setup uses:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

If `configuration.yaml` already has a `homeassistant:` block, merge the `packages:` line into it. Do not create a duplicate top-level key.

Create:

```sh
mkdir -p /config/packages/codex
```

Codex-owned Home Assistant package logic should normally live under:

```text
/config/packages/codex/
```

## 6. Create the alias-only secret index

Codex may know secret **alias names**, never secret values.

Run manually on Home Assistant:

```sh
(
  printf '# Available Home Assistant secret aliases\n\n'
  awk -F: '/^[A-Za-z0-9_-]+:/ {print "- `" $1 "`"}' /config/secrets.yaml

  if [ -f /config/esphome/secrets.yaml ]; then
    printf '\n# Available ESPHome secret aliases\n\n'
    awk -F: '/^[A-Za-z0-9_-]+:/ {print "- `" $1 "`"}' /config/esphome/secrets.yaml
  fi
) > /config/packages/codex/SECRET_NAMES.md

chmod 600 /config/packages/codex/SECRET_NAMES.md
```

Inspect it manually. It must contain names only.

`SECRET_NAMES.md` is ignored by this repository and should not be committed.

## 7. Install the HA-side policy

Create:

```sh
mkdir -p /config/.codex_access
chmod 755 /config/.codex_access
```

Use the repository files under `policy/`, or create these exact contents.

### `READ_WRITE.txt`

```text
/homeassistant/automations.yaml
/homeassistant/scripts.yaml
/homeassistant/scenes.yaml
/homeassistant/themes.yaml
/homeassistant/themes/**
/homeassistant/packages/codex/**
/homeassistant/esphome/*.yaml
/homeassistant/esphome/**/*.yaml
```

### `READ_ONLY.txt`

```text
/homeassistant/configuration.yaml
/homeassistant/packages/**
/homeassistant/custom_components/**
/homeassistant/www/community/**
/homeassistant/home-assistant.log*
```

### `DENY.txt`

```text
**/secrets.yaml
/homeassistant/.storage/**
/homeassistant/*.db*
/homeassistant/backups/**
**/.ssh/**
**/*.key
**/*.pem
```

Then:

```sh
chmod 644 /config/.codex_access/*.txt
```

The policy directory must remain outside Codex-writable package paths.

`DENY` has precedence.

## 8. Install the local Home Assistant app

Copy these repository files to:

```text
/addons/codex_file_bridge/
```

Files:

```text
addon/config.yaml
addon/Dockerfile
addon/run.sh
addon/server.py
```

Refresh the Home Assistant local app/add-on store and install **Home Assistant Codex Bridge**.

### Configure TLS names

The app options include:

```text
api_token
tls_san_ip
tls_san_dns
```

Set:

- `tls_san_ip` to the Home Assistant IP used by the Ubuntu bridge client, or leave blank if the client will use DNS only;
- `tls_san_dns` to a comma-separated list of DNS names clients may use.

Default DNS values:

```text
homeassistant,homeassistant.local
```

The bridge regenerates its self-signed certificate when the configured SAN value changes. If that happens, re-pin the certificate on Ubuntu before using `ha-sync` again.

## 9. Create the bridge bearer token

Generate it manually outside ChatGPT/Codex:

```sh
cat /proc/sys/kernel/random/uuid /proc/sys/kernel/random/uuid | tr -d '\n-'
echo
```

Enter the resulting 64-character value into the app's `api_token` option.

Do not commit it or paste it into chat.

Start the app. Its log should show:

```text
Home Assistant Codex Bridge listening on HTTPS port 8443
```

and a TLS SHA-256 fingerprint.

## 10. Bootstrap TLS trust on Ubuntu

Replace `<HA_HOST>` locally.

Initial connectivity test only:

```bash
curl -k "https://<HA_HOST>:8443/health"
```

Then capture the certificate:

```bash
openssl s_client \
  -connect '<HA_HOST>:8443' \
  -servername '<HA_HOST>' \
  </dev/null 2>/dev/null \
| openssl x509 -outform PEM \
> "$HOME/.config/codex-ha/bridge-ca.crt"

chmod 600 "$HOME/.config/codex-ha/bridge-ca.crt"

openssl x509 \
  -in "$HOME/.config/codex-ha/bridge-ca.crt" \
  -noout -fingerprint -sha256
```

Compare the fingerprint with the bridge app log. They must match.

Do not use `curl -k` for normal operation.

## 11. Store the bridge client environment

Enter the token without shell-history exposure:

```bash
read -rsp "Bridge bearer token: " CODEX_HA_BRIDGE_TOKEN
echo
```

Then:

```bash
read -rp "Bridge URL (example https://192.0.2.10:8443): " CODEX_HA_BRIDGE_URL

umask 077
{
  printf 'export CODEX_HA_BRIDGE_URL=%q\n' "$CODEX_HA_BRIDGE_URL"
  printf 'export CODEX_HA_BRIDGE_TOKEN=%q\n' "$CODEX_HA_BRIDGE_TOKEN"
} > "$HOME/.config/codex-ha/env"

unset CODEX_HA_BRIDGE_TOKEN CODEX_HA_BRIDGE_URL
chmod 600 "$HOME/.config/codex-ha/env"
```

Do not print the file afterward.

## 12. Install `ha-sync`

Copy `client/ha-sync` to:

```text
~/bin/ha-sync
```

Then:

```bash
chmod 700 "$HOME/bin/ha-sync"
export PATH="$HOME/bin:$PATH"
ha-sync --help
```

## 13. Prove the bridge boundary

First test the helper:

```bash
ha-sync ls /homeassistant
ha-sync pull /homeassistant/configuration.yaml
```

Then manually verify a denied secret read using the raw API if desired. Load the bridge env locally:

```bash
source "$HOME/.config/codex-ha/env"
```

Allowed:

```bash
curl --cacert "$HOME/.config/codex-ha/bridge-ca.crt" \
  -H "Authorization: Bearer $CODEX_HA_BRIDGE_TOKEN" \
  -o /tmp/ha-config-test.yaml \
  -w 'configuration.yaml: HTTP %{http_code}\n' \
  "$CODEX_HA_BRIDGE_URL/file?path=/homeassistant/configuration.yaml"
```

Denied:

```bash
curl --cacert "$HOME/.config/codex-ha/bridge-ca.crt" \
  -H "Authorization: Bearer $CODEX_HA_BRIDGE_TOKEN" \
  -o /tmp/ha-secret-test \
  -w 'secrets.yaml: HTTP %{http_code}\n' \
  "$CODEX_HA_BRIDGE_URL/file?path=/homeassistant/secrets.yaml"
```

Expected:

```text
configuration.yaml: HTTP 200
secrets.yaml:       HTTP 403
```

Cleanup:

```bash
rm -f /tmp/ha-config-test.yaml /tmp/ha-secret-test
unset CODEX_HA_BRIDGE_TOKEN CODEX_HA_BRIDGE_URL
```

If the secret read ever returns `200`, stop and fix the HA-side policy before continuing.

## 14. Create a dedicated Home Assistant browser user

Create a dedicated user for browser automation. Give it only the permissions required by your intended workflow.

For workflows involving dashboard editing, HACS, ESPHome Device Builder and Developer Tools, Administrator privileges may be required.

Do not reuse the personal Home Assistant owner account.

### Browser authentication option A: manual one-time login

This is the simpler security model:

1. start Chrome/Playwright with the dedicated profile;
2. manually log into Home Assistant as the dedicated user;
3. let the protected browser profile retain the session;
4. never give Codex the password.

### Browser authentication option B: exact-IP trusted login

For unattended login, Home Assistant's `trusted_networks` provider can map the fixed VM IP to the dedicated user.

Example only:

```yaml
homeassistant:
  packages: !include_dir_named packages
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - <CODEX_VM_IP>/32
      trusted_users:
        <CODEX_VM_IP>:
          - <CODEX_HA_USER_ID>
      allow_bypass_login: true

    - type: homeassistant
```

Important:

- use the exact VM `/32`, not the whole VLAN;
- map only to the dedicated user;
- keep the `homeassistant` auth provider as fallback;
- keep provider order correct;
- never commit the real user ID;
- do not overlap a network used as a `trusted_proxy`;
- validate configuration before restarting;
- keep the VM/firewall isolated because source-IP trust is powerful.

Check current Home Assistant authentication documentation before applying this option.

## 15. Install Codex CLI

Use the current official Codex installation guidance. One supported standalone path has been:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Then:

```bash
codex --version
```

If authenticating with an API key, avoid shell history:

```bash
read -rsp "OpenAI API key: " OPENAI_API_KEY
echo
printf '%s\n' "$OPENAI_API_KEY" | codex login --with-api-key
unset OPENAI_API_KEY
codex login status
```

Never save the key in the Home Assistant workspace.

## 16. Install headed Playwright MCP

From the logged-in graphical Ubuntu desktop:

```bash
chmod 700 client/install-playwright-service.sh
client/install-playwright-service.sh
```

Then:

```bash
codex mcp remove playwright 2>/dev/null || true
codex mcp add playwright --url http://localhost:8931/mcp
codex mcp list
```

Use `localhost`, not `127.0.0.1`.

The installer creates a graphical-login autostart entry so headed Playwright receives the actual display/session environment after reboot.

For reproducibility, set a pinned package version before installation:

```bash
PLAYWRIGHT_MCP_PACKAGE='@playwright/mcp@<VERSION>' \
  client/install-playwright-service.sh
```

## 17. Install the Codex operating contract

Copy:

```text
codex/AGENTS.md
```

to:

```text
~/homeassistant-workspace/AGENTS.md
```

Edit the local copy and replace:

```text
<HA_URL>
```

with the actual Home Assistant URL.

Do not commit that local customized copy back to a public template repository if it contains private deployment information.

## 18. Install exec-policy rules

Copy:

```text
codex/homeassistant.rules
```

to:

```text
~/.codex/rules/homeassistant.rules
```

Verify intent:

```bash
codex execpolicy check --pretty \
  --rules "$HOME/.codex/rules/homeassistant.rules" -- sudo id

codex execpolicy check --pretty \
  --rules "$HOME/.codex/rules/homeassistant.rules" -- \
  ha-sync pull /homeassistant/configuration.yaml
```

Expected:

```text
sudo    -> forbidden
ha-sync -> allow
```

Codex configuration syntax evolves; re-check against your installed CLI version.

## 19. Configure the Codex permission profile

Merge `codex/config.example.toml` into:

```text
~/.codex/config.toml
```

Do not overwrite unrelated model/MCP settings.

The template:

- denies Codex auth data;
- denies browser profile data;
- permits only the narrow bridge helper/config it needs;
- permits workspace files;
- explicitly permits `.git` metadata so local commits work;
- keeps secret-bearing workspace paths denied.

Restart Codex after permission changes.

## 20. Initialize local Git

From the workspace:

```bash
cd "$HOME/homeassistant-workspace"

ha-sync pull /homeassistant/configuration.yaml
ha-sync pull /homeassistant/automations.yaml
ha-sync pull /homeassistant/scripts.yaml
ha-sync pull /homeassistant/scenes.yaml
ha-sync pull /homeassistant/themes
ha-sync pull /homeassistant/packages
ha-sync pull /homeassistant/esphome
```

Use the repository `.gitignore` as a baseline, then:

```bash
git init
git branch -m main
git config user.name "Codex HA"
git config user.email "codex@localhost"
git add .
git commit -m "Baseline Home Assistant configuration"
git status
```

No remote is required.

Git rollback does not cover Home Assistant `.storage`, and this design intentionally denies `.storage`. Storage-mode Lovelace edits therefore require a separate export/versioning strategy if full dashboard rollback is important.

## 21. Install the desktop launcher

From the graphical desktop:

```bash
chmod 700 client/install-codex-desktop-shortcut.sh
client/install-codex-desktop-shortcut.sh
```

This creates **Home Assistant Codex** on the Ubuntu desktop. It starts a fresh Codex session in the workspace.

## 22. Firewall verification

Verify the intended outcome from the VM:

```text
Home Assistant UI:     reachable
Bridge TCP 8443:       reachable
HA SSH TCP 22:         blocked
Internet HTTPS:        reachable
Unrelated LAN access:  blocked according to policy
```

Do not open additional LAN access just because an application-level login fails.

## 23. Final non-destructive smoke test

Launch Codex from the workspace and use:

```text
Read the local AGENTS.md and confirm you are in the Home Assistant workspace.

Do not make any changes.

Then:
1. run git status
2. use ha-sync to confirm /homeassistant/configuration.yaml is readable
3. use Playwright to open Home Assistant
4. confirm the dashboard loads
5. report PASS/FAIL for each check

Do not restart Home Assistant, flash ESPHome, install/update HACS, or modify anything.
```

After it passes, reboot Ubuntu once and repeat the same test.

## 24. Security regression tests

Periodically verify:

```text
configuration.yaml via bridge    readable
secrets.yaml via bridge          denied
Codex auth file                  denied to sandboxed commands
browser profile                  denied to sandboxed commands
sudo                             forbidden
HA SSH                           blocked by network
Playwright                       headed and functional after reboot
local Git metadata               writable
```

See `docs/SECURITY.md` and `docs/UBUNTU_RUNTIME.md`.
