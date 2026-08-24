# Security policy

For the architecture and trust model, see [`docs/SECURITY.md`](docs/SECURITY.md).

## Reporting a vulnerability

Do not include secret values, tokens, private keys, browser cookies or private network details in a public issue.

If the repository host supports private vulnerability/security advisories, use that channel for issues that could expose credentials, bypass bridge path policy, escape `/homeassistant`, defeat authentication, or materially expand Codex privileges.

For ordinary hardening suggestions that do not disclose sensitive information, a normal issue is appropriate.

## If you discover an exposed credential

1. revoke/rotate the credential first;
2. remove it from the current tree;
3. purge reachable Git history;
4. remove stale branches/tags that retain it;
5. run a full-history secret scan;
6. do not assume making a repository private again invalidates a leaked credential.

## Supported versions

This repository is a reference architecture rather than a packaged SaaS product. Security fixes are applied to the current `main` branch; users should re-check compatibility with their installed Home Assistant, Codex and Playwright versions.
