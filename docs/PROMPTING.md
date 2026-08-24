# Prompting ChatGPT / Codex

This repository is designed to be referenced from ChatGPT/Codex prompts without embedding deployment secrets.

Use your own repository URL:

```text
<REPOSITORY_URL>
```

The local workspace `AGENTS.md` is the active runtime/approval contract and contains deployment-specific values such as `<HA_URL>` after local installation.

## Minimal task prompt

```text
Use your connected GitHub access to read:
<REPOSITORY_URL>

Read CODEX_REFERENCE.md and follow the local AGENTS.md as the active operating
contract.

Build <TASK>.

You are pre-authorized to perform normal iterative work required for this task:
inspect, edit permitted files, validate, safely reload, test APIs using existing
!secret aliases, use Playwright for functional/visual testing, refine repeatedly
and make local Git commits of known-good work.

Do not expand the established security boundary or modify unrelated systems.
```

## First-time installation prompt

```text
Use your connected GitHub access to read:
<REPOSITORY_URL>

I am setting this environment up from scratch. Use docs/FIRST_TIME_SETUP.md as
the primary installation guide and docs/SECURITY.md as the security contract.

Guide me step by step with complete copy/paste commands where appropriate.

Do not ask me to paste secret values, bridge tokens, GitHub tokens, Home
Assistant user IDs/passwords or OpenAI API keys into chat. Tell me when a value
must be entered manually outside ChatGPT.

Keep privileged bootstrap actions separate from actions Codex is permitted to
perform after installation.
```

## Advanced dashboard/API task

```text
Use your connected GitHub access to read <REPOSITORY_URL> and follow
CODEX_REFERENCE.md plus the local AGENTS.md.

Build an advanced Home Assistant dashboard for <GOAL>.

You are pre-authorized to iterate autonomously until it is functionally correct
and visually polished.

You may inspect existing entities/packages/cards, create supporting logic under
/homeassistant/packages/codex/, use existing !secret aliases without reading
their values, configure Lovelace, use already-installed HACS frontend cards,
validate/reload safely, inspect states/history/logs/browser console/network
errors, test desktop/mobile layouts, refine repeatedly and make local commits.

Do not stop at generating YAML: deploy, render, test and iterate.
```

## Secret handling

If an API requires credentials:

- use an existing alias from the local `SECRET_NAMES.md`;
- never read/request the value;
- if the alias is missing, report the alias name the user should add manually;
- never hard-code credentials into readable YAML/dashboard/script content.

## Named ESPHome device with repeated OTA authorization

```text
Use your connected GitHub access to read <REPOSITORY_URL> and follow
CODEX_REFERENCE.md plus the local AGENTS.md.

Modify ESPHome device <DEVICE YAML / DEVICE NAME> to <GOAL>.

For this task, you are explicitly pre-authorized to edit, validate, compile,
OTA/install, reconnect, inspect logs/entities, diagnose, modify, rebuild and
re-flash this named device as many times as reasonably necessary until the task
is complete.

Before every flash, validation and compilation must succeed and you must verify
the target is the explicitly authorized device.

This authorization does not apply to any other ESPHome device.
```

## HACS changes

Using already-installed HACS frontend cards is normal dashboard work.

To authorize package changes:

```text
For this task only, you are also pre-authorized to install/update only the HACS
frontend cards directly required for this dashboard. Do not install/update
unrelated HACS packages or custom integrations.
```

Custom integrations execute server-side Python and deserve stricter review.

## Home Assistant restart authorization

```text
For this task only, you are also pre-authorized to restart Home Assistant when
configuration validation succeeds and a full restart is genuinely required.
Prefer a safe reload when sufficient and verify Home Assistant returns afterward.
```

## Read-only investigation

```text
Use your connected GitHub access to read <REPOSITORY_URL> and follow the local
AGENTS.md.

Investigate <PROBLEM>. This task is read-only.

Inspect permitted files, states/history/logs, Lovelace, browser
console/network data, HACS and ESPHome as needed, but make no changes, do not
stage/commit, do not reload/restart, and do not remediate findings.

Report the likely cause, supporting evidence and smallest recommended fix.
```

## Prepare but do not deploy

```text
Use your connected GitHub access to read <REPOSITORY_URL> and follow the local
AGENTS.md.

Prepare changes for <TASK>, validate locally where possible and show the
resulting diff/plan, but do not push files, change Lovelace, reload/restart Home
Assistant, install/update HACS or flash ESPHome until I approve deployment.
```

## Combined scoped authorization

```text
This authorization applies only to <PROJECT>.

Within this project, you are pre-authorized for normal iterative Home Assistant
work. You are also pre-authorized to:
- install/update only HACS frontend cards directly required by this project;
- restart Home Assistant only when validation succeeds and a restart is truly
  required;
- edit/validate/compile/OTA/re-flash ESPHome device <DEVICE> repeatedly as
  needed.

Do not extend these permissions to unrelated packages, integrations, devices,
dashboards, automations or security/network settings.
```

## What task-scoped authorization does not mean

It never automatically authorizes:

- unrelated systems/devices;
- authentication/network/security changes;
- filesystem/network privilege expansion;
- secret extraction;
- HAOS/root/SSH access;
- destructive database operations;
- HACS package changes unless included;
- ESPHome flashing of unnamed devices;
- full HA restart unless included.

## Prompt hygiene

Good prompts identify:

- intended result;
- specific dashboard/device/integration scope;
- whether deployment is allowed;
- whether HACS changes are allowed;
- whether HA restarts are allowed;
- exact ESPHome devices authorized for flashing.

Do not include secret values or unnecessary blanket permissions.
