Act as a senior Home Assistant/Lovelace, scientific-data integration, Python/Kafka/MQTT, and frontend visualization engineer. Own this hobby project end-to-end, with emphasis on scientific usefulness, least privilege, reliable data handling, and a polished dense single-screen UI.

# HA Scientific Dashboard — autonomous implementation brief

Use: https://github.com/DreamMakers2/home-assistant-codex-bridge

Read that repository’s `CODEX_REFERENCE.md` and the local workspace `AGENTS.md` first. Treat the local `AGENTS.md`, bridge policy, Codex sandbox, and your own safety/access restrictions as authoritative boundaries.

## Operating mode and autonomy

- Use the latest GPT model exposed by this Codex CLI installation that supports `x-high`/`xhigh` reasoning, and run at that reasoning level.
- Explicitly use subagents whenever independent work can be parallelized or a second opinion can improve quality. Appropriate delegation includes environment exploration, individual API/source verification, data architecture, Home Assistant integration checks, browser/visual testing, and independent code/config review. Prefer the same latest model at x-high reasoning for subagents; if the runtime makes subagents inherit the parent model/effort, keep the parent on the required model/effort. Do not deliberately downgrade agents to cheaper/faster models.
- If Codex CLI supports Plan mode, use it first for the exploration and implementation plan. After the plan is complete, if the CLI exposes an explicit Goal/Follow-a-goal mode, switch to it and use the Definition of Done below as the durable goal. If no such Goal mode exists, continue in the normal autonomous execution mode. Do not stop after planning.
- Execute the full cycle autonomously: **explore → plan → implement → validate/test → review → improve → re-test → independent final review**.
- Do not ask me routine implementation questions or request confirmations. Infer reasonable choices from the environment and this brief.
- If an unavoidable external prerequisite or permission boundary blocks one part of the project, do not bypass the boundary and do not fabricate success. Continue all unblocked work, adapt where safely possible, and report the exact blocker and smallest manual prerequisite at the end.
- Keep this a hobby project: avoid production-scale error-handling frameworks, elaborate auth schemes, excessive abstractions, or infrastructure that is not needed for this dashboard.

## Mandatory exploration run before planning

Before creating the implementation plan, perform a real exploration run and establish what can actually be done autonomously.

At minimum verify:

1. Codex CLI/runtime capabilities:
   - version;
   - available model/reasoning controls;
   - Plan mode and any Goal/Follow-a-goal mode;
   - subagent/collaboration support;
   - browser/Playwright availability.

2. Bridge and filesystem boundary:
   - bridge/`ha-sync` health;
   - actual read/write/read-only/deny behavior;
   - availability of `/homeassistant/packages/codex/**`;
   - `configuration.yaml` package/theme include structure;
   - permitted logs and existing config relevant to this task;
   - never attempt to bypass policy.

3. Home Assistant:
   - HA version and relevant enabled integrations;
   - ability to validate configuration and perform safe reloads;
   - MQTT availability and suitability;
   - Recorder/history/long-term-statistics behavior relevant to the project;
   - available persistent runtime/storage options for collectors and the one-year archive;
   - whether a continuously running SCiMMA/Kafka collector is possible within current permissions;
   - current entities that can help identify appropriate local stations/regions where a data source is location-dependent.

4. Lovelace/frontend:
   - inspect existing dashboards only for visual inspiration;
   - inventory already-installed HACS frontend cards/resources and their usable versions;
   - verify a completely new dashboard can be created without modifying any existing dashboard;
   - verify browser viewport control and both collapsed and expanded Home Assistant sidebar states.

5. Secrets:
   - inspect secret **alias names only** through the bridge-supported mechanism;
   - verify required credentialed APIs can be exercised through supported Home Assistant/bridge methods without reading or exposing the secret values;
   - never print, copy, infer, recover, or persist secret values.

6. External data sources:
   - verify current official API/feed documentation and practical reachability for every source below;
   - identify schema/rate-limit/authentication changes before implementing against them;
   - make small representative calls only during exploration;
   - verify the intended extracted fields are actually available.

7. Runtime/network blockers:
   - verify outbound access needed by HTTP APIs and SCiMMA Kafka;
   - identify any permission, runtime, package-install, persistent-process, storage, MQTT, browser, or HA limitation that would prevent autonomous completion.

