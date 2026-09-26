# Fresh-query comparison of search matching modes

## Decision

Keep **Any words** as the default. **All words** is a useful refinement, and
**Exact phrase** is useful for established terminology. This small AI-reviewed
pilot shows a relevance/coverage tradeoff, not a universally better mode.
No default, ranking weights or application behavior was changed during evaluation.

## Experiment

Six query intents were declared in MODE_QUERIES before candidate retrieval. None
repeats a query from the original 12-query pilot. The set includes short topic
phrases and longer information requests; it is purposively selected, not a random
sample of user traffic. It was not edited after inspecting results.

All modes use the same 14,748-paper corpus, weighted BM25 (title/abstract/author
5/1/2), Porter stemming, and publication-date/ID tie-breaks. Any words OR-matches
terms, All words AND-matches across fields, and Exact phrase requires adjacent
ordered tokens within one field. Changing the MATCH expression also changes
FTS5 scoring behavior: this is an end-to-end mode comparison, not just filtering
an identical ranked list. The previous uniform-versus-weighted experiment is
separate and its results are not mixed into this comparison.

The union of all three top-10 lists produced 91 query-paper pairs. A single Codex
assessor read every stored title and abstract against the query intent, assigning
0 (irrelevant), 1 (partial/background), or 2 (directly relevant), with a rationale
for each pair. Candidates were shuffled; the assessor did not inspect saved mode
assignments or ranks while grading. No full-text papers or external sources were
reviewed. The same assistant implemented and evaluated the application, so this
is not independent validation or human ground truth.

## Aggregate results

| Mode | Precision@10 | MRR@10 | nDCG@10 | Pooled recall@10 | Zero-result queries | Mean returned@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Any words | 0.5333 | 0.8889 | 0.6876 | 0.5788 | 0/6 | 10.00 |
| All words | 0.5000 | 0.8889 | 0.7457 | 0.6525 | 0/6 | 7.67 |
| Exact phrase | 0.4833 | 0.8333 | 0.6999 | 0.5358 | 1/6 | 5.50 |

Metrics are macro averages across all six queries. Precision counts both grades
1 and 2 as relevant and divides by 10 even for short lists. nDCG uses gains 1 and
3, giving directly relevant papers more credit. Missing results contribute no
gain. Pooled recall uses only relevant papers in the union of top-10 lists, not
all relevant papers in the corpus. Every query has a positive pooled judgment,
so no query was excluded from nDCG or recall. Zero-result frequency includes
every query regardless of relevance labels.

## Corpus result counts

| Query | Any words | All words | Exact phrase |
| --- | ---: | ---: | ---: |
| federated learning | 6,468 | 306 | 277 |
| object detection | 1,828 | 75 | 15 |
| speech recognition | 296 | 39 | 31 |
| protein structure prediction | 5,004 | 8 | 2 |
| privacy preserving medical data | 5,229 | 6 | 0 |
| solar flare forecasting | 491 | 2 | 1 |

All words greatly reduces result counts but did not change the top-10 order for
the first three queries. Exact phrase improved nDCG for object detection and
speech recognition, while losing all results for the medical-privacy request.
For solar flares, most broad results discuss observed flare physics rather than
forecasting. For protein structure, the pool contains partial structural methods
and representation work but no entry graded as a direct full-3D predictor.
High nDCG in such a sparse pool should not be mistaken for comprehensive coverage.

The result counts above are retrieval counts, not counts of relevant papers.
The small sample and subjective AI grades do not establish statistical
significance. If these queries guide future tuning, use another untouched query
set for subsequent evaluation rather than reporting this set as held-out.

## Files and reproduction

- manifest.json: frozen queries, corpus fingerprint, configurations, result counts,
  ranked runs and candidate metadata. Keep it hidden during judging.
- judgments.csv: unchanged blank judging sheet.
- ai-review/judgments.csv: all 91 AI grades and rationales.
- ai-review/provenance.json: review protocol and source/output hashes.
- ai-review/results/: machine-readable metrics, per-query CSV and generated report.

Re-evaluate the frozen runs into a new output directory:

```powershell
.\.venv\Scripts\python.exe scholar_search/manage.py benchmark evaluate benchmarks/matching-20260924 --judgments benchmarks/matching-20260924/ai-review/judgments.csv --judgment-source ai --output benchmarks/matching-rerun
```

To intentionally freeze a new matching experiment with the configured query set:

```powershell
.\.venv\Scripts\python.exe scholar_search/manage.py benchmark prepare --experiment matching --output benchmarks/new-matching-packet
```

The evaluator rejects incomplete grades, missing modes, and counts inconsistent
with the saved top-10 list lengths. Empty pools and zero-result queries remain in
the denominator. Existing packets and reports cannot be overwritten.

## Suggested submission wording

> We evaluated three matching modes on six fresh, predeclared query intents using
> 91 AI-reviewed query-paper pairs. All words achieved the highest macro nDCG@10
> (0.7457), while Any words achieved the highest Precision@10 (0.5333). Exact
> phrase returned zero results for one of six queries. Given the small,
> non-random query set and lack of independent human assessment, we retained
> Any words as the default and exposed the stricter modes as user refinements.
