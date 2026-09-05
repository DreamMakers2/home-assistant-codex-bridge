Act as an expert Home Assistant/Lovelace, HACS frontend, Home Assistant data/Recorder, API-integration, and browser-based visual QA engineer.
Own this project end-to-end and deliver a polished, verified implementation within the existing least-privilege environment.

# Project: HA Statistics Dashboard

Use https://github.com/DreamMakers2/home-assistant-codex-bridge

Read `CODEX_REFERENCE.md` from that repository and the local workspace `AGENTS.md` before doing anything else. Treat the local `AGENTS.md` and your own access/safety restrictions as the active operating contract.

If Codex CLI supports Plan/Goal collaboration modes, use this sequence:
1. **Plan mode:** exploration run first, then the implementation plan.
2. **Goal mode:** execute the approved-by-this-prompt plan autonomously through completion.
If those modes are unavailable, emulate the same sequence internally without pausing for user approval.

Do not ask me questions during normal execution. Resolve ambiguity by inspecting the environment and choosing the smallest conservative solution consistent with this prompt. If a hard capability/security boundary makes a requirement impossible, do not circumvent it: continue all independent work, leave only the blocked portion undone, and document the exact blocker in the final report.

### Context-efficiency requirement

Preserve the complete implementation → test → independent review → improve → affected re-test → final main-agent regression structure below. Token efficiency does **not** authorize skipping required live-data checks, the viewport/sidebar matrix, independent reviews, justified fixes, or the final regression pass. Reduce avoidable context growth instead: use targeted/bounded searches and excerpts rather than broad dumps; filter or summarize large command/API/log/diff output locally; save bulky evidence to temporary files and retrieve only relevant slices; avoid rereading unchanged material; and for Playwright prefer targeted element lookup, compact evaluations and decisive screenshots over repeated full accessibility snapshots or broad console/network histories.

## 1. Mandatory exploration run before planning

Before writing the implementation plan or making project changes, perform a read-only exploration sufficient to determine whether the work can be completed autonomously. Verify at minimum:

- Home Assistant version/runtime characteristics relevant to Lovelace, Recorder/statistics, REST/templates, and reload/validation behavior.
- Actual codex-bridge file permissions and the local `AGENTS.md` authorization contract.
- Browser/Playwright availability and the dedicated Home Assistant UI account's effective capabilities.
- Existing dashboards, dashboard mode/storage behavior, Lovelace resources, and theme setup. Existing dashboards may be inspected for inspiration only.
- Installed HACS frontend cards/resources and their usable versions/config syntax.
- Existing packages and entities relevant to this project; identify duplicates, legacy entities, unavailable entities, units, attributes, update rates, history/statistics eligibility, and naming conflicts.
- Current Recorder/history/statistics configuration that affects one-year retention and database growth.
- Availability and behavior of existing API/data sources using permitted secret aliases without reading secret values.
- API free-tier/rate-limit constraints relevant to the intended polling.
- Whether all required data can be represented without persisting raw API payloads.
- Whether the new dashboard can be created, rendered, edited, validated, and visually tested without modifying an existing dashboard.
- Any environmental, permission, API, browser, storage, or tooling limitation that would prevent a fully autonomous implement → test → review → improve → review cycle.

Use subagents for independent exploration when it materially improves speed, quality, or independent verification; avoid duplicate parallel exploration that merely re-reads the same broad context. Do not make implementation changes until the exploration is complete.

## 2. Scope and isolation

Create a **completely new Lovelace dashboard** for this project. Give it a distinct non-conflicting dashboard identity. **Do not modify any existing dashboard or existing dashboard view.** Existing dashboards may be read/inspected only.

Reuse existing working entities/packages where appropriate instead of duplicating them. New supporting Home Assistant YAML/templates/entities required for this project must stay within the file paths authorized by the local contract, normally `/homeassistant/packages/codex/**`. Do not modify unrelated packages, automations, scripts, scenes, integrations, devices, security settings, or network settings.

Do not use root, sudo, SSH/SCP/SFTP, HAOS shell access, `.storage`, Home Assistant database files, backups, secret values, browser profile/cookies, or any privilege/network expansion.

Existing secret aliases/credentials may be referenced and used by supported Home Assistant/codex-bridge methods. Never read, print, infer, recover, hard-code, or expose secret values. Discover permitted alias names from the local secret-name mechanism if available.

This is a hobby project. Prefer the simplest maintainable Home Assistant-native solution that meets the goal. Do not introduce production-scale error-handling frameworks, elaborate authentication systems, unnecessary services, or architecture that is disproportionate to the dashboard.

## 3. Dashboard goal

Build a dense, high-information, single-screen desktop Statistics dashboard that is useful at a glance and visually polished. It should preserve the visual direction already established in the existing Statistics work while being implemented as a new dashboard:

