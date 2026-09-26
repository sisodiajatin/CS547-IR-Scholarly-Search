# Scholarly project audit

Audit date: 2026-09-21. Scope: current working tree, including uncommitted improvements.

## Follow-up status: 2026-09-22

All five confirmed findings below are now resolved and regression-tested.
- 26 Django tests pass; 47 additional checks pass; the latest audit reports no
  remaining issues among the five original diagnostic findings.
- Corpus: 14,748 rows / 14,748 distinct URLs, with 501 old-ID redirects. A full
  re-import did not recreate duplicates. SQLite integrity and FTS triggers checked.
- A database backup was taken before migration 0009 in `backups/`. There were no
  saved papers in the local database at migration time; overlapping-user bookmark
  preservation and earliest-date retention were verified using isolated test data.
- Login return paths, form error IDs, action validation and HEAD responses corrected.
- Browser availability was checked again: none connected. Visual/runtime browser
  testing, retrieval evaluation, account recovery and production work remain pending.

The original 2026-09-21 observations below are retained as the audit baseline;
AUDIT_RESULTS.json contains current results. Follow-up application changes were
made after authorization to continue.

## Verdict

The core course-project workflows work in the tested environment: search, filtering,
pagination, registration/login/logout, paper reading, saving and removing papers,
private libraries, and BibTeX download. This is a functional local prototype, not a
fully verified public deployment. Search effectiveness has not been scientifically
measured, and real-browser frontend verification remains outstanding.

This audit changes no application behavior or corpus data. It adds this report,
`AUDIT_RESULTS.json`, and a reusable `scripts/audit_project.py` diagnostic script.
The diagnostic script reads the real corpus but performs all write probes in an
isolated test database, then tears it down.

## Executed checks and results

| Area | Result | Scope / limit |
| --- | --- | --- |
| Existing Django suite | 18 / 18 passed | Ranking, authentication, import, reader, citations, library isolation and CSRF |
| Additional audit checks | 47 / 47 passed | HTML structure, routes, search boundaries, pagination, session lifecycle, redirects, cascade/index cleanup, transactional import rollback |
| Diagnostic findings | 5 confirmed | These are separately recorded, not silently counted as passing behavior |
| Clean test database | Passed | All migrations applied successfully to a fresh temporary database |
| Migration drift | None | `makemigrations --check --dry-run` |
| Dependency consistency | Passed | `pip check`; not a CVE/security-advisory scan |
| JavaScript syntax | Passed | `node --check`; does not execute browser interactions |
| SQLite quick check | Passed | Structural database check, not a semantic quality guarantee |
| Static collection dry run | Passed | Finds assets; does not verify a real production static server |
| Development deployment check | 6 warnings | Expected local settings: DEBUG, development secret, HTTP and non-secure cookies |
| Simulated production settings | 2 warnings | Only HSTS subdomain/preload choices remain; these are domain-specific, not automatic requirements |
| Browser visual/interaction QA | Blocked | UI tool returned no available browsers |

Additional passing checks include safe handling of long/Unicode/punctuation queries,
invalid and extreme page numbers, unknown and out-of-range paper IDs, a branded
404 with DEBUG disabled, anonymous library privacy, rejected cross-site redirect
targets, and rollback after 250 imported rows had already been flushed.

No claim is made about cross-browser layout, actual mobile overflow, screen-reader
behavior, clipboard permissions, runtime JavaScript errors, real TLS, sustained
concurrency, full accessibility compliance, or dependency vulnerabilities.

## Original confirmed findings (resolved 2026-09-22)

### DATA-01: Duplicate corpus records (medium)

Observed 15,249 rows but only 14,748 distinct paper URLs. There are 501 duplicate
URL groups and 501 excess rows, plus 505 duplicate exact-title groups. Search and
library records use database IDs, so the same paper can appear twice and be saved
twice under different IDs. The importer is idempotent by ID, not by paper identity.

Fix: define a canonical arXiv identifier and version policy, consolidate duplicate
records while preserving saved-paper references, then enforce an appropriate
uniqueness constraint. Do not simply delete rows that existing libraries reference.

Evidence: `search/models.py:30`, `search/management/commands/import_papers.py:68`,
and `AUDIT_RESULTS.json` corpus section.

### AUTH-01: Login loses the original destination (medium)

Reproduction: POST valid credentials to `/users/login/?next=/library/`.
Observed redirect: `/search/`, rather than `/library/`. Protected profile redirects
similarly lose the original destination. Anonymous Save links also lack a return
path, so users must rediscover their paper after signing in.

