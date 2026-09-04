# Troubleshooting

## Local app does not appear

Confirm the app source exists under:

```text
/addons/codex_file_bridge/
```

with:

```text
config.yaml
Dockerfile
run.sh
server.py
```

Refresh the Home Assistant local app/add-on store.

## Bridge token generation tool missing

If `openssl` is unavailable in the HA terminal, generate 64 hex characters with:

```sh
cat /proc/sys/kernel/random/uuid /proc/sys/kernel/random/uuid | tr -d '\n-'
echo
```

Do not paste the result into chat or Git.

## Bridge health worked, then port 8443 refuses connections

A TCP refusal occurs before bearer authentication.

Check that **Home Assistant Codex Bridge** is running and that the firewall still permits VM -> HA TCP 8443.

## `configuration.yaml` is readable but `secrets.yaml` must be denied

Expected:

```text
configuration.yaml -> HTTP 200
secrets.yaml       -> HTTP 403
```

If a secret file returns `200`, stop using the bridge and repair the HA-side policy.

## TLS works only with `curl -k`

`-k` is bootstrap-only.

Pin the bridge certificate to:

```text
~/.config/codex-ha/bridge-ca.crt
```

and verify its SHA-256 fingerprint against the app log.

If `tls_san_ip` or `tls_san_dns` changes, the app regenerates the certificate and the Ubuntu copy must be re-pinned.

## Certificate hostname/IP mismatch

The URL used by `ha-sync` must match one of the certificate SANs.

Configure the app options:

```text
tls_san_ip
tls_san_dns
```

then re-pin the regenerated certificate.

## `ha-sync delete` reports an already missing file

The client treats raw bridge `404` as idempotent success:

```text
ABSENT /homeassistant/...
```

## `ha-sync` cannot read its environment

The Codex permission profile needs narrow reads for:

```text
~/bin/ha-sync
~/.config/codex-ha/env
~/.config/codex-ha/bridge-ca.crt
```

while keeping browser/auth data denied.

The bridge env contains the low-privilege bridge token. HA-side policy still independently limits it.

## `ha-sync` fails with `PermissionError: Operation not permitted`

If the error occurs while opening an HTTPS connection, the `workspace-write` sandbox probably has network access disabled. Add:

```toml
[sandbox_workspace_write]
network_access = true
```

or launch Codex with:

```bash
codex --sandbox workspace-write --ask-for-approval never \
  -c sandbox_workspace_write.network_access=true
```

Restart Codex after changing the config. This setting permits socket creation from sandboxed commands; the bridge token and Home Assistant-side path policy still control what `ha-sync` may access.

## Playwright MCP tools still ask for approval

Set the default on the trusted local server rather than maintaining a per-tool list:

```toml
[mcp_servers.playwright]
url = "http://localhost:8931/mcp"
default_tools_approval_mode = "approve"
```

Restart Codex. Per-tool `approval_mode` entries override the server default, so remove or update any conflicting `prompt` or `writes` entries.

## Codex permission profile says `default_permissions` is missing

Keep:

```toml
default_permissions = "homeassistant"
```

as a top-level key before section headers.

## Codex executable is blocked by sandbox

Do not blanket-deny all of:

```text
~/.codex
```

Some Codex installation layouts place the executable beneath that tree.

Deny auth material narrowly instead.

## Local Git cannot stage/commit

The workspace permission profile should include:

```toml
[permissions.homeassistant.filesystem.":workspace_roots"]
"." = "write"
".git" = "write"
```

Restart Codex after changing permissions.

Ordinary Unix ownership/mode bits are not sufficient proof because the sandbox can mount `.git` differently.

## Playwright launches headed without an X server

Typical error:

```text
Looks like you launched a headed browser without having a XServer running
```

Run `client/install-playwright-service.sh` from the logged-in graphical desktop.

The installer uses desktop autostart to import the real display/session variables before restarting Playwright MCP.

## Playwright works now but fails after reboot

Verify:

```text
~/.config/autostart/playwright-mcp.desktop
~/bin/start-playwright-mcp
~/.config/systemd/user/playwright-mcp.service
```

After login:

```bash
systemctl --user --no-pager --full status playwright-mcp.service
```

Then repeat the read-only smoke test.

## Playwright MCP rejects `127.0.0.1`

Use:

```text
http://localhost:8931/mcp
```

not:

```text
http://127.0.0.1:8931/mcp
```

Some versions validate the Host header.

## Playwright service exits with status 127

Node installed through NVM may not be on systemd's default PATH.

Re-run the installer from a shell where `node` and `npx` resolve correctly. It records the current Node bin directory in the service.

## Home Assistant login fails from another VLAN

Do not open more firewall access as the first fix.

If using manual profile login, confirm the account/password and browser session.

If using `trusted_networks`, verify:

- exact VM `/32`;
- correct dedicated HA user ID;
- provider order;
- `homeassistant` fallback provider;
- no overlap with `trusted_proxies`;
- fixed VM IP.

## `trusted_networks` is too broad

Never trust an entire VLAN just for Codex. Use the single fixed VM address `/32`.

If that is not acceptable, use manual browser login instead.

## Browser profile is accessible to shell commands

The permission profile should deny:

```text
~/.config/codex-ha/browser-profile
```

Playwright MCP still uses that profile directly.

## Git rollback did not restore a Lovelace dashboard

Home Assistant storage-mode dashboards are stored under `.storage`, which this design denies and does not commit.

Use YAML-mode dashboards or an explicit export/versioning workflow if complete dashboard rollback is required.

## Security audit finds a suspected credential

During a read-only audit:

- do not print it;
- do not hash/transform it;
- report path/location only;
- do not remediate until separately authorized.

After separate authorization, remove/replace the literal, validate the result and commit the intended remediation.

If a real credential was committed to Git history, removing the current file is not enough: rotate/revoke the credential and rewrite/purge history before publication.

## Existing frontend console warnings

Separate:

- pre-existing warnings;
- certificate/browser noise;
- errors introduced by the current task;
- errors that prevent functionality.

Do not declare a dashboard complete merely because configuration saved.