- dark/Noctis-compatible visual treatment;
- compact spacing and strong information density;
- subtle gradients/borders rather than heavy decoration;
- Bitcoin/crypto: amber;
- traditional financial data: blue/purple;
- CS2/Steam: cyan;
- energy/computer/server: green;
- no unnecessary content-title/header card consuming vertical space;
- useful information only;
- no scrolling.

Prefer already-installed HACS frontend cards when they materially improve the result. Known installed options include layout-card, card-mod, Mushroom, ApexCharts Card, mini-graph-card, Stack In Card, Vertical Stack In Card, Plotly Graph Card, Tabbed Card, Gauge Card Pro, Bubble Card, Catppuccin Theme, and the other HACS resources already present in the system. Inspect actual installed resources before relying on them. Do not install new HACS packages merely to solve something already supported by installed cards.

## 4. Required dashboard data/content

Inspect the live system first and reuse valid existing entities. Create only missing/necessary normalized entities.

### Bitcoin / CoinGecko
Use USD data and present:
- current BTC/USD;
- 24-hour percentage change;
- 24-hour volume;
- market capitalization;
- detailed historical price visualization;
- useful volume context.

The previously established polling target is approximately 10 minutes for lightweight live BTC data. Historical/time-series handling must obey the storage rules below; do not persist rolling raw API response arrays merely to draw charts.

### Traditional market / Alpha Vantage
Use SPY as the S&P 500 proxy and present:
- latest close/value;
- daily percentage change;
- latest day range;
- useful historical trend;
- 20-day moving-average context where supported by the available data.

The previously established Alpha Vantage polling target is approximately every 2 hours and must remain compatible with the free-plan request budget. Do not add extra Alpha Vantage symbols that would exceed the available free-tier allowance.

### Counter-Strike 2 player activity
Use the existing CS2 current-player data if valid and present:
- current concurrent players;
- useful recent player-activity history;
- a smoothed/hourly-average context where useful.

### PriceEmpire: overall CS2 market
Use PriceEmpire to show overall CS2-market condition rather than only individual skins. Include the useful metrics available from the current API/environment, such as:
- market/index breadth;
- average 1-day, 7-day, and 30-day change where available;
- Cases, Collections, Tournaments, and Liquid category/index performance;
- leading/largest and/or most-active returned market index where meaningful;
- top daily gainer and loser where useful;
- reported volume/sales only with accurate labeling;
- a stable Chroma Case index with value/activity/sales-change context where available.

Do **not** present overlapping PriceEmpire insight/index sums as an exact global CS2 market capitalization or exact whole-market trade tape. Label samples/proxies honestly. If using cumulative `total_sold` changes as activity, present them as activity for that returned index/sample, not exact global trades/hour.

PriceEmpire responses can be very large. Poll PriceEmpire **once per day** unless exploration proves a specific lightweight call is both necessary and safely within the established constraints. Keep total PriceEmpire usage comfortably within the free-plan allowance.

### Personal CS2 inventory / PriceEmpire
Use the two existing portfolios:
- cash/YouPin portfolio slug: `cs2-292`;
- Steam-priced portfolio slug: `cs2-steam-6`.

Present compact, useful portfolio information where available:
- cash/YouPin inventory value;
- Steam inventory value;
- Steam-vs-cash premium in USD and percent;
- item count;
- 24-hour change/value change;
- ROI/invested value where meaningful;
- best/worst performer only if it improves the dashboard without clutter.

Do not persist full inventory item arrays, image metadata, descriptions, prices-by-market arrays, palette data, or transaction arrays.

### Computer/server energy
Use the existing computer/server monthly energy sensor if valid and present:
- current/monthly energy;
- useful recent history;
- daily increase/consumption context where derivable correctly.

## 5. Data retention, storage, and raw-payload rules

Design the data model for **up to one year of useful history** for dashboard elements.

For **each individual API/data source**, the maximum allowed database footprint attributable to that source is **2 GB**. Once retaining additional history would exceed that source's 2 GB budget, remove historical data **oldest-first** while preserving the newest useful data. A source with multiple derived entities shares that source's 2 GB budget.

Raw external API payloads must not be persistently stored. Process them only as needed and retain only normalized/extracted values actually required by the dashboard. In particular, do not persist large raw JSON arrays/objects in Recorder attributes, files, or project databases simply for later charting.

Prefer efficient scalar states and Home Assistant statistics/downsampled history where they satisfy the visual requirement. Avoid 365 days of unnecessarily high-frequency raw state history when lower-resolution long-term history preserves the information needed for one-year views.

During planning, estimate the expected one-year footprint and update frequency for each source and ensure the design stays comfortably below the 2 GB/source ceiling under normal operation. Do not claim the ceiling is enforced if the chosen architecture cannot actually honor the oldest-first rule; choose the smallest feasible mechanism available within the current access/security boundary.