Fix: preserve and validate a same-origin `next` parameter. Return users to their
paper/library; keep saving as an explicit CSRF-protected POST action.

Evidence: `search/views.py:68`, `templates/_save_button.html`.

### UI-01: Invalid signup form emits duplicate IDs (medium)

Reproduction: submit matching weak passwords `abc` with otherwise valid signup
fields. Multiple password validation messages each receive `id_password2_error`.
This violates unique-ID requirements and makes the error target ambiguous for
assistive technology. Clean GET forms pass the ID checks; the bug is in error states.

Fix: render one error-list container per field with a unique ID, associate it using
`aria-describedby`, and optionally focus an error summary after submission.

Evidence: `templates/_fields.html:3`, `AUDIT_RESULTS.json` invalid_form_markup.

### API-01: Unknown save action creates a bookmark (low)

An authenticated POST with `action=typo` creates a saved-paper record and redirects
with HTTP 302. Any action except `remove` is treated as `save`.

Fix: validate an explicit save/remove enum and return a form error or HTTP 400 for
unsupported actions. Existing idempotency, CSRF and account-isolation tests pass.

Evidence: `search/views.py:123`.

### HTTP-01: Read pages reject HEAD (low)

HEAD requests to `/`, `/resps/`, `/library/`, and the reader returned 405 while GET
works. This can interfere with clients or monitoring that use HEAD for metadata.

Fix: allow HEAD on read endpoints, using Django's safe-method decorator where
appropriate. Keep mutating endpoints POST-only.

Evidence: method decorators in `search/views.py` and recorded HEAD statuses.

## Search and data improvements

1. **Create a judged retrieval evaluation set.** BM25 ordering tests prove selected
   implementation behavior, not that real results are relevant. Collect representative
   queries and human relevance judgments. Compare a baseline with BM25 using
   precision@10, recall@k, MRR, and nDCG@10; include empty/no-result queries. This is
   the most valuable addition for the CS547 coursework.
2. **Add explicit phrase and field search.** The current tokenizer removes quote
   syntax and OR-matches terms. A controlled query for `"quantum computing"` also
   returned a paper titled `Quantum optics`. This is current behavior, not advertised
   phrase support. Add phrases, AND/OR options and title/author field selectors,
   with tests for combinations and malformed syntax.
3. **Support direct paper identifiers.** An existing fixture at
   `https://arxiv.org/abs/2401.12345` was not found by `2401.12345`. URLs/identifiers
   are not in the current index. Extract and index a canonical arXiv ID and DOI
   when available.
4. **Show collection freshness and refresh it.** The dataset spans 1992-05-04 to
   2024-11-25. The app has no automatic ingestion/update job. Label it clearly as a
   snapshot and add incremental updates, provenance and retry/failure reporting.
5. **Improve query assistance.** Add spelling suggestions, result-term highlighting,
   explicit matching modes, author filters and a year range. Consider stop-word
   handling carefully: common-word queries currently match broadly. Measure
   relevance before adding semantic/vector search.
6. **Improve citation metadata.** Current exports are generic `@misc` entries with
   title/author/year/URL. Store structured authors, arXiv ID, DOI, venue and version
   when available; test corporate authors and names containing commas. The current
   comma split is a heuristic and has not been validated across the corpus.

## Frontend improvements

- **Finish real-browser QA first.** Test 360px, 390px, 768px, 1024px and 1440px widths,
  browser zoom at 200%, long paper titles/authors, error forms and empty libraries.
  Exercise menu open/close, Tab order, `/`, `j`/`k`, Enter, Escape, clipboard success
  and denial, back navigation and loading state restoration.
- **Make the preview follow selection.** It currently previews only the first result;
  keyboard browsing does not update it. The label correctly says TOP RESULT, but
  a selectable reader pane would make the layout more useful.
- **Clarify publication-chart navigation.** A bar showing a specific year's count
  navigates to `q=research&year=YEAR`, meaning papers containing research since that
  year, not the records counted by the bar. Offer an exact-year browsing route or
  make bars descriptive only.
- **Improve small-text readability.** CSS uses 7-10px for several labels and controls.
  Review these at actual device sizes and increase interactive target sizes where
  needed. This is a source-based concern, not a measured visual failure.
- **Offer configurable character shortcuts.** Single-letter global shortcuts should
  be disableable/remappable or scoped to a focused region; include a shortcut guide.
- **Complete error and recovery UX.** Add branded 400/403/500 pages, clear save/remove
  confirmation with undo where practical, and safe retry paths. A branded 404 exists.
