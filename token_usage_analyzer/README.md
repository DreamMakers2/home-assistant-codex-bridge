# Codex token usage analyzer

`analyze.py` performs a read-only forensic pass over local Codex rollout JSONLs. It de-duplicates paired `token_usage_record` / `event_msg token_count` emissions into logical model requests, scopes optional seed IDs only through structured `session_meta` lineage rather than arbitrary prompt text, records persisted context-window IDs when available, and measures adjacent-request input growth against intervening tool-output size.

It deliberately does **not** claim exact per-tool replay attribution: current rollout JSONLs do not persist serialized model request bodies or per-history-item cache attribution. `potential_replay_mass_until_compaction` is therefore a diagnostic counterfactual, not billed usage.

Typical use:

```bash
python3 token_usage_analyzer/analyze.py \
  --root ~/.codex/sessions \
  --out /tmp/codex-token-usage-analysis \
  --seed <PARENT_OR_RESUME_THREAD_ID>
```

Repeat `--seed` for multiple parent/resume IDs, use `--seed-file PATH` for a whitespace-separated list, or omit seeds to analyze every JSONL below the root. The analyzer writes JSON/CSV plus `REPORT.md`; it never modifies the source sessions.
