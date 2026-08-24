# Ubuntu runtime and desktop workflow

This page covers day-to-day startup after the environment has been bootstrapped.

## Desired behavior

```text
Ubuntu boots
   |
   v
human logs into graphical desktop as the Codex runtime user
   |
   +--> desktop autostart imports real DISPLAY/Wayland variables
   |    and starts/restarts headed Playwright MCP
   |
   +--> user launches "Home Assistant Codex"
        |
        v
     normal terminal
        |
        v
     fresh Codex session in ~/homeassistant-workspace
```

A fresh Codex session is preferred over automatically resuming an old interactive task.

## Desktop shortcut

Install:

```bash
chmod 700 client/install-codex-desktop-shortcut.sh
client/install-codex-desktop-shortcut.sh
```

Override the workspace if needed:

```bash
CODEX_HA_WORKSPACE=/path/to/workspace \
  client/install-codex-desktop-shortcut.sh
```

GNOME may require **Allow Launching** once.

## Headed Playwright MCP

Install from the logged-in graphical session:

```bash
chmod 700 client/install-playwright-service.sh
client/install-playwright-service.sh
```

The installer creates:

```text
~/.config/systemd/user/playwright-mcp.service
~/bin/start-playwright-mcp
~/.config/autostart/playwright-mcp.desktop
```

The graphical autostart helper imports the actual session environment into `systemd --user`, then restarts the service. This avoids the common post-reboot failure:

```text
Looks like you launched a headed browser without having a XServer running
```

Verify:

```bash
systemctl --user --no-pager --full status playwright-mcp.service
```

Expected:

```text
Active: active (running)
Listening on http://localhost:8931
```

Register with Codex:

```bash
codex mcp remove playwright 2>/dev/null || true
codex mcp add playwright --url http://localhost:8931/mcp
```

Use `localhost`, not `127.0.0.1`.

## Reproducible Playwright version

The installer defaults to `@playwright/mcp@latest` for convenience. For reproducibility, pin a version:

```bash
PLAYWRIGHT_MCP_PACKAGE='@playwright/mcp@<VERSION>' \
  client/install-playwright-service.sh
```

Record the chosen version in your private deployment notes, not in the public template unless it is intentionally the project-wide default.

## Safe smoke test

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

Run once immediately and once after a real Ubuntu reboot.

## Git metadata

The normal workflow expects Codex to stage and make local commits. The permission profile therefore includes:

```toml
[permissions.homeassistant.filesystem.":workspace_roots"]
"." = "write"
".git" = "write"
```

A `test -w .git` result is not sufficient proof under sandboxing. The practical proof is an explicitly authorized stage/commit of an intended non-secret change.

## Read-only credential exposure audit

A safe regression prompt:

```text
This is a read-only security audit of the Home Assistant Codex environment.

Read the local AGENTS.md first and follow it strictly.

Check whether any secret or credential value may have been accidentally exposed
through locations that Codex is legitimately allowed to read.

Do not make any changes.

Do not read protected secret stores, browser profiles, auth files, private
keys, backups, shell history or process environments. Do not try to infer,
recover, validate, test or reveal a secret value.

Inspect only normally readable project/config/log locations and the readable Git
working tree for signs of literal API keys/tokens, Authorization headers,
embedded passwords, private-key material, webhook secrets, credential-like query
parameters or suspicious high-entropy literals.

If something may be a real secret:
- do not display, quote, hash or transform it;
- report only the path and approximate location;
- describe the suspected exposure generically;
- redact the value completely as [REDACTED].

Report PASS/FAIL for readable configuration, readable logs and the Git working
tree, plus audit limitations. Do not fix anything.
```

If remediation is desired, authorize it separately after reviewing the finding.
