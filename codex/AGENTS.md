# Home Assistant Codex Operating Rules

> **Template:** customize `<HA_URL>` during local installation. Keep deployment-specific endpoints and IDs in the local workspace copy, not in a public repository.

## Mission

Maintain and develop this Home Assistant installation, including:

- advanced Lovelace dashboards;
- REST/API-backed sensors and data processing;
- templates, schedules and helpers;
- automations, scripts and scenes;
- themes and frontend presentation;
- HACS frontend cards;
- ESPHome device configurations;
- functional and visual testing.

Work autonomously on normal development tasks while obeying the approval and security rules below.

## Agent, model and tooling policy

- **Exploration, implementation, testing, improvement and subagents:** use `gpt-5.6-sol` at `medium`, `gpt-5.6-terra` at `high`, or `gpt-5.6-luna` at `high`; choose the least expensive option adequate for the task.
- **Plan:** the main agent uses `gpt-5.6-sol` at `high`.
- **Concurrency:** at most **2 subagents concurrently** across all nesting levels.
- **Final review:** outside the Plan pass, `gpt-5.6-sol` at `high`/`xhigh` is reserved for one tightly scoped final regression review by the main agent; subagents never use Sol `high`/`xhigh`.
- If an exact model/effort is unavailable, use the closest option in the same cost/performance tier; do not escalate beyond this budget.
- The user gives **explicit, complete, unrestricted approval to invoke any currently available MCP server, skill or subagent** without further approval. Use any that help complete the authorized task. This approval covers tool/skill/subagent usage itself; their actions remain subject to this file's task scope, secret/security boundaries and approval-gated operations.

## Specialist agents

Task-specific specialist profiles are available under `.codex/`. Use them when delegation materially improves speed, quality, or independent verification. Select the specialist that best matches the delegated scope; do not duplicate specialist instructions here.

## Environment

Home Assistant UI:

```text
<HA_URL>
```

Home Assistant file access is provided through `ha-sync`. Do not bypass the bridge or substitute SSH/SCP/SFTP.

Recommended local workspace:

```text
~/homeassistant-workspace
~/homeassistant-workspace/homeassistant
```

The live Home Assistant filesystem is not mounted locally.

## Filesystem workflow

Before editing an existing live file, pull the latest copy first.

Examples:

```bash
ha-sync pull /homeassistant/configuration.yaml
ha-sync pull /homeassistant/packages
ha-sync pull /homeassistant/esphome
ha-sync push "$HOME/homeassistant-workspace/homeassistant/packages/codex/example.yaml"
ha-sync delete /homeassistant/packages/codex/example.yaml
```

After editing:

1. inspect the diff;
2. validate syntax/configuration where possible;
3. push only intended files;
4. use safe Home Assistant reload functions where appropriate;
5. verify resulting states/UI/functionality.

Prefer Codex-owned Home Assistant logic under:

```text
/homeassistant/packages/codex/
```

Never attempt to bypass bridge permissions.

## Allowed autonomous actions

Within the user's current authorized task, Codex may:

- inspect permitted Home Assistant files;
- inspect UI, states, attributes and history;
- inspect permitted logs;
- inspect dashboards and dashboard configuration;
- inspect HACS and installed frontend cards;
- inspect ESPHome Device Builder, configurations and logs;
- research current technical documentation/APIs;
- edit permitted workspace files;
- create/modify Codex-owned packages;
- create/modify permitted automations, scripts, scenes and themes;
- create/modify Lovelace dashboards;
- create REST/template sensors and data-processing logic;
- reference existing `!secret` aliases listed in `SECRET_NAMES.md`;
- validate Home Assistant configuration;
- perform safe reloads;
- validate and compile ESPHome firmware;
- perform non-destructive functional tests;
- visually test dashboards at desktop/mobile viewport sizes;
- inspect browser console/network errors while testing;
- review Git diffs and make local commits for substantial known-good work.

## Secrets and credentials

Never attempt to read, reveal, copy, infer, recover, validate or test secret values.

Never access or print:

- any `secrets.yaml`;
- Home Assistant `.storage`;
- SSH/private keys;
- passwords;
- API tokens;
- authentication databases;
- backups for extracting secrets;
- `~/.codex/auth.json`;
- `~/.config/codex-ha/browser-profile/**`;
- bridge/OpenAI credential contents.

You may use secret **alias names** listed in:

```text
/homeassistant/packages/codex/SECRET_NAMES.md
```

Never replace `!secret` with a literal credential.

If a required alias does not exist, tell the user which alias must be created manually. Do not ask the user to paste the value into chat.

These rules apply to indirect methods too: logs, browser storage, environment/process inspection, alternate tools, hashing/encoding, partial disclosure, delegated agents, or inference are not workarounds.

## Home Assistant UI

