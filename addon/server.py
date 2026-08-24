#!/usr/bin/env python3

import fnmatch
import hashlib
import json
import os
import posixpath
import secrets
import ssl
import tempfile

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path("/homeassistant")
POLICY = ROOT / ".codex_access"
MAX_WRITE = 10 * 1024 * 1024
SERVICE_VERSION = "0.2.0"


def load_token():
    with open("/data/options.json", "r", encoding="utf-8") as f:
        options = json.load(f)

    token = str(options.get("api_token", "")).strip()
    if len(token) < 32:
        raise RuntimeError("api_token must be at least 32 characters")
    return token


TOKEN = load_token()


def load_patterns(filename):
    result = []
    with open(POLICY / filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            result.append(line)
    return result


def policies():
    return (
        load_patterns("READ_WRITE.txt"),
        load_patterns("READ_ONLY.txt"),
        load_patterns("DENY.txt"),
    )


def matches(path, patterns):
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def pattern_prefix(pattern):
    positions = [
        i
        for i in (pattern.find("*"), pattern.find("?"), pattern.find("["))
        if i >= 0
    ]
    if positions:
        pattern = pattern[: min(positions)]
    return pattern.rstrip("/")


def normalize_path(raw):
    if raw is None:
        raise ValueError("Missing path")

    raw = unquote(raw)
    if "\x00" in raw:
        raise ValueError("Invalid path")

    logical = posixpath.normpath(raw)
    if not logical.startswith("/"):
        logical = "/" + logical

    if logical != "/homeassistant" and not logical.startswith("/homeassistant/"):
        raise PermissionError("Path outside /homeassistant")

    relative = logical[len("/homeassistant") :].lstrip("/")
    current = ROOT

    for part in PurePosixPath(relative).parts:
        if part in ("", ".", ".."):
            continue
        current = current / part
        if current.exists() and current.is_symlink():
            raise PermissionError("Symlinks are not allowed")

    resolved = current.resolve(strict=False)
    root_resolved = ROOT.resolve()

    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PermissionError("Path escapes /homeassistant") from exc

    return logical, resolved


def can_read(logical):
    rw, ro, deny = policies()
    if matches(logical, deny):
        return False
    return matches(logical, rw) or matches(logical, ro)


def can_write(logical):
    rw, _, deny = policies()
    if matches(logical, deny):
        return False
    return matches(logical, rw)


def can_browse(logical):
    rw, ro, deny = policies()
    if matches(logical, deny):
        return False

    if can_read(logical):
        return True

    base = logical.rstrip("/")
    for pattern in rw + ro:
        prefix = pattern_prefix(pattern)
        if (
            prefix == base
            or prefix.startswith(base + "/")
            or base.startswith(prefix + "/")
        ):
            return True

    return False


class Handler(BaseHTTPRequestHandler):
    server_version = "HomeAssistantCodexBridge/0.2"

    def send_json(self, status, data):
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()

        if self.command != "HEAD":
            self.wfile.write(payload)

    def authorized(self):
        expected = "Bearer " + TOKEN
        supplied = self.headers.get("Authorization", "")
        return secrets.compare_digest(expected, supplied)

    def require_auth(self):
        if self.authorized():
            return True
        self.send_json(401, {"error": "unauthorized"})
        return False

    def requested_path(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        value = query.get("path", [None])[0]
        return parsed.path, value

    def do_GET(self):
        endpoint, raw = self.requested_path()

        if endpoint == "/health":
            self.send_json(
                200,
                {
                    "status": "ok",
                    "service": "home-assistant-codex-bridge",
                    "version": SERVICE_VERSION,
                },
            )
            return

        if not self.require_auth():
            return

        try:
            logical, fs_path = normalize_path(raw)

            if endpoint == "/list":
                self.handle_list(logical, fs_path)
                return

            if endpoint == "/file":
                self.handle_get_file(logical, fs_path, head=False)
                return

            self.send_json(404, {"error": "not found"})

        except PermissionError as exc:
            self.send_json(403, {"error": str(exc)})
        except (ValueError, OSError) as exc:
            self.send_json(400, {"error": str(exc)})

    def do_HEAD(self):
        endpoint, raw = self.requested_path()

        if endpoint == "/health":
            self.send_json(200, {"status": "ok"})
            return

        if not self.require_auth():
            return

        try:
            logical, fs_path = normalize_path(raw)

            if endpoint != "/file":
                self.send_json(404, {"error": "not found"})
                return

            self.handle_get_file(logical, fs_path, head=True)

        except PermissionError as exc:
            self.send_json(403, {"error": str(exc)})
        except (ValueError, OSError) as exc:
            self.send_json(400, {"error": str(exc)})

    def do_PUT(self):
        endpoint, raw = self.requested_path()

        if not self.require_auth():
            return

        if endpoint != "/file":
            self.send_json(404, {"error": "not found"})
            return

        try:
            logical, fs_path = normalize_path(raw)

            if not can_write(logical):
                raise PermissionError("write access denied")

            if fs_path.exists() and fs_path.is_dir():
                raise ValueError("target is a directory")

            parent = fs_path.parent
            if not parent.exists() or not parent.is_dir():
                raise ValueError("parent directory does not exist")

            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise ValueError("Content-Length is required")

            try:
                content_length = int(raw_length)
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc

            if content_length < 0 or content_length > MAX_WRITE:
                raise ValueError("file too large")

            body = self.rfile.read(content_length)

            fd, tmp_name = tempfile.mkstemp(prefix=".codex-write-", dir=str(parent))
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(body)
                    f.flush()
                    os.fsync(f.fileno())

                if fs_path.exists():
                    mode = fs_path.stat().st_mode & 0o777
                else:
                    mode = 0o644

                os.chmod(tmp_name, mode)
                os.replace(tmp_name, fs_path)

            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)

            self.send_json(
                200,
                {
                    "status": "written",
                    "path": logical,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                },
            )

        except PermissionError as exc:
            self.send_json(403, {"error": str(exc)})
        except (ValueError, OSError) as exc:
            self.send_json(400, {"error": str(exc)})

    def do_DELETE(self):
        endpoint, raw = self.requested_path()

        if not self.require_auth():
            return

        if endpoint != "/file":
            self.send_json(404, {"error": "not found"})
            return

        try:
            logical, fs_path = normalize_path(raw)

            if not can_write(logical):
                raise PermissionError("delete access denied")

            if not fs_path.exists():
                self.send_json(404, {"error": "file not found"})
                return

            if not fs_path.is_file():
                raise ValueError("only files may be deleted")

            fs_path.unlink()
            self.send_json(200, {"status": "deleted", "path": logical})

        except PermissionError as exc:
            self.send_json(403, {"error": str(exc)})
        except (ValueError, OSError) as exc:
            self.send_json(400, {"error": str(exc)})

    def do_POST(self):
        endpoint, raw = self.requested_path()

        if not self.require_auth():
            return

        if endpoint != "/mkdir":
            self.send_json(404, {"error": "not found"})
            return

        try:
            logical, fs_path = normalize_path(raw)

            if not can_write(logical):
                raise PermissionError("directory creation denied")

            if fs_path.exists():
                self.send_json(200, {"status": "exists", "path": logical})
                return

            if not fs_path.parent.exists():
                raise ValueError("parent directory does not exist")

            fs_path.mkdir(mode=0o755)
            self.send_json(201, {"status": "created", "path": logical})

        except PermissionError as exc:
            self.send_json(403, {"error": str(exc)})
        except (ValueError, OSError) as exc:
            self.send_json(400, {"error": str(exc)})

    def handle_get_file(self, logical, fs_path, head=False):
        if not can_read(logical):
            raise PermissionError("read access denied")

        if not fs_path.exists() or not fs_path.is_file():
            self.send_json(404, {"error": "file not found"})
            return

        size = fs_path.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(size))
        self.end_headers()

        if head:
            return

        with open(fs_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def handle_list(self, logical, fs_path):
        if not can_browse(logical):
            raise PermissionError("directory access denied")

        if not fs_path.exists() or not fs_path.is_dir():
            self.send_json(404, {"error": "directory not found"})
            return

        result = []

        with os.scandir(fs_path) as entries:
            for entry in sorted(entries, key=lambda item: item.name.lower()):
                if entry.is_symlink():
                    continue

                child_logical = (
                    logical.rstrip("/") + "/" + entry.name
                    if logical != "/"
                    else "/" + entry.name
                )

                if entry.is_dir(follow_symlinks=False):
                    if not can_browse(child_logical):
                        continue
                    result.append({"name": entry.name, "type": "directory"})

                elif entry.is_file(follow_symlinks=False):
                    if not can_read(child_logical):
                        continue

                    stat = entry.stat(follow_symlinks=False)
                    result.append(
                        {
                            "name": entry.name,
                            "type": "file",
                            "size": stat.st_size,
                            "mtime": int(stat.st_mtime),
                        }
                    )

        self.send_json(200, {"path": logical, "entries": result})


def main():
    address = ("0.0.0.0", 8443)
    server = ThreadingHTTPServer(address, Handler)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(
        certfile="/data/codex-file-bridge.crt",
        keyfile="/data/codex-file-bridge.key",
    )

    server.socket = context.wrap_socket(server.socket, server_side=True)

    print("Home Assistant Codex Bridge listening on HTTPS port 8443", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