Do not create the implementation plan until this exploration is complete.

## Scope

Build a **completely new Lovelace dashboard** for dense scientific/environmental/astronomical monitoring. Do **not** modify, replace, migrate, or delete any existing dashboard. Existing dashboards may be inspected for visual/layout inspiration only.

Do not add the previously discussed finance or gaming content.

The scientific project scope is:

### Space weather
- NOAA SWPC:
  - planetary Kp;
  - solar-wind speed;
  - IMF Bz;
  - other compact space-weather values already discussed, such as useful X-ray activity, only where they materially improve the dashboard.
- NMDB cosmic rays:
  - current rate/count or equivalent available metric;
  - useful short-term anomaly/change.

### Earth and near-Earth events
- USGS earthquakes:
  - strongest recent event;
  - nearest notable event;
  - useful recent event activity/history.
- NASA/JPL close approaches:
  - next/nearest useful NEO close approach information.
- NASA/JPL fireballs:
  - latest useful fireball event and relevant scientific values.

### Atmosphere, climate, fire, water and ocean
- OpenAQ:
  - local/relevant research-grade PM2.5;
  - add PM10/NO2 only if the chosen station/source supports them cleanly and they improve the dashboard.
- NASA FIRMS:
  - regional active-fire/hotspot information and useful aggregate metrics.
- NOAA atmospheric CO2:
  - current concentration/trend/change useful for the dashboard.
- NSIDC sea ice:
  - current extent and/or anomaly/trend appropriate to the available public dataset.
- USGS Water:
  - relevant local/nearest useful river discharge/flow and gauge height where available.
- NOAA/NDBC:
  - relevant nearest useful ocean/coastal conditions where available.

### Biodiversity, research and exoplanets
- GBIF:
  - a compact, scientifically meaningful local/recent biodiversity metric using the available occurrence data.
- OpenAlex:
  - the previously discussed compact scientific “research pulse”; choose a simple, explainable query/metric that fits the dashboard rather than building a research analytics system.
- NASA Exoplanet Archive:
  - compact counts/recent-discovery information suitable for this dashboard.

### Gravitational-wave observatories / SCiMMA
Use the existing SCiMMA access for:
- `igwn.gwalert`;
- `igwn.gwistat.H1`;
- `igwn.gwistat.H1.range_history`;
- `igwn.gwistat.L1`;
- `igwn.gwistat.L1.range_history`;
- `igwn.gwistat.V1`;
- `igwn.gwistat.V1.range_history`;
- `igwn.gwistat.K1`;
- `igwn.gwistat.K1.range_history`.

For gravitational-wave alerts:
- distinguish production `S...`, mock `MS...`, and test `TS...` superevents;
- model the alert lifecycle correctly: PRELIMINARY / INITIAL / UPDATE / RETRACTION;
- keep “latest received message” separate from “latest active non-retracted production candidate”;
- extract useful dashboard fields such as event/superevent ID, time, alert type, FAR, significance, instruments, pipeline/group/search, classification probabilities, source properties, and any useful derived scalar localization information that can be obtained without retaining raw blobs;
- never persist raw Avro packets, FITS/skymap binary payloads, or other raw Kafka payloads.

Known prior validation from this project: `igwn.gwalert` authentication and Avro decoding were successfully tested with mock events; an archived **production** notice `S250818k-update.avro` was also successfully decoded and GraceDB confirmed it had been sent to `kafka.scimma.org/igwn.gwalert`. Treat that as prior evidence; do not waste time repeating large historical scans unless needed to validate your implementation.

## Data architecture and retention

Choose the smallest architecture that the exploration proves can run reliably within the current permissions. Prefer the previously discussed lightweight collector/MQTT approach for feeds that need parsing or continuous streaming when MQTT and a suitable persistent runtime are already available. Simpler REST/template/native HA mechanisms are acceptable for straightforward sources. Do not add a new heavyweight platform just to satisfy architectural preference.

Requirements:

