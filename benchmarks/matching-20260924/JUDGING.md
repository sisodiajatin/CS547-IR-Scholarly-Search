# Matching-mode pilot

Six fresh query intents were declared before retrieval. Judge the shuffled union
of three top-10 lists using stored titles/abstracts. Do not inspect manifest ranks
while grading. Grade 0 irrelevant, 1 partial/background, 2 directly relevant.
Provide a reviewer and rationale for every pair. AI reviewers must use an AI:
prefix and evaluate with --judgment-source ai. This is provisional AI evidence,
not human ground truth. Keep zero-result queries in the experiment. Precision
uses denominator 10 even for short lists. Recall is relative to the judged pool.
All three modes use weighted BM25 (5/1/2); matching changes both candidates and
FTS scoring behavior. Queries are selected examples, not a random user sample.
