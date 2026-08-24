# Contributing

Contributions are welcome if they preserve the project's least-privilege security model.

## Before opening a change

- never include real credentials, tokens, user IDs, private IPs/hostnames, browser data or secret alias inventories;
- use placeholders and RFC 5737 documentation addresses;
- preserve `DENY` precedence in the HA-side bridge policy;
- do not weaken secret-handling or privilege-escalation rules merely to simplify setup;
- keep deployment-specific configuration in local/private files.

## Changes to security boundaries

Changes that broaden bridge paths, Home Assistant privileges, network access, authentication behavior or Codex host permissions should include:

- threat-model impact;
- reason the broader access is required;
- safer alternatives considered;
- regression tests.

## Testing

For shell/Python changes, test the specific client/app behavior where possible.

For documentation changes, verify commands are internally consistent and do not contain live deployment information.

Before submitting:

```bash
git status
git diff --check
```

Run a secret scanner if available.

## Licensing of contributions

Unless explicitly stated otherwise, contributions submitted for inclusion are provided under the project's license terms in `LICENSE`: Apache License 2.0 subject to the Commons Clause License Condition v1.0.

Do not contribute material you do not have the right to license under those terms.
