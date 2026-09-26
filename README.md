# Scholarly | CS547 Scholarly Search

For the architecture, demo walkthrough and evaluation summary, see
[COURSE_SUBMISSION.md](COURSE_SUBMISSION.md).

A Django application for exploring academic papers by title, abstract and author.
The included arXiv corpus contains 15,249 source rows representing 14,748 distinct paper URLs. Search is public; accounts have a
research-area profile and private saved-paper library. Results use SQLite FTS5 with Porter stemming and weighted
BM25 ranking, with publication-year filtering and relevance/newest sorting.

## Local setup

Requires Python 3.10+ and SQLite with FTS5 (included in the tested Python 3.13 build).
Django 5.2 LTS is used; supported versions: https://www.djangoproject.com/download/.
Run commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scholar_search/manage.py migrate
.\.venv\Scripts\python.exe scholar_search/manage.py import_papers arxiv_papers.sql
.\.venv\Scripts\python.exe scholar_search/manage.py runserver
```

On macOS/Linux replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.
Open http://127.0.0.1:8000/. No MySQL server, Node build, NLTK data download or API
key is required. Data goes into ignored `scholar_search/local.sqlite3`; the bundled SQL dump is unchanged. Legacy database files remain local and are
excluded from Git. Importing again updates matching URLs
without duplicating papers. The importer accepts this repository's MySQL dump
format; it is not a general SQL importer. Do not use Django `loaddata` on SQL files.

## Search behavior

Example: `/resps/?q=neural+networks&year=2020&sort=relevance&page=2`.
Terms are case-normalized, stemmed by FTS5, and OR-matched. Title, abstract and
author weights are 5, 1 and 2. `year_mode=since` (default) includes the selected year
and all later years; `year_mode=exact` selects only that year. Chart bars use exact
year browsing without a keyword query. A year alone browses newest first.
Pagination retains query and filters. Relevance is independent of profile fields.
The index is maintained by database triggers, including during bulk imports.

Use **Match words** under Refine results to select `match=any` (default, any
query word), `match=all` (every query word, possibly across fields), or
`match=phrase` (the ordered, adjacent word sequence within one field). Phrase
mode preserves repeated words. All modes ignore punctuation and use the existing
Porter stemming, so Exact phrase is not a case-sensitive literal substring match.
Quotes and Boolean operators typed in the query do not enable special syntax;
use the selector. Matching uses at most 40 terms, as before. The selected mode
survives query edits, pagination, and reader return navigation. Reset restores
Any words. The frozen benchmark remains an evaluation of the original Any words
matching; no relevance improvement is claimed from these new controls yet.

## Tests

```powershell
.\.venv\Scripts\python.exe scholar_search/manage.py test search
.\.venv\Scripts\python.exe scholar_search/manage.py check
.\.venv\Scripts\python.exe scholar_search/manage.py makemigrations --check --dry-run
```

## Configuration and deployment

Set environment variables in your shell or hosting platform (`.env` files are not
loaded automatically):

| Variable | Default | Purpose |
| --- | --- | --- |
| DJANGO_DEBUG | true | Set false outside local development |
| DJANGO_SECRET_KEY | development-only fallback | Required custom secret when debug is false |
| DJANGO_ALLOWED_HOSTS | localhost,127.0.0.1,[::1] | Comma-separated allowed hosts |
| DJANGO_DB_PATH | scholar_search/local.sqlite3 | SQLite database file |

With debug disabled the app requires a secret, redirects to HTTPS, and enables
secure cookies and HSTS. Configure your HTTPS host/reverse proxy correctly. Use a
production application server, run `collectstatic`, serve `staticfiles/`, back up
the database and add account rate limiting before public deployment. The Django
development server is for local use. `manage.py check --deploy` checks deployment
settings; run it against your actual production configuration.

## Existing accounts and data

Migration 0007 converts legacy `umTester` accounts to Django users and profiles,
hashes passwords, and clears the legacy plaintext password column. It aborts on
username collisions rather than silently merging accounts, and is intentionally
irreversible. Back up an existing database before migration. Old custom sessions
are no longer authenticated; users must log in again. The default local database
is new: external MySQL data/accounts are not automatically copied into it. Migrate
such data separately before running the account conversion. Existing legacy paper
tables are retained; the bundled corpus is imported into the new Paper model.

See [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) for the audit, completed changes and
next milestones, including judged retrieval evaluation and production hardening.

## Research terminal UI

The interface follows the screenshots and design specification in `assest/`:
navy panels, cyan focus states, compact controls, a persistent navigation rail,
and paper preview and reading panes. No frontend build or third-party UI CDN is
required. The original reference assets are preserved.

- **Workspace**: recent corpus papers, real publication-year distribution and research starting points.
- **Deep Query**: ranked results, year/sort filters and a top-result preview on wide screens.
- **Paper reader**: full abstract, original arXiv link, saved-paper action and BibTeX copy/download.
- **My Library**: account-specific saved papers, title/author filtering and removal from the reading queue.
- **Keyboard**: `/` focuses search; `j`/`k` focus paper titles; Enter follows the focused link; Escape closes the mobile navigation.

Run `migrate` after pulling these changes to create the saved-paper table.
The screenshots contain additional mock features (citation graphs, alerts, live
harvesters and external integrations); these are not represented as working
features. Displayed corpus statistics use the actual local dataset.

Validation: 47 backend tests and 47 audit checks pass. Five Chrome browser tests
cover responsive layouts and reader workflows. Firefox and WebKit smoke tests
also pass after resolving download and sandbox startup issues. See [QA_REPORT.md](QA_REPORT.md).

## Audit fixes (2026-09-22)

Migration 0009 consolidates exact-URL duplicate papers, retains the lowest paper ID,
merges saved references while keeping the earliest save date, and preserves removed
paper links through redirects. A unique URL index prevents repeat imports from
recreating duplicates. URL variants and different arXiv versions remain separate;
this does not merge papers by title. The migration is irreversible: back up existing
databases first. The local database was backed up under ignored `backups/` before
applying it. The SQLite FTS triggers remain intact.

Login now preserves validated same-origin return destinations. Guest Save links
return to the paper after login without automatically saving it. Invalid save actions
return HTTP 400, read endpoints support HEAD, and signup errors use unique IDs.

Run `python scripts/audit_project.py` using the project virtual environment to rerun
the 47 additional checks. Current machine-readable results are in AUDIT_RESULTS.json.

## Reader navigation and browser QA

Reader links carry an allowlisted local `return_to` URL, retaining search filters,
year mode, sort and page (or library filter/page) through login, save/remove and
legacy-ID redirects. Direct reader visits fall back to Deep Query.

Install browser-test dependencies and engines, then run the isolated test database:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PLAYWRIGHT_BROWSERS_PATH="$PWD\.playwright-browsers"
.\.venv\Scripts\python.exe -m playwright install firefox webkit
.\.venv\Scripts\python.exe scholar_search/manage.py test e2e
```

