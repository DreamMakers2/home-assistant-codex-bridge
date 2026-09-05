#!/usr/bin/env python3
"""Read-only Codex JSONL token/context forensic analyzer.

The analyzer never treats a repeated usage event as a second model request and
never infers parent/resume membership from arbitrary prompt text. Exact
per-tool replay attribution remains unknown unless a future rollout format
persists serialized request/history membership.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import tiktoken  # type: ignore

    _ENC = tiktoken.get_encoding("o200k_base")

    def token_estimate(text: str) -> int:
        return len(_ENC.encode(text))

    TOKEN_METHOD = "o200k_base tokenizer estimate (model tokenizer/version not persisted)"
except Exception:

    def token_estimate(text: str) -> int:
        return math.ceil(len(text.encode("utf-8")) / 4)

    TOKEN_METHOD = "ceil(UTF-8 bytes/4), fallback estimate"

USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def output_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "".join(parts)
    return canonical(value)


def usage_from_event(event):
    payload = event.get("payload", {})
    if event.get("type") == "token_usage_record":
        return payload.get("usage"), "token_usage_record"
    if event.get("type") == "event_msg" and payload.get("type") == "token_count":
        return payload.get("info", {}).get("last_token_usage"), "event_msg/token_count"
    return None, None


def usage_key(usage) -> tuple:
    return tuple(int(usage.get(k) or 0) for k in USAGE_FIELDS)


def nonzero_usage(usage) -> bool:
    return any(int(usage.get(k) or 0) != 0 for k in USAGE_FIELDS)


def parse_ts(ts: str | None):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def dedupe_usage_rows(rows: list[dict]) -> tuple[list[dict], int]:
    """Prefer token_usage_record over nearby duplicate event_msg/token_count rows."""
    rows = sorted(rows, key=lambda r: (r["ordinal"], r["line"]))
    token_rows_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        if row["record_type"] == "token_usage_record":
            token_rows_by_key[usage_key(row["usage"])].append(row)

    logical: list[dict] = []
    duplicate_count = 0
    for row in rows:
        if row["record_type"] != "event_msg/token_count":
            logical.append(row)
            continue
        key = usage_key(row["usage"])
        duplicate = False
        for candidate in token_rows_by_key.get(key, []):
            ordinal_close = abs(candidate["ordinal"] - row["ordinal"]) <= 5
            a, b = parse_ts(candidate.get("timestamp")), parse_ts(row.get("timestamp"))
            time_close = bool(a and b and abs((a - b).total_seconds()) <= 2.0)
            if ordinal_close or time_close:
                duplicate = True
                break
        if duplicate:
            duplicate_count += 1
        else:
            logical.append(row)
    return logical, duplicate_count


def first_session_meta(events: list[dict]) -> dict:
    for event in events:
        if event.get("type") == "session_meta":
            return event.get("payload", {})
    return {}


def structured_thread_ids(events: list[dict]) -> set[str]:
    """Collect IDs only from structured session metadata, never free text."""
    ids: set[str] = set()
    for event in events:
        if event.get("type") != "session_meta":
            continue
        payload = event.get("payload", {})
        for key in ("session_id", "id", "thread_id", "parent_thread_id", "parent_id"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                ids.add(value)
    return ids


def load_events(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8", "replace")
    events, errors = [], []
    for line_no, line in enumerate(text.splitlines(), 1):
        try:
            event = json.loads(line)
            event["_line"] = line_no
            if event.get("ordinal") is None:
                event["ordinal"] = line_no
            events.append(event)
        except Exception as exc:
            errors.append({"line": line_no, "error": str(exc)})
    return raw, events, errors


def selected_by_seeds(events: list[dict], seeds: set[str]) -> tuple[bool, list[str]]:
    if not seeds:
        return True, []
    ids = structured_thread_ids(events)
    hits = sorted(ids & seeds)
    return bool(hits), hits


def context_window_id_at(meta: dict, compactions: list[dict], ordinal: int):
    initial = (
        (meta.get("context_window") or {}).get("window_id")
        if isinstance(meta.get("context_window"), dict)
        else None
    )
    active = initial
    for compaction in sorted(compactions, key=lambda c: c["ordinal"]):
        if compaction["ordinal"] >= ordinal:
            break
        if compaction.get("window_id"):
            active = compaction["window_id"]
    return active


def nearest_request(rows: list[dict], ordinal: int, direction: str):
    if direction == "before":
        candidates = [r for r in rows if r["ordinal"] < ordinal]
        return candidates[-1] if candidates else None
    candidates = [r for r in rows if r["ordinal"] > ordinal]
    return candidates[0] if candidates else None


def aggregate_groups(calls: list[dict], key: str):
    groups = defaultdict(list)
    for call in calls:
        groups[str(call.get(key))].append(call)
    out = []
    for group, values in groups.items():
        out.append(
            {
                "group": group,
                "call_count": len(values),
                "output_bytes": sum(v["output_bytes_utf8"] for v in values),
                "output_token_estimate": sum(v["output_token_estimate"] for v in values),
                "candidate_retained_request_count": sum(
                    v["candidate_later_requests_until_compaction"] for v in values
                ),
                "replay_mass_tokens": None,
                "potential_replay_mass_until_compaction": sum(
                    v["potential_replay_mass_until_compaction"] for v in values
                ),
            }
        )
    return sorted(
        out,
        key=lambda x: x["potential_replay_mass_until_compaction"],
        reverse=True,
    )


def linear_stats(points: list[tuple[int, int]]):
    if len(points) < 2:
        return {
            "n": len(points),
            "correlation_r": None,
            "slope": None,
            "intercept": None,
        }
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else None
    intercept = my - slope * mx if slope is not None else None
    r = sxy / math.sqrt(sxx * syy) if sxx and syy else None
    return {"n": len(points), "correlation_r": r, "slope": slope, "intercept": intercept}


def write_json(out: Path, name: str, value):
    (out / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def args_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(Path.home() / ".codex" / "sessions"),
        help="Codex sessions root",
    )
    parser.add_argument(
        "--out",
        default="/tmp/codex-token-usage-analysis",
        help="Output directory",
    )
    parser.add_argument(
        "--seed",
        action="append",
        default=[],
        help="Canonical/structured thread ID to include; repeatable",
    )
    parser.add_argument(
        "--seed-file",
        help="Text file containing thread IDs separated by whitespace",
    )
    return parser


def main() -> int:
    args = args_parser().parse_args()
    root, out = Path(args.root).expanduser(), Path(args.out).expanduser()
    seeds = set(args.seed)
    if args.seed_file:
        seeds.update(Path(args.seed_file).read_text(encoding="utf-8").split())
    out.mkdir(parents=True, exist_ok=True)

    parsed_files = []
    parse_errors = []
    for path in sorted(root.rglob("*.jsonl")):
        raw, events, errors = load_events(path)
        selected, seed_hits = selected_by_seeds(events, seeds)
        if not selected:
            continue
        rel = str(path.relative_to(root))
        for error in errors:
            parse_errors.append({"source_file": rel, **error})
        meta = first_session_meta(events)
        sid = meta.get("session_id") or meta.get("id") or path.stem
        parsed_files.append(
            {
                "path": path,
                "rel": rel,
                "raw": raw,
                "events": events,
                "meta": meta,
                "session_id": sid,
                "seed_hits": seed_hits,
                "structured_thread_ids": sorted(structured_thread_ids(events)),
            }
        )

    calls, raw_requests, requests, compactions, manifests = [], [], [], [], []
    per_file_requests: dict[str, list[dict]] = {}
    per_file_compactions: dict[str, list[dict]] = {}

    for item in parsed_files:
        rel = item["rel"]
        raw = item["raw"]
        events = item["events"]
        meta = item["meta"]
        sid = item["session_id"]
        fh = hashlib.sha256(raw).hexdigest()
        manifests.append(
            {
                "source_file": rel,
                "sha256": fh,
                "bytes": len(raw),
                "session_id": sid,
                "seed_matches_structured": item["seed_hits"],
                "structured_thread_ids": item["structured_thread_ids"],
                "events": len(events),
            }
        )

        ctx = meta.get("model_context_window")
        raw_req = []
        file_compactions = []
        for event in events:
            payload = event.get("payload", {})
            if event.get("type") == "turn_context":
                ctx = payload.get("model_context_window", ctx)
            usage, record_type = usage_from_event(event)
            if usage and nonzero_usage(usage):
                row = {
                    "source_file": rel,
                    "session_id": sid,
                    "ordinal": int(event.get("ordinal") or event["_line"]),
                    "line": event["_line"],
                    "timestamp": event.get("timestamp"),
                    "usage": usage,
                    "context_window": payload.get("info", {}).get(
                        "model_context_window", ctx
                    ),
                    "record_type": record_type,
                }
                raw_req.append(row)
                raw_requests.append(row)
            if event.get("type") == "compacted":
                history = payload.get("replacement_history", [])
                compact = {
                    "source_file": rel,
                    "session_id": sid,
                    "ordinal": int(event.get("ordinal") or event["_line"]),
                    "line": event["_line"],
                    "timestamp": event.get("timestamp"),
                    "replacement_history_items": len(history),
                    "replacement_history_sha256": hashlib.sha256(
                        canonical(history).encode()
                    ).hexdigest(),
                    "window_id": payload.get("window_id"),
                    "window_number": payload.get("window_number"),
                    "previous_window_id": payload.get("previous_window_id"),
                }
                file_compactions.append(compact)
                compactions.append(compact)

        logical, duplicate_count = dedupe_usage_rows(raw_req)
        for row in logical:
            row["context_window_id"] = context_window_id_at(
                meta, file_compactions, row["ordinal"]
            )
        per_file_requests[rel] = logical
        per_file_compactions[rel] = file_compactions
        requests.extend(logical)
        manifests[-1]["raw_usage_records_nonzero"] = len(raw_req)
        manifests[-1]["logical_request_records"] = len(logical)
        manifests[-1]["duplicate_usage_records_removed"] = duplicate_count

        outputs = {}
        for event in events:
            payload = event.get("payload", {})
            if event.get("type") == "response_item" and payload.get("type") in (
                "custom_tool_call_output",
                "function_call_output",
            ):
                outputs[payload.get("call_id")] = event

        for event in events:
            payload = event.get("payload", {})
            if not (
                event.get("type") == "response_item"
                and payload.get("type") in ("custom_tool_call", "function_call")
            ):
                continue
            call_id = payload.get("call_id")
            output_event = outputs.get(call_id)
            output_payload = output_event.get("payload", {}) if output_event else {}
            text = output_text(output_payload.get("output", "")) if output_event else ""
            nested = sorted(
                set(
                    re.findall(
                        r"tools\.(mcp__[A-Za-z0-9_]+)",
                        str(payload.get("input", payload.get("arguments", ""))),
                    )
                )
            )
            names = (
                nested
                if len(nested) == 1
                else (
                    [payload.get("name", "UNKNOWN")]
                    if not nested
                    else ["MULTIPLE_NESTED_MCP"]
                )
            )
            output_ordinal = int(
                (output_event or event).get("ordinal")
                or (output_event or event)["_line"]
            )
            logical = per_file_requests[rel]
            before = nearest_request(
                logical,
                int(event.get("ordinal") or event["_line"]),
                "before",
            )
            after = nearest_request(logical, output_ordinal, "after")
            boundary = next(
                (c for c in file_compactions if c["ordinal"] > output_ordinal),
                None,
            )
            end = boundary["ordinal"] if boundary else math.inf
            candidates = [
                r for r in logical if output_ordinal < r["ordinal"] < end
            ]
            for name in names:
                match = re.match(r"mcp__([^_]+)__(.+)", name)
                server = (
                    match.group(1)
                    if match
                    else (
                        "functions"
                        if payload.get("type") == "function_call"
                        else "codex"
                    )
                )
                tool = match.group(2) if match else name
                estimate = token_estimate(text)
                calls.append(
                    {
                        "call_key": f"{sid}:{call_id}:{name}",
                        "session_id": sid,
                        "seed_matches_structured": item["seed_hits"],
                        "source_file": rel,
                        "source_sha256": fh,
                        "call_id": call_id,
                        "wrapper_tool": payload.get("name"),
                        "exact_tool": name,
                        "nested_mcp_tools": nested,
                        "server": server,
                        "tool": tool,
                        "call_timestamp": event.get("timestamp"),
                        "call_ordinal": int(
                            event.get("ordinal") or event["_line"]
                        ),
                        "call_line": event["_line"],
                        "output_timestamp": (
                            output_event.get("timestamp") if output_event else None
                        ),
                        "output_ordinal": output_ordinal if output_event else None,
                        "output_line": output_event["_line"] if output_event else None,
                        "output_present": bool(output_event),
                        "output_bytes_utf8": len(text.encode()),
                        "output_payload_json_bytes_utf8": len(
                            canonical(output_payload.get("output", "")).encode()
                        ),
                        "output_token_estimate": estimate,
                        "output_token_method": TOKEN_METHOD,
                        "output_sha256": hashlib.sha256(text.encode()).hexdigest(),
                        "input_before_request": before["usage"] if before else None,
                        "input_after_request": after["usage"] if after else None,
                        "context_window": (after or before or {}).get(
                            "context_window"
                        ),
                        "context_window_id": context_window_id_at(
                            meta, file_compactions, output_ordinal
                        ),
                        "next_compaction_ordinal": (
                            boundary["ordinal"] if boundary else None
                        ),
                        "candidate_later_requests_until_compaction": len(
                            candidates
                        ),
                        "retained_requests_proven": None,
                        "retention_status": (
                            "UNKNOWN: serialized model request/history membership "
                            "is not persisted"
                        ),
                        "replay_mass_tokens": None,
                        "potential_replay_mass_until_compaction": (
                            estimate * len(candidates)
                        ),
                        "candidate_cached_input_tokens_sum": sum(
                            int(r["usage"].get("cached_input_tokens") or 0)
                            for r in candidates
                        ),
                        "candidate_uncached_input_tokens_sum": sum(
                            int(r["usage"].get("input_tokens") or 0)
                            - int(r["usage"].get("cached_input_tokens") or 0)
                            for r in candidates
                        ),
                        "evidence": {
                            "call_response_item_line": event["_line"],
                            "output_response_item_line": (
                                output_event["_line"] if output_event else None
                            ),
                            "next_compaction_line": (
                                boundary["line"] if boundary else None
                            ),
                        },
                    }
                )

    # Adjacent-request growth is direct evidence of whether persisted tool
    # output expands the next request, without claiming exact retained replay.
    growth_intervals = []
    calls_by_file = defaultdict(list)
    for call in calls:
        calls_by_file[call["source_file"]].append(call)
    for rel, logical in per_file_requests.items():
        logical = sorted(logical, key=lambda r: r["ordinal"])
        boundaries = per_file_compactions[rel]
        for left, right in zip(logical, logical[1:]):
            if any(
                left["ordinal"] < compact["ordinal"] < right["ordinal"]
                for compact in boundaries
            ):
                continue
            interval_calls = [
                call
                for call in calls_by_file[rel]
                if call.get("output_ordinal") is not None
                and left["ordinal"] < call["output_ordinal"] < right["ordinal"]
            ]
            total_out = sum(
                call["output_token_estimate"] for call in interval_calls
            )
            input_left = int(left["usage"].get("input_tokens") or 0)
            input_right = int(right["usage"].get("input_tokens") or 0)
            growth_intervals.append(
                {
                    "source_file": rel,
                    "session_id": left["session_id"],
                    "from_request_ordinal": left["ordinal"],
                    "to_request_ordinal": right["ordinal"],
                    "tool_call_count": len(interval_calls),
                    "tool_output_token_estimate": total_out,
                    "input_tokens_before": input_left,
                    "input_tokens_after": input_right,
                    "input_token_delta": input_right - input_left,
                }
            )

    points_all = [
        (g["tool_output_token_estimate"], g["input_token_delta"])
        for g in growth_intervals
        if g["tool_output_token_estimate"] > 0
    ]
    points_single = [
        (g["tool_output_token_estimate"], g["input_token_delta"])
        for g in growth_intervals
        if g["tool_call_count"] == 1 and g["tool_output_token_estimate"] > 0
    ]
    growth_stats = {
        "all_nonzero_tool_intervals": linear_stats(points_all),
        "single_tool_output_intervals": linear_stats(points_single),
    }

    summary = {
        "raw_nonzero_usage_records": len(raw_requests),
        "logical_request_records": len(requests),
        "duplicate_usage_records_removed": len(raw_requests) - len(requests),
        "by_tool": aggregate_groups(calls, "exact_tool"),
        "by_server": aggregate_groups(calls, "server"),
        "by_transcript": aggregate_groups(calls, "session_id"),
        "tool_output_vs_next_request_growth": growth_stats,
    }

    context_growth = []
    for sid in sorted({r["session_id"] for r in requests}):
        values = [r for r in requests if r["session_id"] == sid]
        inputs = [int(r["usage"].get("input_tokens") or 0) for r in values]
        context_growth.append(
            {
                "session_id": sid,
                "logical_requests": len(values),
                "first_input_tokens": inputs[0] if inputs else None,
                "last_input_tokens": inputs[-1] if inputs else None,
                "max_input_tokens": max(inputs) if inputs else None,
                "input_growth_first_to_last": (
                    inputs[-1] - inputs[0] if inputs else None
                ),
                "input_tokens_sum": sum(inputs),
                "cached_input_tokens_sum": sum(
                    int(r["usage"].get("cached_input_tokens") or 0)
                    for r in values
                ),
                "cache_write_input_tokens_sum": sum(
                    int(r["usage"].get("cache_write_input_tokens") or 0)
                    for r in values
                ),
                "context_windows": sorted(
                    {
                        r.get("context_window")
                        for r in values
                        if r.get("context_window") is not None
                    }
                ),
                "context_window_ids": sorted(
                    {
                        r.get("context_window_id")
                        for r in values
                        if r.get("context_window_id")
                    }
                ),
                "compactions": sum(c["session_id"] == sid for c in compactions),
            }
        )

    write_json(out, "calls.json", calls)
    write_json(out, "requests_raw.json", raw_requests)
    write_json(out, "requests.json", requests)
    write_json(out, "source_manifest.json", manifests)
    write_json(out, "compactions.json", compactions)
    write_json(out, "parse_errors.json", parse_errors)
    write_json(out, "context_growth.json", context_growth)
    write_json(out, "tool_growth_intervals.json", growth_intervals)
    write_json(out, "summary.json", summary)

    columns = sorted(
        {
            key
            for call in calls
            for key in call
            if key not in ("input_before_request", "input_after_request", "evidence")
        }
    )
    with (out / "calls.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for call in calls:
            writer.writerow(
                {
                    key: (
                        json.dumps(call.get(key), ensure_ascii=False)
                        if isinstance(call.get(key), (list, dict))
                        else call.get(key)
                    )
                    for key in columns
                }
            )

    top = sorted(
        calls,
        key=lambda call: call["potential_replay_mass_until_compaction"],
        reverse=True,
    )
    lines = [
        "# Codex token/context forensic analysis",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}  ",
        (
            f"In scope: **{len(parsed_files)} JSONLs**, **{len(calls)} tool-call "
            f"records**, **{len(requests)} logical model requests** "
            f"({len(raw_requests) - len(requests)} duplicate usage records removed), "
            f"**{len(compactions)} compactions**."
        ),
        "",
        "## Finding and limits",
        "",
        (
            "**Exact individual replay mass is not provable from current rollout "
            "JSONLs.** They persist ordered history items and aggregate request usage, "
            "but not the serialized request body or per-history-item cache attribution. "
            "`replay_mass_tokens` therefore remains null; "
            "`potential_replay_mass_until_compaction` is explicitly a diagnostic "
            "counterfactual, not billed usage."
        ),
        "",
        (
            "Selection is based only on canonical/structured session metadata. "
            "Arbitrary prompt text containing a seed ID does not put a transcript in "
            "scope. Duplicate `token_usage_record` + `event_msg/token_count` "
            "representations of one request are collapsed, preferring "
            "`token_usage_record`."
        ),
        "",
        "## Tool-output growth evidence",
        "",
        f"Token estimate: {TOKEN_METHOD}.",
        (
            "All nonzero tool intervals regression: `"
            + json.dumps(growth_stats["all_nonzero_tool_intervals"])
            + "`."
        ),
        (
            "Single-tool-output intervals regression: `"
            + json.dumps(growth_stats["single_tool_output_intervals"])
            + "`."
        ),
        "",
        "## Top potential pathological outputs",
        "",
        "|rank|call|tool/server|output est.|candidate logical requests|potential replay mass|",
        "|---:|---|---|---:|---:|---:|",
    ]
    for index, call in enumerate(top[:30], 1):
        lines.append(
            f"|{index}|`{call['call_key']}`|`{call['exact_tool']}` / "
            f"`{call['server']}`|{call['output_token_estimate']:,}|"
            f"{call['candidate_later_requests_until_compaction']:,}|"
            f"{call['potential_replay_mass_until_compaction']:,}|"
        )
    for title, key in (
        ("By tool", "by_tool"),
        ("By server", "by_server"),
        ("By transcript", "by_transcript"),
    ):
        lines += [
            "",
            f"## {title}",
            "",
            "|group|calls|output est.|candidate logical requests|potential replay mass|",
            "|---|---:|---:|---:|---:|",
        ]
        for row in summary[key][:30]:
            lines.append(
                f"|`{row['group']}`|{row['call_count']:,}|"
                f"{row['output_token_estimate']:,}|"
                f"{row['candidate_retained_request_count']:,}|"
                f"{row['potential_replay_mass_until_compaction']:,}|"
            )
    lines += [
        "",
        "## Artifacts",
        "",
        "- `requests_raw.json`: raw non-zero usage emissions.",
        "- `requests.json`: de-duplicated logical model requests.",
        "- `calls.json` / `calls.csv`: persisted tool calls and outputs.",
        "- `tool_growth_intervals.json`: adjacent-request input growth versus intervening tool-output estimates.",
        "- `context_growth.json`: context/input trajectory by transcript.",
        "- `source_manifest.json`, `compactions.json`, `parse_errors.json`: verification ledger.",
        "- `summary.json`: sortable aggregates and regression diagnostics.",
        "",
        (
            "Reproduce: `python3 token_usage_analyzer/analyze.py --root "
            f"{root} --out {out}` plus any required `--seed` arguments."
        ),
    ]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(
        f"logical requests={len(requests)} raw usage records={len(raw_requests)} "
        f"duplicates removed={len(raw_requests) - len(requests)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
