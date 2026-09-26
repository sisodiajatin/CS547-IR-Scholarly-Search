# QA report

## Pre-push verification, 2026-09-25

The combined backend and browser suite passed all 53 tests, including Chrome
and the Firefox/WebKit smoke subtests. The cross-engine phrase-filter test now
waits for navigation before inspecting the resulting page, avoiding a WebKit
execution-context race. Django system checks, migration drift checks and
dependency checks also passed. The local run log is in ignored
qa-artifacts/prepush-tests.log.

## Cross-browser blocker resolved, 2026-09-25

Firefox 155.0 (Playwright build 1543) and WebKit 26.6 (build 2359) now pass
the cross-browser smoke test. Coverage: exact-year result counts, reader return
URL, phrase-mode selection/results, 390px horizontal-overflow check, mobile
menu/Escape focus restoration and no uncaught JavaScript errors. Both ran on a
disposable Django database. Screenshots are in ignored qa-artifacts/.

The Playwright Node downloader continued timing out, but Windows curl downloaded
the official archives successfully from cdn.playwright.dev (redirecting to
Microsoft's download service). They were expanded into the project browser cache;
the existing winldd-1007 dependency checker was copied from the local Playwright
cache. Firefox stalled under the restricted sandbox. Running the tests outside
the sandbox succeeded. No browser security settings were disabled.

Set PLAYWRIGHT_BROWSERS_PATH to the project's .playwright-browsers directory
when reproducing. Installed Chrome remains the default for the Chrome suite.
The 47 backend and five Chrome tests passed in the previous combined run; the
additional smoke test now passes with both engine subtests. This is smoke
coverage, not the full Chrome interaction matrix in every engine. Physical-device,
screen-reader and native browser-zoom testing remain open. Earlier download
blocker notes below are historical and superseded by this result.


## Submission verification, 2026-09-24

The combined run of all 47 backend tests and all five Chrome tests passed (52
total). Django system checks passed and migration drift checks found no changes.
The submission overview, architecture diagram and demo script are in
COURSE_SUBMISSION.md. Earlier counts below describe prior runs.

Firefox installation was retried outside the sandbox with a 60-second connection
timeout; all download mirrors still timed out. The combined installer stopped at
Firefox, so neither engine was tested in that run. Cross-browser coverage remains
unverified; the passing Chrome suite is not evidence of Firefox/WebKit behavior.

A separate WebKit installation retry also exhausted its mirrors with connection
timeouts. Both missing browser engines remain an external download blocker.

## Matching-mode update

Added Any words, All words and Exact phrase controls. Verification passed:
43 backend tests plus Chrome matching-mode and responsive-layout tests (45 total).
Coverage includes cross-field AND matching, phrase order and repeated words,
stemming/punctuation, invalid modes, year filtering and pagination. Chrome verifies
mode retention through query edits and reader return navigation. Responsive tests
cover all five existing widths; the updated 390px results screenshot was visually
inspected. Earlier Firefox/WebKit limitations remain unchanged. The frozen pilot
results do not evaluate the new modes.

## Verified

- 38 Django search/navigation/benchmark tests pass.
- 47 project audit checks pass; results in AUDIT_RESULTS.json.
- Django system check passes; no migration drift.
- Four Chrome Playwright tests pass on a disposable database. Long title, author
  and abstract fixtures exercise wrapping, pagination and reader layout.
- Home, results, reader, guest library, login and signup at 360, 390, 768, 1024 and
  1440px; signed-in library at all five widths; no horizontal overflow.
- Exact-year chart click, page 2, reader and return URL; login/save/remove round
  trip; old-ID redirect and filtered library return.
- Mobile menu/Escape/focus, slash and j/k/Enter shortcuts, validation errors and
  unique IDs, empty state, loading state after browser Back, BibTeX download,
  clipboard success and denied-permission fallback.
- Reduced 720px layout viewport models reflow on a 1440px display at 200% zoom.
  This is not a test of the native browser zoom control.
- Browser tests assert no uncaught page errors, HTTP 5xx, or failed script,
  stylesheet or image loads in Chrome. Traces and screenshots: qa-artifacts/.
  Desktop home and mobile results screenshots were also visually inspected.

## Remaining verification

Firefox and WebKit binaries could not be downloaded: all CDN mirrors timed out,
including retries outside the sandbox. Their smoke tests therefore fail at browser
launch and have not validated app behavior. Native browser zoom, physical mobile
devices and screen-reader interaction remain outside completed coverage.

Full browser reproduction is in README.md. To run only the verified Chrome checks:

```powershell
.\.venv\Scripts\python.exe scholar_search/manage.py test e2e.test_browser.BrowserTests.test_chart_and_result_roundtrip e2e.test_browser.BrowserTests.test_responsive_layouts_and_navigation e2e.test_browser.BrowserTests.test_keyboard_errors_download_and_clipboard e2e.test_browser.BrowserTests.test_desktop_zoom
```

## Benchmark readiness

The pilot contains 167 query-paper judgments across 12 intents. Grades and reviewer
fields are deliberately blank. Evaluating the blank packet correctly raises a
CommandError and creates no report. Metric tests use explicitly synthetic fixtures
and hand-calculated expectations; these are not course evaluation results.
Tests cover deterministic ties, repeatable pools/fingerprints, missing/duplicate
or invalid judgments, missing rankers, zero-positive queries, frozen-run evaluation
and overwrite protection. Human grading is required before reporting relevance.
