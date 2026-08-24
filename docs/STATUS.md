# Reference implementation status

Last documentation review: **2026-08-24**

## Overall

The reference architecture has been exercised end-to-end with:

- Home Assistant OS;
- Ubuntu Desktop VM;
- Codex CLI;
- restricted HTTPS file bridge;
- pinned bridge TLS certificate;
- `ha-sync`;
- dedicated Home Assistant browser account;
- headed Chrome + Playwright MCP;
- local Git workflow;
- Home Assistant dashboards/Developer Tools;
- HACS and ESPHome Device Builder when installed.

Exact software versions and UI paths change over time. Revalidate current upstream requirements during installation.

## Verified behaviors

```text
Allowed bridge read                         PASS
Denied secrets.yaml bridge read             PASS
Allowed bridge write                        PASS
Bridge delete/mkdir                         PASS
Home Assistant UI through Playwright        PASS
Headed Playwright after Ubuntu reboot       PASS
Dashboard render                            PASS
Developer Tools access                      PASS
Local Git stage/commit                      PASS
Codex auth-file sandbox deny                PASS
Browser-profile sandbox deny                PASS
sudo exec-policy deny                       PASS
```

## Publication status

The repository template contains:

- no live deployment IPs;
- no private hostnames;
- no Home Assistant user IDs;
- no secret alias inventory;
- no tokens/passwords/API keys;
- no browser/session data;
- no private keys/certificates;
- documentation-only RFC 5737 example addresses.

See `PUBLIC_RELEASE_CHECKLIST.md` before changing repository visibility.

## Known design limitations

- The browser account may be an HA Administrator and is therefore a stronger privilege surface than the bridge.
- The bridge token must be usable by `ha-sync`; HA-side path policy remains the primary filesystem boundary.
- Git does not version Home Assistant `.storage`, which is intentionally denied.
- Storage-mode Lovelace changes need an explicit export/versioning strategy for full rollback.
- Playwright MCP defaults to `@latest` unless the installer is given a pinned package version.
- The architecture is practical least privilege, not high-assurance containment.
