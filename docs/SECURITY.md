# Security model

## Goal

Provide a practical least-privilege boundary that lets Codex work effectively on Home Assistant and ESPHome while keeping secret values, `.storage`, HAOS root/SSH access, databases and backups outside normal Codex filesystem access.

This is a hobby/home-automation reference architecture, not a formal high-assurance isolation system.

## Trust boundaries

### Ubuntu Codex VM

The VM runs:

- Codex CLI;
- local Git workspace;
- `ha-sync`;
- visible Chrome + Playwright MCP.

Recommended network posture:

```text
Codex VM -> Home Assistant UI port    ALLOW
Codex VM -> Home Assistant TCP 8443  ALLOW
Codex VM -> Internet                 ALLOW
Codex VM -> SSH / unrelated LAN      DENY
```

Do not give the VM HAOS root/SSH credentials or general host filesystem access.

### HA-side bridge

The bridge is the hard filesystem authorization boundary.

Home Assistant configuration is mounted into the app as:

```text
/homeassistant
```

Requests are checked against:

```text
/homeassistant/.codex_access/READ_WRITE.txt
/homeassistant/.codex_access/READ_ONLY.txt
/homeassistant/.codex_access/DENY.txt
```

which corresponds to `/config/.codex_access/` on Home Assistant.

The policy directory is outside Codex-writable paths.

Possession of the bridge bearer token does not bypass the path policy.

### Home Assistant browser account

The browser account is a separate privilege boundary.

A dedicated account may need Administrator privileges for dashboard editing, HACS, ESPHome Device Builder and Developer Tools. That means filesystem denies alone do not prevent powerful UI actions.

UI risk is constrained by:

- local `AGENTS.md`;
- task-scoped approval rules;
- dedicated browser account/profile;
- network isolation;
- user oversight for high-impact operations.

### Network boundary

The network is an independent blast-radius control.

Do not treat Home Assistant authentication or the bridge bearer token as a substitute for VLAN/firewall isolation.

## Default file policy

### Read/write

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

### Read-only

```text
/homeassistant/configuration.yaml
/homeassistant/packages/**
/homeassistant/custom_components/**
/homeassistant/www/community/**
/homeassistant/home-assistant.log*
```

### Explicit deny

```text
**/secrets.yaml
/homeassistant/.storage/**
/homeassistant/*.db*
/homeassistant/backups/**
**/.ssh/**
**/*.key
**/*.pem
```

`DENY` wins over an allow rule.

## Secret handling

Codex may use `!secret` alias names from a locally generated index:

```text
/config/packages/codex/SECRET_NAMES.md
```

The index must contain names only.

If an alias is missing, Codex should report the required alias name. The value is entered manually outside ChatGPT/Codex.

### Bridge token caveat

`ha-sync` needs the bridge bearer token. It is stored locally in a protected file such as:

```text
~/.config/codex-ha/env
```

The Codex permission profile may need to allow that file to be read so `ha-sync` can function.

This is an accepted tradeoff: the token authenticates only to the restricted bridge and the HA-side policy still limits every request.

Do not confuse it with a general Home Assistant access token.

## Codex/OpenAI auth

Deny sandboxed shell access to:

```text
~/.codex/auth.json
```

Do not blanket-deny all of `~/.codex` if your Codex executable is installed beneath it.

## Browser profile

Recommended profile:

```text
~/.config/codex-ha/browser-profile
```

Deny routine sandboxed shell access to the profile. Playwright MCP intentionally uses it.

Protecting the profile does not make the browser account low privilege; it only reduces direct cookie/session-file exposure to shell commands.

## Browser authentication choices

### Manual login

The human logs the dedicated browser profile into Home Assistant once. Codex never receives the password.

### Exact-IP trusted login

Home Assistant `trusted_networks` can map the fixed Codex VM address to the dedicated user.

This is powerful source-IP trust. If used:

- trust only the exact VM `/32`;
- map only to the dedicated user;
- retain the `homeassistant` provider fallback;
- keep firewall isolation tight;
- never commit the real Home Assistant user ID;
- validate configuration before restart.

## TLS

The bridge generates a self-signed certificate in app-private `/data`.

Configure `tls_san_ip` / `tls_san_dns` before use.

The client should pin the certificate at:

```text
~/.config/codex-ha/bridge-ca.crt
```

`curl -k` is only for the first bootstrap connectivity check.

Changing configured SAN values causes certificate regeneration; re-pin the certificate afterward.

## Path handling

The bridge:

- normalizes requested paths;
- requires them to remain under `/homeassistant`;
- rejects existing symlink components;
- resolves the path and verifies it remains inside the root;
- applies policy after normalization;
- filters denied entries from listings.

## Write/delete behavior

- maximum write: 10 MiB/request;
- writes use a temporary file + fsync + atomic `os.replace`;
- new files default to mode `0644`;
- directory creation requires an existing parent and writable match;
- delete is file-only and requires read/write authorization;
- directory deletion is not exposed.

## Command restrictions

Reference exec-policy forbids:

```text
sudo
su
pkexec
doas
ssh
scp
sftp
mount
umount
docker
podman
```

`ha-sync` is the intended HA filesystem transport.

These rules complement, but do not replace, the HA-side policy and network boundary.

## Task-scoped authorization

Normal iterative work inside an explicitly authorized task may proceed without repeated approval.

A specific ESPHome device can be authorized for repeated validate/compile/OTA/reconnect/log/re-flash cycles during the task.

Authorization never implicitly extends to unrelated devices or later tasks.

## High-impact actions

Unless explicitly pre-authorized for the task, retain user approval before:

- Home Assistant restart/shutdown;
- HACS install/update/remove;
- custom integration install/update;
- destructive database/Recorder work;
- deleting integrations/devices/entities or substantial unrelated config;
- authentication/network/security changes;
- significant physical/security actions;
- expansion of filesystem/network/privilege boundaries.

## Read-only semantics

If the user requests a read-only audit/investigation, Codex must not remediate findings, edit/delete files, stage/commit, reload/restart, install/update packages or flash firmware.

A later separate authorization can permit remediation.

## Repository/publication hygiene

Never commit:

- secret values or `secrets.yaml`;
- bridge/Home Assistant/OpenAI/GitHub tokens;
- trusted-user IDs;
- browser profiles/cookies;
- TLS private keys;
- SSH keys;
- databases/backups;
- local secret alias inventories.

This public template uses placeholders and RFC 5737 documentation addresses only.

## Periodic invariants

Verify:

```text
Bridge health                        reachable
configuration.yaml                  HTTP 200
secrets.yaml                        HTTP 403
Home Assistant UI                   reachable
HA SSH                              blocked
Internet HTTPS                      reachable
Codex auth file                     denied
browser profile                     denied
sudo                                forbidden
ha-sync                             works
Playwright after reboot/login       works
local Git metadata                  writable
```