- **Improve navigation continuity.** Preserve the originating search and page when
  opening a paper, and return to that context instead of a blank Deep Query page.

## Backend and deployment gaps

- **Authentication throttling:** no app-level login/signup rate limit or lockout is
  configured. Add measured limits before a public launch. Existing tests verify
  password hashing and CSRF, not brute-force protection.
- **Account recovery:** signup does not collect email; password reset/change,
  verification, profile editing and account deletion flows are absent.
- **Production setup:** local defaults are intentionally development-oriented.
  The simulated production check used an ephemeral random secret with DEBUG=false;
  it did not change the running server or validate a real deployment. Configure
  actual hosts, TLS/reverse-proxy behavior, a production application server, static
  serving, backups, and error monitoring. HSTS subdomain/preload settings require
  domain-specific decisions; do not enable them just to silence warnings.
- **Continuous verification:** no CI workflow, dependency lock file, browser test
  suite, lint/format checks, or coverage tracking is present. The version range
  alone does not make installations identical.
- **Corpus administration:** no operator-facing ingestion status, dataset management,
  index maintenance or health endpoint. The Django admin route is not enabled.
- **Scale carefully:** corpus count/date aggregation runs on each rendered page,
  while saved_ids loads every bookmark for the user even for a ten-result page.
  Cache corpus metadata and retrieve saved flags for visible IDs as needed. Benchmark
  before replacing SQLite. The FTS schema intentionally couples this implementation
  to SQLite; changing the database ENGINE alone will not migrate search.
- **Repository hygiene:** 30 tracked `.pyc` files, the legacy database and an evaluation
  log remain tracked despite .gitignore rules. Remove generated artifacts from
  version control in a dedicated cleanup. Do not interpret the old evaluation log
  as a validated evaluation of the current engine.

Deployment recommendations follow Django's official checklist:
https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
Login redirect behavior can use Django's supported authentication views:
https://docs.djangoproject.com/en/5.2/topics/auth/default/

## Local performance sample

Full Django test-client request, existing 15,249-row corpus, five sequential samples
per query, same local process. These are server-side timings, not browser load or
network timings, and not a concurrency benchmark.

| Query | Median | Maximum |
| --- | ---: | ---: |
| neural networks | 18.76 ms | 43.03 ms |
| transformer attention | 11.01 ms | 11.41 ms |
| the | 38.54 ms | 39.82 ms |
| quantum computing | 20.41 ms | 21.62 ms |

Anonymous home and search each executed three SQL queries in the sampled request;
there was no per-result database-query explosion in those paths.

## Suggested order of work

1. Completed: duplicate consolidation, login return paths, signup error markup, action validation and HEAD support.
2. Complete browser/device testing and add automated browser regression coverage.
3. Build the judged retrieval benchmark and use its results to improve search syntax/ranking.
4. Add account recovery, throttling and production operations before public hosting.
5. Add notes/tags/collections, bulk citation export, saved searches and email alerts.
6. Add related-paper discovery and citation graphs only when reliable relationship
   metadata is available; avoid inferred citation links being presented as facts.

## Reproduce

```powershell
.\.venv\Scripts\python.exe scholar_search/manage.py test search --verbosity 2
.\.venv\Scripts\python.exe scripts/audit_project.py
.\.venv\Scripts\python.exe scholar_search/manage.py check --deploy
.\.venv\Scripts\python.exe scholar_search/manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pip check
node --check scholar_search/static/app.js
```

The audit script writes machine-readable observations to `AUDIT_RESULTS.json`.
Its 47 passing checks are bounded checks, not proof that the whole project is bug-free;
the five original diagnostic issues are resolved; unverified browser behavior and the listed feature/operational gaps remain open.


## Follow-up implementation: chart, navigation, QA and relevance pilot

This update supersedes earlier browser/benchmark status above. Exact-year chart
browsing and origin-preserving reader navigation are implemented and regression
tested. Current validation: 38 backend tests, 47 audit checks, four passing Chrome
browser tests across 360/390/768/1024/1440px, system check and migration drift check.
The 200% check emulates the reduced layout viewport; native browser zoom controls
remain unverified. Firefox and WebKit smoke tests are implemented but their browser
downloads timed out. See QA_REPORT.md for scope and reproduction.

The human-judged pilot is prepared under benchmarks/pilot-20260922: 12 queries,
167 blank judgments, frozen weighted-versus-uniform BM25 runs. Human grading is
the remaining dependency for relevance scores. No lexical or generated judgments
are presented as human ground truth. Account/operations milestones remain open.
