# AI-reviewed relevance benchmark

6-query ai-reviewed pilot; recall is relative to the pooled top-10 candidates, not the entire corpus. Frozen runs are evaluated without rerunning search. AI judgments are provisional and are not human ground truth or independent validation.

| Ranker | Precision@10 | MRR@10 | nDCG@10 | Pooled recall@10 |
| --- | --- | --- | --- | --- |
| any | 0.5333 (n=6) | 0.8889 (n=6) | 0.6876 (n=6) | 0.5788 (n=6) |
| all | 0.5000 (n=6) | 0.8889 (n=6) | 0.7457 (n=6) | 0.6525 (n=6) |
| phrase | 0.4833 (n=6) | 0.8333 (n=6) | 0.6999 (n=6) | 0.5358 (n=6) |

| Mode | Zero-result queries | Zero-result rate | Mean returned@10 |
| --- | --- | --- | --- |
| any | 0/6 | 0.00% | 10.00 |
| all | 0/6 | 0.00% | 7.67 |
| phrase | 1/6 | 16.67% | 5.50 |

Zero-relevance queries: none

Corpus fingerprint: 96db1ed2ab9c464b9d7b31297b6abdcebdb0242d26996f653c50bbe12e0748b4