Chromium tests use installed Chrome by default. For bundled Chromium, install it
with Playwright and set `$env:E2E_CHROMIUM_CHANNEL=''`. Screenshots and traces are
written to ignored `qa-artifacts/`. Full suite failures on missing engines are
intentional; the suite does not silently skip cross-browser coverage.

## Human-judged relevance pilot

The frozen [pilot packet](benchmarks/pilot-20260922/JUDGING.md) contains 12 query
intents and 167 pooled query-paper pairs from the current 14,748-paper corpus.
Give judges only JUDGING.md and judgments.csv; manifest.json reveals system ranks.
Human reviewers fill grades (0/1/2) and reviewer names. No relevance results are
claimed until that work is complete.

```powershell
# Prepare a NEW packet only when intentionally freezing a new experiment:
.\.venv\Scripts\python.exe scholar_search/manage.py benchmark prepare --output benchmarks/new-pilot
# Score the original frozen runs once human judgments are complete:
.\.venv\Scripts\python.exe scholar_search/manage.py benchmark evaluate benchmarks/pilot-20260922 --judgments benchmarks/pilot-20260922/judgments.csv --output benchmarks/pilot-results
```

Both rankers use identical FTS5 Porter/OR matching and deterministic ties; only
field weights change (5/1/2 versus 1/1/1). The report exports per-query and macro
Precision@10, MRR@10, nDCG@10 and **pooled** recall@10. Recall is not corpus-wide.
Zero-positive queries have undefined nDCG/recall and explicit excluded counts.
Missing, duplicate, invalid or unreviewed judgments prevent evaluation. Existing
packets/reports cannot be overwritten. Corpus and judgment SHA-256 hashes identify
the evaluated inputs; frozen runs permit scoring without querying a changed index.

An additional [AI-reviewed pilot](benchmarks/pilot-ai-20260924/README.md) now
contains grades and rationales for all 167 pairs, with explicitly AI-labeled
results. The original human-review sheet remains unchanged. Use
`--judgment-source ai` when evaluating these judgments. They are provisional
AI assessments, not human ground truth. Eight benchmark tests cover scoring,
validation and provenance labeling.

The [fresh-query matching comparison](benchmarks/matching-20260924/README.md)
evaluates Any words, All words and Exact phrase with fixed weighted BM25 on six
new query intents and 91 AI-reviewed pairs. It includes corpus result counts and
zero-result rates. All words led on nDCG@10; Any words led on Precision@10; Exact
phrase returned nothing for one query. Any words remains the default. Prepare
this experiment with `benchmark prepare --experiment matching --output NEW_PATH`.
The backend suite now has 47 passing tests, including empty-query-pool coverage,
frozen mode runs and result-count validation.