- Retain useful extracted historical data for **up to 365 days**.
- **Per individual API/data source, maximum persisted database footprint is 2 GB.**
- When a source reaches its 2 GB cap, delete that source’s oldest historical records first until it is below the limit.
- Time-based retention also removes records older than 365 days.
- Use a storage layout that makes the per-source cap reliably enforceable.
- **Never store raw API responses, raw Kafka messages, raw Avro containers, FITS/skymap blobs, or other raw payloads. Store only fields actually needed by the dashboard/history plus minimal IDs/timestamps required for deduplication and lifecycle handling.**
- Avoid duplicate historical rows when APIs return overlapping windows.
- Keep Home Assistant current-state entities clean and useful; do not flood Recorder with high-cardinality/raw attributes.
- For longer-history visualization, use the retained extracted archive and/or HA long-term statistics as appropriate to the capabilities found during exploration.
- Fetch incrementally/compactly where practical; do not repeatedly download large historical payloads to obtain a single current value.

Previously assumed sensible cadences may be used as defaults unless current source semantics/API limits justify a different choice:
- SWPC: about 5 min;
- NMDB: about 5 min;
- earthquakes: about 5 min incremental;
- JPL close approaches/fireballs: about hourly;
- OpenAQ: about hourly;
- FIRMS regional aggregates: about hourly;
- OpenAlex: about every 6 h;
- NSIDC: daily;
- NOAA CO2: daily;
- GBIF: about every 6 h;
- USGS Water: about 15 min;
- NDBC: about hourly;
- Exoplanet Archive: daily;
- SCiMMA/IGWN: continuous/event-driven.

Use current official source documentation to adjust these only where appropriate.

## Dashboard UX and visual requirements

The dashboard is a dense, scientific command center intended to fit on one desktop screen.

Visual direction:
- use the existing **Noctis** theme/visual language where available;
- preserve the dense dark command-center aesthetic, colors, spacing, and compactness established in the existing statistics dashboard, but build this dashboard from scratch;
- no internal title/header card;
- use already-installed HACS cards where they genuinely improve the result; inspect what is installed rather than assuming versions;
- likely useful existing cards include `layout-card`, `card-mod`, Mushroom, `apexcharts-card`, `stack-in-card`, and `mini-graph-card`, but use the actual installed inventory and choose the most suitable components;
- do not install/update/remove HACS packages unless the local operating contract already explicitly authorizes it; the task is designed to use what is already installed.

Grouping:
- represent every source in a useful way, but not every source requires a dedicated large card;
- combine closely related sources into coherent panels to preserve density;
- prioritize high-information KPI tiles plus compact charts/tables/event summaries;
- make current state immediately readable while retaining access to meaningful history;
- avoid decorative empty space.

### Resolution priority

**Primary target — highest priority: `2560 × 1285`.**

At 2560×1285:
- optimize the entire dashboard for this viewport first;
- test with the Home Assistant sidebar **expanded and collapsed**;
- there must be **no vertical scrollbar, no horizontal scrollbar, no overflowing cards, no clipped/overlapping elements, and no overlapping/clipped text** in either sidebar state;
- spacing, margins, card heights, chart heights, typography, legends, axes, and responsive grid behavior must all be polished at this exact size.

Secondary targets:
- `1920 × 965`;
- `2752 × 997`.

For both secondary resolutions:
- test sidebar expanded and collapsed;
- optimize them after the primary target;
- no scrollbars, overflow, overlap, or clipped text;
- preserve useful density and readable charts even if individual panel proportions must adapt.

Do not solve fit problems by shrinking text to an unreadable size or hiding core scientific content. Refine the grid/card composition instead.

## Location-dependent sources

Where OpenAQ, FIRMS, USGS Water, NDBC, GBIF, or another source needs a geographic reference, use the existing Home Assistant home/location context or nearest scientifically useful station/region discovered during exploration. Do not expose exact home coordinates in logs, prompts, commits, or the final report.

## Home Assistant integration rules

- Create supporting YAML only in locations permitted by the active bridge policy, with project-owned logic under `/homeassistant/packages/codex/**` where appropriate.
- `configuration.yaml` is read-only unless the active local contract says otherwise; do not try to bypass that. If a required package/theme include is absent, treat it as an external prerequisite and continue everything else possible.
- Use safe reloads where supported.
- **Do not restart Home Assistant without explicit approval.** This task is intended to complete without a full restart. If a restart is the only remaining prerequisite, leave it as a clearly documented final blocker/manual step.
- **Do not perform ESPHome OTA/install.** ESPHome is not part of this dashboard unless exploration proves some existing entity is merely being read; do not expand scope into device firmware.
- Do not use root, sudo, SSH, SCP/SFTP, Supervisor shell, or host/system access.
- Do not read or modify `.storage` directly. Lovelace may be managed through the authorized Home Assistant UI.
- Do not read HA databases/backups or any denied paths.
- Do not change authentication, users, network/security settings, or privilege boundaries.
- Do not modify unrelated automations, scripts, scenes, integrations, devices, entities, themes, or dashboards.

