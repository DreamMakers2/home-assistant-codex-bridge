# Setup and rebuild reference

For a new installation, start with [`FIRST_TIME_SETUP.md`](FIRST_TIME_SETUP.md).

This document is a compact checklist for auditing or rebuilding an existing deployment.

## Components

Home Assistant side:

```text
/config/packages/codex/
/config/.codex_access/
/addons/codex_file_bridge/
```

Ubuntu side:

```text
~/homeassistant-workspace/
~/bin/ha-sync
~/.config/codex-ha/env
~/.config/codex-ha/bridge-ca.crt
~/.config/codex-ha/browser-profile
~/.config/systemd/user/playwright-mcp.service
~/.config/autostart/playwright-mcp.desktop
~/.codex/rules/homeassistant.rules
~/.codex/config.toml
```

## Rebuild order

1. Establish VM isolation/firewall policy.
2. Install Ubuntu base packages, Chrome and Node.
3. Create Home Assistant package directory.
4. Generate alias-only `SECRET_NAMES.md`.
5. Install protected bridge path policy.
6. Install/configure the local bridge app.
7. Generate bridge token outside ChatGPT/Codex.
8. Pin bridge TLS certificate.
9. Install/test `ha-sync`.
10. Create dedicated Home Assistant browser user.
11. Configure browser login (manual profile or exact-IP trusted login).
12. Install/authenticate Codex.
13. Install headed Playwright MCP.
14. Install local `AGENTS.md`, exec rules and permission profile.
15. Pull baseline Home Assistant files and initialize local Git.
16. Install desktop shortcut.
17. Run non-destructive smoke test.
18. Reboot and repeat smoke test.
19. Run periodic secret-exposure audit.

## Must-pass bridge tests

```text
configuration.yaml -> HTTP 200
secrets.yaml       -> HTTP 403
```

## Must-pass Codex tests

```text
AGENTS.md readable
ha-sync works
Codex auth file denied
browser profile denied
sudo forbidden
.git writable for authorized local commits
```

## Must-pass browser tests

```text
Playwright headed
Home Assistant loads
required dashboard/dev-tools pages accessible
reboot/login restores headed Playwright
```

## Important local-only values

Do not publish:

```text
real HA IP/URL
real Codex VM IP
Home Assistant trusted user ID
bridge token
Home Assistant passwords/tokens
OpenAI credentials
browser profile/session data
SECRET_NAMES.md
```

The public repository should remain generic; deployment-specific facts belong in private/local notes and the customized local `AGENTS.md`.
