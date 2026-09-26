# AI-reviewed relevance pilot

On 2026-09-24, Codex assessed all 167 query-paper pairs in the frozen 12-query
pilot using the stored title, abstract and written query intent. This was a
single AI review, not a human assessment. No full papers were read and no
external verification was performed. The assessor previously implemented the
benchmark, so this is not independent validation.

The original human-review sheet remains blank and unchanged. This directory's
judgments.csv contains the AI grades, explicitly identified reviewer, and an
individual rationale for every pair. provenance.json records the input/output
hashes and review protocol. Rankings and ranker assignments were not inspected
while grading; they were used by the evaluator after grades were saved.

## Rubric and decisions

- 0: Does not address the stated information need. 30 pairs.
- 1: Useful background or a partial match. 32 pairs.
- 2: Directly addresses the information need. 105 pairs.

Judgments assess topical usefulness, not whether a paper's claims are correct.
Negative experimental results can still be directly relevant. Surveys of methods
can receive 2. Benchmarking infrastructure, interpretability studies and
adjacent applications receive 1 when they inform the topic but do not provide the
requested method. These boundaries are subjective and could change under human
review. In particular, cross-modal retrieval, neural differential-equation
identification, and the GKP-qubit abstract have partial-relevance rationales that
deserve checking in any later review.

## Results

| Ranker | Precision@10 | MRR@10 | nDCG@10 | Pooled recall@10 |
| --- | ---: | ---: | ---: | ---: |
| Weighted BM25 (5/1/2) | 0.8167 | 0.9583 | 0.7931 | 0.7334 |
| Uniform BM25 (1/1/1) | 0.8417 | 0.9583 | 0.8811 | 0.7820 |

These are macro averages over 12 queries using these AI judgments. Precision
counts grades 1 and 2 as relevant. nDCG distinguishes their gains (1 versus 3).
Uniform BM25 has higher nDCG for 9 queries, lower for 2, and ties for 1. The largest
weaknesses include machine translation (Precision@10 0.2 weighted, 0.4 uniform)
and quantum error correction (0.2 for both). Keyword matches often use different
meanings of translation, retrieval or correction. This suggests testing stricter
multi-term matching and field weights in a separate experiment.

No significance claim is made. The small query set was not randomly sampled, and
both systems contributed candidates to the judgment pool. Pooled recall is not
corpus recall. A high nDCG can coexist with low precision when a pool contains few
relevant papers: quantum error correction illustrates this. Do not tune on this
pilot and then present improvements on the same queries as held-out evaluation.
The application's default ranker has not been changed.

## Reproduce

From the repository root, choose a new output directory:

```powershell
.\.venv\Scripts\python.exe scholar_search/manage.py benchmark evaluate benchmarks/pilot-20260922 --judgments benchmarks/pilot-ai-20260924/judgments.csv --judgment-source ai --output benchmarks/ai-rerun
```

The evaluator uses frozen rankings, not a rerun against the current database.
It exports results/REPORT.md, results/metrics.json and results/per_query.csv.
The CLI refuses to label reviewers marked `AI:` as human unless their provenance
is altered; explicit `--judgment-source ai` produces the correctly labeled report.

## Suggested submission wording

> We conducted a provisional AI-assisted relevance evaluation over 12 predeclared
> query intents. A single Codex assessor graded 167 pooled query-paper pairs from
> titles and abstracts on a 0-2 scale and recorded a rationale for every grade.
> Uniform BM25 achieved macro Precision@10 of 0.8417 and nDCG@10 of 0.8811,
> compared with 0.8167 and 0.7931 for weighted BM25. These judgments have not been
> independently validated by human assessors. Recall is measured relative to the
> pooled candidates rather than all relevant documents in the corpus.
