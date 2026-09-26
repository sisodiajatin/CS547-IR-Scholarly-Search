# Improvement plan and audit

## Findings
- Repeated inline CSS, inconsistent layouts, invalid nested links/buttons, missing mobile results layout and inaccessible form controls.
- Plaintext password storage and lookup; logout via GET; unvalidated registration.
- Hardcoded database credentials and secret key; README setup does not match code.
- Full corpus tokenized at module import; duplicate search implementation; database account lookup inside each paper loop.
- Session-dependent queries and pagination, lost year filters, case mismatch, exclusive year boundary, and crashes for empty queries.
- Profile boosts admit unrelated papers. Existing evaluation labels lexical overlap as relevance and can report values greater than one.
- No functional tests or installable dependency manifest.

## Implemented in this pass
1. Retain Django templates and vanilla CSS. Introduce a shared responsive editorial design, keyboard focus, labeled forms, empty/error/loading states, expandable abstracts and consistent navigation.
2. Use Django authentication, password validation, hashed credentials, CSRF-protected POST logout and protected profiles. One-way migration transfers legacy accounts and clears legacy plaintext credentials; collisions abort for manual resolution.
3. Use local SQLite and FTS5 with Porter stemming and weighted BM25 (title 5, abstract 1, author 2). Queries use OR matching across unique terms; scores are relevance ordering, not confidence probabilities. Index triggers track inserts, updates and deletes.
4. Keep queries, inclusive publication-year filters, sorting and pagination in URLs. Search remains available without an account. Research area is profile metadata; it does not alter ranking.
5. Add a transactional, rerunnable importer for the included MySQL dump, without executing its SQL. Keep original data files untouched. Use a new ignored local.sqlite3 database.
6. Add regression tests covering ranking, stemming, authors, filters, pagination, malformed input, index updates, authentication, account conversion and import.

## Next milestones
- Research evaluation: create a judged query/paper dataset; compare BM25 with the original lexical baseline using precision@10, recall and nDCG. Do not present token overlap as ground-truth evaluation.
- Account hardening for public deployment: rate-limit login and signup at the application/gateway, configure password reset and email delivery, and review account recovery.
- Product expansion: saved searches, collection folders and citation alerts, after confirming desired workflows.
- Operations: production WSGI/ASGI hosting, HTTPS, static asset serving, backups, CI, structured error monitoring and corpus update policy.
- Scale: benchmark realistic concurrent searches before selecting a separate search service; current search backend intentionally requires SQLite FTS5.

## Verification
- 18 regression tests pass; Django system checks and migration drift checks pass.
- Imported 15,249 real papers from the bundled dump.
- Local single-query check: "neural networks" matched 3,730 papers; count plus first 10 results took about 17 ms. This is a development measurement, not a concurrency benchmark.
- Browser visual inspection remains pending: no browser was available through the connected UI tool. Responsive CSS and rendered HTML were checked programmatically; this does not replace visual QA.

## Reference-driven UI rebuild

Applied the four screenshot references and the fifth folder's DESIGN.md in `assest/`.
The previous light editorial design is replaced by the Scholarly dark research
terminal: navy surface hierarchy, cyan selections, monospace metadata, serif paper
titles, fixed navigation, compact controls, split search/preview panes, and mobile
navigation. Workspace charts/counts use actual corpus data. Paper reading, private
saved-paper libraries, filtering, and BibTeX exports now work end to end. Mock
citation counts, lineage graphs and live integrations were not copied as data.

Migration 0008 adds the unique user/paper saved-record relationship. No changes
were made to source reference assets or paper ranking semantics.

## Audit fixes completed (2026-09-22)

Resolved all five diagnostic issues. Added safe login return paths, unique linked
form-error IDs, strict save/remove validation and HEAD support. Migration 0009
consolidates exact URL duplicates with bookmark/date preservation and old-ID
redirects, enforcing URL uniqueness without rebuilding the SQLite FTS source table.
The importer now updates by URL identity. Backed up and migrated the local database,
then verified a full re-import keeps 14,748 unique records. All 26 tests and 47 audit
checks pass. Browser QA remains blocked by unavailable browser connections.


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
