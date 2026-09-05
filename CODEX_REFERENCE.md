# Codex runtime reference

This file is the concise, prompt-facing reference for **Home Assistant Codex Bridge**.

It intentionally contains no live deployment IPs, user IDs, tokens, secret aliases or private hostnames. The local workspace `AGENTS.md` is the active runtime contract and should be customized with local endpoints during installation.

## Mission

Use Codex to maintain Home Assistant through a least-privilege Ubuntu workspace while preserving these boundaries:

- no Home Assistant or ESPHome secret values;
- no HAOS/root/SSH access;
- no `.storage`, databases or backups;
- no direct shell access to browser session data;
- Home Assistant file access through `ha-sync`;
- Home Assistant UI interaction through Playwright;
- task-scoped authorization for normal iterations;
- explicit gating for high-impact operations unless the current task pre-authorizes them.

## Local runtime

Recommended defaults:

```text
Ubuntu runtime user:   codex
Workspace:             ~/homeassistant-workspace
Local HA mirror:       ~/homeassistant-workspace/homeassistant
Playwright MCP:        http://localhost:8931/mcp
Bridge client config:  ~/.config/codex-ha/
```

Deployment-specific values are stored locally, not in this repository:

```text
Home Assistant URL:    <HA_URL>
Bridge URL:            https://<HA_HOST>:8443
Codex VM fixed IP:     <CODEX_VM_IP>
```

## File transport

Use `ha-sync` for Home Assistant filesystem work.

```bash
ha-sync ls /homeassistant
ha-sync pull /homeassistant/configuration.yaml
ha-sync pull /homeassistant/packages
ha-sync pull /homeassistant/esphome
ha-sync push "$HOME/homeassistant-workspace/homeassistant/packages/codex/example.yaml"
ha-sync delete /homeassistant/packages/codex/example.yaml
ha-sync mkdir /homeassistant/packages/codex/example_dir
```

Do not bypass bridge policy or use SSH/SCP/SFTP as an alternative.

## Default HA-side file policy

Read/write:

```text
/homeassistant/automations.yaml
/homeassistant/scripts.yaml
/homeassistant/scenes.yaml
/homeassistant/themes.yaml
/homeassistant/themes/**
/homeassistant/packages/codex/**
/homeassistant/packages/statistics_data.yaml
/homeassistant/esphome/*.yaml
/homeassistant/esphome/**/*.yaml
```

Read-only:

```text
/homeassistant/configuration.yaml
/homeassistant/packages/**
/homeassistant/custom_components/**
/homeassistant/www/community/**
/homeassistant/home-assistant.log*
```

Explicit deny:

```text
**/secrets.yaml
/homeassistant/.storage/**
/homeassistant/*.db*
/homeassistant/backups/**
**/.ssh/**
**/*.key
**/*.pem
```

`DENY` wins over all allow rules.

## Secret handling

Codex may use secret alias names from the locally generated:

```text
/homeassistant/packages/codex/SECRET_NAMES.md
```

It must never read, infer, recover, validate, test or reveal the values.

If a needed alias does not exist, Codex should tell the user which alias to add manually outside Codex/ChatGPT.

## UI capability

The design can use a dedicated Home Assistant browser user for:

- Lovelace view/edit;
- Developer Tools;
- states/history;
- configuration validation and safe reloads;
- HACS inspection/use of already-installed frontend cards;
- ESPHome Device Builder;
- functional and visual testing.

A browser Administrator account is intentionally more privileged than the file bridge. UI approval rules therefore remain important.

## Task-scoped authorization

Normal work within an explicitly authorized task may proceed autonomously through repeated:

```text
inspect -> edit -> validate -> push/reload -> test -> refine -> repeat
```

A named ESPHome device may be explicitly pre-authorized for repeated validate/compile/OTA/reconnect/log/re-flash cycles during that task.

Pre-authorization never implicitly extends to unrelated devices, integrations, dashboards, security settings or network boundaries.

## Approval-gated by default

Unless explicitly included in the current task:

- Home Assistant restart/shutdown;
- ESPHome OTA/install;
- HACS install/update/remove;
- custom integration installation/update;
- destructive database/Recorder work;
- deletion of integrations/devices/entities or substantial unrelated config;
- authentication/network/security changes;
- significant physical/security actions;
- expansion of filesystem/network/privilege boundaries.

## Git

The workspace is a local Git repository.

Codex may stage and commit substantial known-good work without separate approval when the current task authorizes the underlying changes. `.git` must therefore be writable inside the workspace permission profile.

Never force-add ignored credential/session files or add/push a remote unless the user explicitly requests it.

## Read-only requests

When the user says a task is read-only, an audit, investigation-only, or "do not make changes":

- do not edit/delete files;
- do not remediate findings;
- do not stage or commit;
- do not reload/restart/flash/install;
- report findings only.

A later separate authorization may permit remediation.

## Definition of done for dashboard work

Where practical:

1. validate;
2. safely reload;
3. render visibly;
4. verify data populates;
5. inspect console/network errors;
6. test relevant interactions;
7. test desktop/mobile layouts;
8. refine until correct and polished;
9. commit substantial known-good work;
10. report remaining warnings/blockers.

See `docs/PROMPTING.md` for reusable task prompts and `docs/SECURITY.md` for the full trust model.
