# Home Assistant Codex Bridge API

Base URL:

```text
https://<HA_HOST>:8443
```

The bridge uses a self-signed TLS certificate. Normal clients should verify the pinned certificate at:

```text
~/.config/codex-ha/bridge-ca.crt
```

`curl -k` is for initial bootstrap only.

## Authentication

`GET /health` is unauthenticated.

All other endpoints require:

```http
Authorization: Bearer <bridge-token>
```

The token is not a Home Assistant access token and does not bypass path authorization.

## Health

```http
GET /health
```

Example:

```json
{
  "status": "ok",
  "service": "home-assistant-codex-bridge",
  "version": "0.2.0"
}
```

## List

```http
GET /list?path=/homeassistant/packages
```

Only policy-visible entries are returned.

## Read

```http
GET /file?path=/homeassistant/configuration.yaml
```

Allowed file: `200`.

Denied file such as `/homeassistant/secrets.yaml`: `403`.

## HEAD

```http
HEAD /file?path=/homeassistant/configuration.yaml
```

Checks availability/metadata without returning the body.

## Write/replace

```http
PUT /file?path=/homeassistant/packages/codex/example.yaml
```

The request body is the complete file.

Maximum request body:

```text
10 MiB
```

Example response:

```json
{
  "status": "written",
  "path": "/homeassistant/packages/codex/example.yaml",
  "bytes": 123,
  "sha256": "..."
}
```

## Delete

```http
DELETE /file?path=/homeassistant/packages/codex/example.yaml
```

Only read/write-authorized files may be deleted. Directory deletion is not exposed.

Raw missing-file response: `404`.

`ha-sync delete` treats `404` as idempotent success and prints `ABSENT`.

## Create directory

```http
POST /mkdir?path=/homeassistant/packages/codex/subdirectory
```

The parent must exist and the new path must be writable.

## Typical status codes

```text
200 success/existing
201 directory created
400 invalid request/path/filesystem error
401 missing/wrong bearer token
403 policy denied
404 endpoint/file/directory not found
```

HTTP `000` / TCP failure occurs before authentication; verify the app and firewall first.

## Security behavior

The bridge:

- restricts paths to `/homeassistant`;
- normalizes paths;
- rejects existing symlink components;
- verifies resolved targets remain inside the root;
- evaluates deny before read/write;
- filters denied list entries;
- uses TLS 1.2+;
- performs atomic file replacement.

## Policy source

```text
/homeassistant/.codex_access/READ_WRITE.txt
/homeassistant/.codex_access/READ_ONLY.txt
/homeassistant/.codex_access/DENY.txt
```

The protected policy should not be writable by Codex.

## Preferred client

Codex should normally use:

```text
ha-sync
```

Direct API access is mainly for bootstrap verification or troubleshooting.
