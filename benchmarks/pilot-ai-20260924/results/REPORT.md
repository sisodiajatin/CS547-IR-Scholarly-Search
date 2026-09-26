# AI-reviewed relevance benchmark

12-query ai-reviewed pilot; recall is relative to the pooled top-10 candidates, not the entire corpus. Frozen runs are evaluated without rerunning search. AI judgments are provisional and are not human ground truth or independent validation.

| Ranker | Precision@10 | MRR@10 | nDCG@10 | Pooled recall@10 |
| --- | --- | --- | --- | --- |
| weighted | 0.8167 (n=12) | 0.9583 (n=12) | 0.7931 (n=12) | 0.7334 (n=12) |
| uniform | 0.8417 (n=12) | 0.9583 (n=12) | 0.8811 (n=12) | 0.7820 (n=12) |

Zero-relevance queries: none

Corpus fingerprint: 96db1ed2ab9c464b9d7b31297b6abdcebdb0242d26996f653c50bbe12e0748b4
