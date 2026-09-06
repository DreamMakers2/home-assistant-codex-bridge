# Playwright QA Phase 1

Status: implementation contract. Phase 1 moves only low-ambiguity, repetitive browser QA into deterministic Playwright checks. It does not replace independent visual review or final main-agent review.

## 1. Purpose

Use Playwright Test for repeatable mechanical acceptance checks against the real deployed Home Assistant dashboard. Codex/LLM browser work should focus on implementation, diagnosis and visual judgment instead of repeatedly recreating the same viewport, scrollbar, error and screenshot evidence.

Target workflow:

```text
implement
  -> run affected deterministic state(s)
  -> fix deterministic failures
  -> rerun affected state(s)
  -> run full six-state deterministic gate
  -> independent visual reviewer consumes screenshots + compact QA summary
  -> fix justified visual findings
  -> rerun affected deterministic state(s)
  -> full deterministic regression
  -> final main-agent review
```

Deterministic PASS does not mean the dashboard is visually polished, readable or useful. Those judgments remain with the existing visual/reviewer loop.

## 2. Phase 1 scope

The runner must exercise the actual deployed dashboard and provide these hard checks:

1. exact viewport/sidebar matrix is executed;
2. the requested dashboard renders and reaches a usable ready state;
3. no page-level vertical scrolling;
4. no page-level horizontal scrolling;
5. required top-level rendered dashboard items remain fully inside the browser viewport;
6. no unexpected JavaScript/page errors;
7. no unexpected failed network requests or HTTP 4xx/5xx responses during the bounded test run;
8. one screenshot is captured for every exercised state;
9. compact machine-readable and human-readable results are produced.

Required matrix:

| State ID | Viewport | Sidebar |
| --- | --- | --- |
| `2560x1285-collapsed` | 2560x1285 | collapsed |
| `2560x1285-expanded` | 2560x1285 | expanded |
| `1920x965-collapsed` | 1920x965 | collapsed |
| `1920x965-expanded` | 1920x965 | expanded |
| `2752x997-collapsed` | 2752x997 | collapsed |
| `2752x997-expanded` | 2752x997 | expanded |

Run the matrix sequentially. Do not parallelize states against one persistent authenticated HA profile/session; sidebar/profile state and live UI state must not race between tests.

## 3. Explicit non-scope

Do not add the following to Phase 1:

- card-to-card collision detection, card-internal overflow, generic text clipping/overlap, chart legend/axis/tooltip geometry: Issue #1;
- content/data population semantics, chart-series presence, reload persistence or interaction coverage: Issue #2;
- screenshot baselines, pixel-diff acceptance or attempts to automate visual polish/readability/usefulness: Issue #3;
- weaker authentication/session shortcuts to make the runner convenient: Issue #4.

Phase 1 screenshots are review evidence, not pixel-diff assertions.

## 4. Runner architecture

Use reviewed Playwright Test code as the acceptance engine. Playwright CLI/MCP may be used by Codex to inspect or debug a failing test, but routine acceptance must not depend on an LLM manually issuing browser commands.

Recommended minimal repository layout:

```text
qa/playwright/
  playwright.config.ts
  dashboard-phase1.spec.ts
  lib/
    ha-session.ts
    ha-dashboard.ts
  run-dashboard-qa
```

Equivalent names/layout are acceptable if the interfaces below remain clear.

Responsibilities:

- `ha-session`: obtain an already-authorized browser/page through the approved security boundary; no test owns reusable credentials.
- `ha-dashboard`: set/verify viewport and sidebar state, identify dashboard readiness, identify top-level rendered dashboard items, and return bounded geometry/error evidence.
- spec: parameterize the six states and implement assertions.
- wrapper: expose simple single-state, primary-target and full-matrix commands and write compact results/artifacts.

Do not place deployment-specific Home Assistant URLs, user IDs, cookies, tokens or browser state in the public repository.

## 5. Inputs and execution modes

The runner needs only:

- deployed dashboard URL supplied at runtime;
- requested execution mode/state;
- optional artifact directory.

The implementation should expose equivalent commands for:

```text
single state     -> one named matrix state
primary          -> 2560x1285 collapsed + expanded
full             -> all six matrix states
```

`full` is the final acceptance/regression mode. During iteration, Codex should use the narrowest affected state(s), then run `full` before review/final acceptance.

Default artifacts should go outside the Git working tree, preferably under `/tmp`, unless an explicit path is supplied.

## 6. State setup

Each state is responsible for establishing its own conditions; do not rely on the previous state's persisted sidebar setting.

For every state:

1. set exact viewport dimensions;
2. navigate/open the target dashboard;
3. explicitly set requested sidebar state using a stable HA UI mechanism;
4. verify the sidebar actually reached that state using observable DOM/geometry/state, not by assuming a click succeeded;
5. wait for the dashboard ready condition;
6. run assertions and capture evidence.

Use Playwright web-first assertions/polling for observable state. Do not use arbitrary sleeps as readiness logic. Do not use `networkidle` as the dashboard-ready definition because Home Assistant is a live application with persistent/network activity.

## 7. Dashboard ready condition

The implementation must define a small HA/Lovelace adapter rather than treating successful navigation as ready.

Minimum ready condition:

- browser is on the requested dashboard/view;
- the active Lovelace/dashboard root is attached and visible;
- HA launch/loading shell for that view is no longer blocking it;
- at least one top-level rendered dashboard item is identified.

If the adapter cannot identify the dashboard root or any top-level rendered item, fail with `dashboard_rendered`, not PASS with an empty set.

Top-level QA items must represent the active view's top-level cards/panels, not every nested `hui-card`/custom-card descendant. Keep this selector logic centralized in `ha-dashboard` so HA/frontend changes can be fixed in one place.

## 8. Deterministic assertions

### 8.1 Dashboard rendered

`dashboard_rendered = PASS` only when the ready condition above is satisfied.

Failure evidence should contain a short reason such as wrong route, missing dashboard root, loading state did not clear, or zero top-level items. Do not dump the full DOM/accessibility tree.

### 8.2 No page-level vertical/horizontal scrolling

Check the document scrolling element and the HA primary page/view scroll container used by the current frontend, if separate.

For each page-level scroll container record only:

```text
clientWidth
scrollWidth
clientHeight
scrollHeight
```

Allow only a minimal explicit rounding tolerance (for example 1 CSS pixel) if needed for browser fractional geometry. Any larger tolerance must be justified in code.

Do not inspect card-internal overflow in Phase 1; that belongs to Issue #1.

### 8.3 Top-level items inside viewport

For every top-level QA item, obtain `getBoundingClientRect()` and require the complete rectangle to stay within the browser viewport, subject only to the same small rounding tolerance.

The assertion must not scroll an item into view before measuring it. Successful Playwright interaction is not proof of viewport fit because Playwright can auto-scroll targets.

On failure return only the item identifier, viewport bounds, item bounds and overflow direction/pixels.

This check does not attempt to determine whether text/content inside the card is clipped; that is Issue #1.

### 8.4 Browser errors

Capture from navigation start through completion of the state's assertions/screenshot:

- uncaught page errors (`pageerror`);
- console messages at `error` severity.

Use a small reviewed allowlist only for proven benign HA/browser noise. Every allowlist entry must be narrow and have an inline rationale. Do not broadly ignore whole error classes merely to stabilize tests.

A newly observed non-allowlisted error fails the state.

### 8.5 Network errors

Capture both:

- transport/request failures;
- HTTP responses with status 400-599.

A `requestfailed` listener alone is insufficient because an HTTP 404/500 is still a completed HTTP response.

Scope/allowlist only known benign behavior where necessary. Failure output must never include request/response bodies, authorization headers, cookies or storage data. Strip query strings/fragments from reported URLs unless explicitly proven non-sensitive; origin + pathname is normally sufficient.

The bounded observation window is navigation start through the state's completed assertions/screenshot. Do not wait indefinitely for a live HA page to become network-idle.

## 9. Artifacts and result contract

Always attempt a viewport screenshot for each exercised state, including failed states when the page is renderable.