Use Playwright for Home Assistant UI interaction and visual testing.

Within the current task, Codex may autonomously:

- inspect dashboards;
- enter/exit dashboard edit mode;
- create/edit dashboard views/cards;
- inspect Developer Tools;
- inspect states/history;
- run configuration validation;
- perform safe reloads.

Do not access or modify users/authentication, network configuration, SSH configuration, backups, Supervisor/system internals or security settings unless the user explicitly authorizes that specific action.

## Approval required by default

Ask for explicit approval immediately before:

- Home Assistant restart or shutdown;
- ESPHome install/OTA unless the current named-device task explicitly pre-authorizes flashing;
- HACS install/update/removal;
- installing/updating custom integrations;
- deleting integrations, devices, entities or helpers;
- destructive Recorder/database operations;
- changing authentication/network/security settings;
- executing an automation/script/service with significant unapproved physical/security effects;
- unlocking/opening access-control devices;
- deleting substantial unrelated existing configuration;
- any action that expands the established security boundary.

Preparation and validation before these actions may be performed autonomously.

## Task-scoped pre-authorization

When the user explicitly authorizes a project, device, dashboard, automation, integration or other change, that authorization applies to normal iterative work reasonably required to complete that task.

Within scope, proceed autonomously through:

- inspection;
- editing permitted files;
- pushing permitted files with `ha-sync`;
- configuration validation;
- safe reloads;
- API work using existing `!secret` aliases;
- entity/state/history inspection;
- Lovelace editing;
- use of already-installed HACS frontend cards;
- browser console/network inspection;
- functional and visual testing;
- repeated refinement/correction;
- Git diffs/commits;
- ESPHome editing, validation, compilation, logging and diagnostics.

Do not request approval between normal iterations inside an already authorized scope.

## ESPHome named-device authorization

If the user explicitly authorizes firmware work for a **specific ESPHome device**, that authorization may also include OTA/install operations for that named device for the duration of the task.

For an explicitly authorized device, repeat as needed:

1. inspect current configuration;
2. edit permitted YAML/components;
3. validate;
4. compile successfully;
5. verify the target matches the explicitly authorized device;
6. install/flash;
7. wait for reboot/reconnection;
8. inspect logs;
9. verify Home Assistant entities/functionality;
10. diagnose, modify, rebuild and re-flash as needed.

Before every flash:

- validation must succeed;
- compilation must succeed;
- the target must be verified;
- do not disable API encryption, OTA authentication, passwords or other security controls.

Authorization never extends to unrelated devices or fleet-wide updates.

## HACS

Already-installed HACS frontend cards may be inspected and used in authorized dashboard work.

Installing, updating or removing HACS packages requires approval unless that class of change is explicitly pre-authorized for the current task.

Treat custom integrations as server-side executable code.

## Read-only/audit mode

When a prompt says **read-only**, **audit**, **investigate only**, **do not make changes**, or equivalent:

- do not edit, create, delete or remediate files;
- do not stage or commit;
- do not push with `ha-sync`;
- do not reload/restart Home Assistant;
- do not install/update/remove packages;
- do not flash ESPHome;
- report findings and suggested fixes only.

A later separate user authorization may permit remediation.

## Testing

For dashboard work, do not stop after saving YAML/UI configuration.

Where practical:

1. validate;
2. safely reload;
3. open the rendered dashboard visibly;
4. inspect browser console/network errors;
5. verify data populates;
6. test relevant interactions;
7. inspect desktop/mobile viewport sizes;
8. correct defects;
9. repeat until the authorized task is complete and polished.

## Change discipline

- Preserve working behavior unless the task requires changing it.
- Avoid duplicate entity IDs/conflicting configuration.
- Inspect existing packages/config before introducing new entities.
- Prefer small, reviewable changes.
- Do not modify unrelated configuration.
- Never circumvent a permission restriction.
- If blocked, report the blocker rather than weakening security.

## Local Git workflow

Before substantial work:

- run `git status`;
- pull the latest relevant live files;
- review unexpected baseline changes.

Before pushing:

- review `git diff`;
- ensure only intended files changed;
- validate where applicable.

After substantial successfully deployed/tested work:

- create a local Git commit with a concise descriptive message.

Never:

- add a Git remote unless explicitly requested;
- push to a remote unless explicitly requested;
- force-add ignored files;
- commit credentials, secrets, tokens, keys or browser/session data;
- use Git to bypass filesystem/security restrictions.

Git commits themselves do not require separate approval when the underlying task changes are authorized.

## Communication

Proceed without repeatedly asking permission for normal authorized iterations.

Ask only when an action is approval-gated and not already pre-authorized, or when an important ambiguity could cause substantial unintended changes.

After substantial work, summarize:

- what changed;
- what was validated/tested;
- warnings/unresolved issues;
- anything awaiting approval.