## Secrets and credentials

API keys and credentials required for this project already exist through secrets/bridge-supported methods.

- Use existing secret alias names and supported Home Assistant/codex-bridge mechanisms to exercise credentialed APIs.
- Never read, print, log, copy, commit, infer, reconstruct, or expose secret values.
- Do not hard-code credentials into YAML, collectors, dashboard configuration, test fixtures, URLs, command history, or Git.
- A secret being unreadable to Codex is expected; that alone is not a blocker if it can be consumed through the supported mechanism.
- If a required alias is genuinely missing, continue all other work and report the exact alias name needed at the end rather than asking me during the run.

## Implementation and test cycle

After exploration, produce a concrete implementation plan in Plan mode, then execute it fully.

For each logical phase:
1. implement the smallest coherent slice;
2. validate configuration/code;
3. deploy through the allowed bridge/UI path;
4. safely reload if applicable;
5. verify live data/state;
6. inspect logs plus browser console/network errors relevant to the change;
7. visually inspect the rendered result;
8. fix defects before moving on.

For data ingestion/history:
- verify parsing against real representative responses;
- verify deduplication/lifecycle handling;
- verify timestamp/unit handling;
- verify stale/unavailable source behavior is understandable without building a large fault-management framework;
- verify 365-day pruning and 2 GB/source oldest-first pruning logic without generating multi-gigabyte test data;
- verify raw payloads are not being persisted.

For Lovelace:
- use Playwright/browser testing, not YAML inspection alone;
- render and inspect all three target resolutions;
- test expanded and collapsed sidebar at each resolution;
- inspect browser console and failed network requests;
- verify data actually populates;
- verify charts/legends/axes/text do not collide;
- verify there is no page or card overflow/scrollbar;
- iterate until the primary viewport is visually polished and the secondary viewports are solid.

## Review requirements

Use subagents for independent review where available.

After the first complete implementation:
- run an independent technical review of data ingestion, retention, secret handling, HA integration, and change scope;
- run an independent visual/layout review against the exact viewport/sidebar matrix;
- fix justified findings;
- re-run affected tests;
- perform a final independent review after improvements.

Do not accept “works in YAML” as done if the actual dashboard is visually broken or empty.

Use local Git for change tracking and make sensible known-good commits for substantial completed phases. Do not add a remote, expose secrets, or force-add ignored credential/session files.

## Definition of Done

The task is complete only when, within the access actually available:

- exploration found and documented the real autonomous capability boundary before planning;
- a completely new scientific Lovelace dashboard exists and no existing dashboard was modified;
- every scoped scientific source is either integrated and populated or has a precise externally imposed blocker documented;
- SCiMMA/IGWN alert and detector/range data are correctly parsed with production/mock/test and retraction semantics;
- historical extracted data is retained up to 365 days with a hard 2 GB/source cap and oldest-first pruning;
- no raw external payloads are persisted;
- secrets remain inaccessible/unexposed;
- Home Assistant configuration validates;
- safe reloads needed by the implementation succeed;
- the dashboard is functional and visually polished at **2560×1285** with both sidebar states and has **zero scrollbars/overflow/overlap**;
- `1920×965` and `2752×997` are also tested in both sidebar states and have zero scrollbars/overflow/overlap;
- browser console/network issues introduced by the project are resolved;
- an independent review has been performed, findings addressed, and a final review completed;
- known-good work is committed locally;
- the final report is concise and includes: what was created, dashboard path/name, integrated source status, retention/storage implementation, tests performed, viewport/sidebar results, commits, and any remaining hard blockers/manual prerequisite.

Do not stop at a design, YAML draft, or partial proof of concept. Carry the project as far through the full implement → test → review → improve → review cycle as the established permissions and safety boundaries allow.
