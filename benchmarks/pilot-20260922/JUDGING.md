# Human judging instructions

Give reviewers only this file and judgments.csv. Keep manifest.json with the
benchmark coordinator until judging is complete: it contains ranker assignments.

Read each query's information need, then the title and abstract of each candidate.
Use the source URL when more context is necessary. Grade usefulness to that need:
- 0: irrelevant; does not help answer the information need.
- 1: partly relevant; useful background or one aspect, but not the main topic.
- 2: directly relevant; the main contribution addresses the information need.

Fill grade with 0, 1 or 2 and reviewer with your initials/name. Leave notes for
ambiguous judgments. Do not edit query_id or paper_url. Order is shuffled with a
fixed seed; no retrieval score, rank or ranker identity is displayed.

Judge every row. Do not treat unknown/unread papers as irrelevant. For multiple
reviewers, reconcile disagreements into one final sheet before evaluation. Do not
inspect manifest.json while judging. Record any adjudication in notes.

The pilot has 12 predeclared query intents and at most 240 judgments. Its candidate
pool is the union of two systems' top 10 results, not a comprehensive list of all
relevant papers in the corpus. Recall is therefore reported only as pooled recall.
Queries with no positive judgments have undefined recall/nDCG and are reported
separately. Precision uses a denominator of 10, including for short result lists.

Run `python scholar_search/manage.py benchmark evaluate PATH_TO_PACKET --judgments
PATH_TO_COMPLETED_CSV --output PATH_TO_NEW_REPORT_DIRECTORY` after human review.
No real-world relevance scores are available until judgments are complete.
