# Public release checklist

Use this immediately before changing repository visibility.

## Current-tree checks

Confirm the repository contains none of:

- real Home Assistant/LAN/VLAN IP addresses;
- private hostnames;
- Home Assistant user IDs;
- bridge tokens;
- Home Assistant/OpenAI/GitHub access tokens;
- secret values;
- local secret alias inventories;
- browser cookies/session profiles;
- TLS/SSH private keys;
- databases/backups;
- personal shell history;
- local `.env` files.

This template should contain only placeholders and RFC 5737 documentation addresses.

## Automated secret scan

Run at least one full-history scanner against a complete local clone, preferably two independent tools, for example:

```text
gitleaks
trufflehog
```

Review findings manually. Do not assume a private repository is safe simply because automated scanning is clean.

## History

A public release exposes Git history, not just the current tree.

If deployment-specific data or credentials ever existed in reachable history:

1. rotate/revoke any actual credential first;
2. rewrite/purge history;
3. remove stale branches/tags containing the old objects;
4. re-scan the rewritten repository;
5. understand that hosted Git providers may retain unreachable objects/cache temporarily.

This project's sanitized publication workflow intentionally rewrites `main` so old deployment-specific commits are no longer in the branch history.

## Repository settings

Before publication:

- choose the final repository name, recommended `home-assistant-codex-bridge`;
- update the repository description/topics;
- review default branch;
- review collaborators/deploy keys/webhooks/actions secrets;
- review branch protection;
- enable secret scanning where available;
- enable private vulnerability reporting/security advisories if desired.

## Documentation

Verify:

- all `<REPOSITORY_URL>` placeholders are updated if desired;
- installation instructions still match current Codex/Home Assistant/Playwright behavior;
- no screenshots contain private network data or user identities;
- no private deployment status is described as universal behavior.

## License

Confirm you intend to publish under:

```text
Apache License 2.0
subject to Commons Clause License Condition v1.0
```

This combination is source-available and includes a commercial-sale restriction; it is not OSI-approved open source.

Review `LICENSE` and `NOTICE` before publication.

## Final command-line scan

From a clean clone, examples:

```bash
git grep -nE \
  '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|Authorization:[[:space:]]*Bearer|api[_-]?key[[:space:]]*[:=][[:space:]]*[^<[:space:]]+)' \
  -- . ':!LICENSE' || true
```

Also inspect:

```bash
git status
git log --oneline --all --decorate
git branch -a
git tag -l
```

Automated regexes are only supplemental; use a dedicated secret scanner.

## Publication gate

Only make the repository public after:

```text
Current tree sanitized            PASS
Reachable history sanitized       PASS
Full-history secret scan          PASS
Branches/tags reviewed            PASS
Repository settings reviewed      PASS
License reviewed                  PASS
Documentation reviewed            PASS
```
