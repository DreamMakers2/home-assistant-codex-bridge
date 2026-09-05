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

GNOME may require **Allow Launching** once for each launcher.

The installer creates standard, **no approval**, and **yolo** launchers. All three apply the HA-specific context controls:

```text
model_auto_compact_token_limit=110000
model_auto_compact_token_limit_scope="total"
tool_output_token_limit=4000
agents.max_concurrent_threads_per_session=3
mcp_servers.playwright.default_tools_approval_mode=approve
```

The shared thread limit includes the root thread, so `3` allows the existing maximum of two concurrent subagents. The no-approval launcher additionally retains `workspace-write` isolation and pins `sandbox_workspace_write.network_access=true` so `ha-sync` can use HTTPS. The yolo launcher uses `--dangerously-bypass-approvals-and-sandbox`; use it only when the VM is an adequate external sandbox.

The token controls reduce retained tool-output/context replay; they do not remove the validation, visual QA, reviewer/improve/re-test, or final regression requirements in `AGENTS.md`.

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

Then merge the following into `~/.codex/config.toml`:

```toml
[mcp_servers.playwright]
url = "http://localhost:8931/mcp"
default_tools_approval_mode = "approve"
disabled_tools = ["browser_run_code_unsafe"]
```

Use `localhost`, not `127.0.0.1`.

## Reproducible Playwright version

The installer intentionally defaults to the project-pinned `@playwright/mcp@0.0.80` so browser tool schemas and output behavior do not change between runs without review. To deliberately test another version:

```bash
PLAYWRIGHT_MCP_PACKAGE='@playwright/mcp@<VERSION>' \
  client/install-playwright-service.sh
```

Update the project-wide pin only after validating the newer release; deployment-specific experiments can remain in private notes.

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