## 6. Responsiveness and visual acceptance criteria

The dashboard must have **no page-level vertical or horizontal scrollbars, no clipped/overflowing card content, no overlapping cards, and no overlapping/truncated text that harms readability** at the target resolutions below.

### Highest-priority target
**2560 × 1285**

This resolution is the primary design target. Optimize grid/layout behavior, scaling, card heights, spacing, margins, typography, chart density, legends, labels, and visual balance specifically for it.

Test it in both:
- Home Assistant sidebar collapsed;
- Home Assistant sidebar expanded.

Both sidebar states must remain polished and fully usable with no scrolling/overflow/overlap.

### Secondary targets
Also optimize and test:
- **1920 × 965**
- **2752 × 997**

Test both collapsed and expanded sidebar states where the UI permits.

Use Playwright/browser inspection, not visual guesswork alone. At each target/state:
- render the actual deployed dashboard;
- inspect screenshots;
- verify document/card overflow and scroll dimensions;
- inspect bounding boxes/visible text for collisions;
- verify chart legends/axes/tooltips do not create layout breakage;
- inspect browser console and relevant network errors;
- verify cards remain readable and useful rather than merely technically fitting.

Treat 2560×1285 quality as more important than compromises required for the two secondary sizes.

## 7. Implementation and autonomous iteration

After exploration, create a concise implementation plan in Plan mode if supported. The plan must cover:
- source/entity reuse vs. new entities;
- normalized data extraction and polling;
- retention/storage approach;
- new dashboard construction;
- validation/deployment path;
- test matrix;
- review/refinement loop;
- any discovered constraints and the chosen workaround.

Then execute without waiting for me.

Use the normal autonomous loop repeatedly until the project meets the acceptance criteria:

`inspect → edit → validate → deploy/safe reload → functional test → visual test → review → improve → revalidate → retest`

Do not stop after generating YAML. The dashboard must be created/deployed in Home Assistant and visibly rendered.

Use independent subagents for implementation/data/storage and visual/responsive review whenever appropriate. At minimum, before declaring completion perform:
1. an implementation/data/storage review independent from the primary implementation pass;
2. a visual/responsive review across the required viewport/sidebar matrix;
3. after fixes and affected re-tests, one tightly scoped final regression review by the main agent.

Fix issues found by reviews and rerun affected tests. Keep follow-up passes scoped to the changed or failing area when possible, but do not cap iterations while a justified material defect remains unresolved.

Use local Git tracking/commits for substantial known-good work if permitted by the active local contract. Do not add/push a remote.

## 8. Safety/approval boundaries during this task

Normal project-scoped inspection, permitted file editing, Lovelace editing, API use through existing secret aliases, validation, safe reloads, browser testing, and repeated refinement are pre-authorized.

This task does **not** expand your existing access boundary. Follow the local `AGENTS.md` for approval-gated operations. In particular, do not bypass restrictions around Home Assistant restart/shutdown, destructive Recorder/database operations, HACS install/update/remove, custom integration changes, ESPHome OTA/install, authentication/network/security changes, or unrelated destructive changes.

Do not pause to ask me for approval during the normal workflow. Prefer approaches that avoid gated operations. If a gated action is genuinely unavoidable and is not already pre-authorized by the local contract, leave only that action pending, complete everything else possible, and report it as a hard blocker.

ESPHome changes/OTA are not expected for this dashboard project.

## 9. Definition of done

Do not declare completion until all achievable requirements have been implemented and verified.

Completion requires:
- exploration completed before planning;
- a completely new dashboard exists and no existing dashboard was modified;
- required data is populated from live/valid sources or a clearly documented unavoidable source limitation exists;
- raw API payloads are not persistently stored by the new implementation;
- source polling respects established rate limits/interval decisions;
- one-year retention design and per-source 2 GB cap/oldest-first behavior are addressed credibly;
- Home Assistant configuration affected by the project validates;
- the new dashboard renders without relevant console/network/config errors;
- 2560×1285 passes visual/overflow testing with both collapsed and expanded sidebar;
- 1920×965 and 2752×997 have been tested and refined as secondary targets;
- no page scrollbars, card overlap, or material text overlap/overflow remains at the tested targets;
- an independent review has been performed after implementation;
- review findings have been fixed and affected tests rerun;
- the tightly scoped final main-agent regression review passes or remaining hard blockers are precisely documented.

## 10. Final report

At the end, return one concise technical report containing:
- what was created;
- files/config/entities added or reused;
- dashboard identity/path;
- API sources and final polling cadence;
- retention/storage approach and estimated one-year footprint per source;
- target-resolution/sidebar test matrix with pass/fail results;
- validation/reload/test results;
- review findings and fixes;
- local commit identifier(s), if created;
- any remaining warnings or hard blockers.

Do not include secret values, raw API payloads, generic engineering explanations, or a tutorial.