Use stable filenames:

```text
2560x1285-collapsed.png
2560x1285-expanded.png
1920x965-collapsed.png
1920x965-expanded.png
2752x997-collapsed.png
2752x997-expanded.png
summary.json
summary.txt
```

Do not enable trace/video collection by default in Phase 1. Those artifacts can contain private UI/session/network data and require the explicit security policy tracked in Issue #4.

`summary.txt` should remain compact, for example:

```text
Dashboard QA: FAIL
States: 5/6 PASS
2560x1285-expanded: FAIL top_level_in_viewport (item=priceempire, right=+15px)
Other states: PASS
Artifacts: /tmp/...
```

`summary.json` must use a stable schema version and contain enough structured data for Codex to target reruns without ingesting browser dumps. Minimum shape:

```json
{
  "schema_version": 1,
  "overall": "pass|fail",
  "states": [
    {
      "id": "2560x1285-collapsed",
      "status": "pass|fail",
      "checks": {
        "dashboard_rendered": "pass|fail",
        "vertical_page_scroll": "pass|fail",
        "horizontal_page_scroll": "pass|fail",
        "top_level_in_viewport": "pass|fail",
        "browser_errors": "pass|fail",
        "network_errors": "pass|fail"
      },
      "failures": [],
      "screenshot": "..."
    }
  ]
}
```

Passing output should not include DOM snapshots, console histories, network histories or repeated geometry for every passing item.

## 10. Failure and retry policy

Phase 1 acceptance must not hide instability with automatic retries. Default acceptance runs should use zero retries. A test that intermittently fails is a harness/application problem to investigate, not an automatic PASS.

A full run should continue through all six states even if one state fails so the reviewer receives a complete matrix. Single-state reruns are used for diagnosis/fix cycles.

Do not auto-heal assertions, update allowlists or change acceptance tolerances in response to a failure. Codex may propose such a change only when evidence shows the test itself is wrong.

## 11. Security boundary

The existing runtime intentionally protects `~/.config/codex-ha/browser-profile` from routine sandboxed shell access while the headed Playwright MCP service uses that profile. Preserve this boundary.

Phase 1 implementation must therefore satisfy all of the following:

- exercise the real authenticated HA dashboard;
- do not create/commit a readable `playwright/.auth/*.json` or equivalent reusable cookie/header state in the workspace;
- do not read/copy the protected browser profile;
- do not expose cookies, tokens, authorization headers or reusable session state in test output/artifacts;
- do not enable unrestricted agent-controlled `eval`/`run-code` merely to make deterministic tests work;
- routine Codex use should invoke reviewed test code and receive compact results plus approved screenshots.

The exact secure browser/session attachment mechanism is the prerequisite tracked in Issue #4. If no compliant mechanism is available, implementation must stop at that boundary and report it rather than weakening isolation.

## 12. Integration with existing browser QA

Once Phase 1 is operational:

- browser specialist should run deterministic state checks instead of manually repeating viewport/scroll/error/network checks;
- independent visual reviewer should normally consume the six generated screenshots plus `summary.txt`/relevant compact failures;
- interactive MCP browser inspection remains appropriate for implementation, diagnosis, ambiguous failures and visual judgment;
- deterministic PASS must not be used to skip required independent visual review, justified improvement passes, affected re-tests or final main-agent review.

If deterministic checks fail, fix those mechanical defects before spending reviewer tokens judging polish unless the failure itself requires browser diagnosis.

## 13. Harness definition of done

Phase 1 is operational only when:

- a secure authenticated execution path satisfying Section 11 exists;
- all six exact states can run against a real deployed Lovelace dashboard;
- each state explicitly sets and verifies its sidebar state;
- the six Phase 1 checks produce deterministic PASS/FAIL with bounded evidence;
- screenshots and both summaries are produced in the agreed artifact location;
- a failure in one state does not prevent the rest of the full matrix from running;
- repeated runs against an unchanged dashboard do not show material harness flakiness;
- no reusable browser credentials/session data are exposed to the workspace, Git or normal test output;
- existing visual and final-review gates remain intact.
