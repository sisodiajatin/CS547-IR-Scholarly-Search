"""Reproducible pooled retrieval evaluation; never manufactures judgments."""
import csv
import hashlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from .models import Paper
from .services import search_papers

TOPICS = [
    ("neural networks", "Find methods for designing or training artificial neural networks; exclude incidental mentions and purely biological neurons."),
    ("transformer attention", "Find attention mechanisms used in Transformer neural architectures; exclude electrical transformers."),
    ("information retrieval", "Find methods for retrieving and ranking documents relevant to an information need; exclude unrelated information theory."),
    ("machine translation", "Find computational methods for translating text between human languages; exclude geometric translation."),
    ("graph neural networks", "Find neural methods that operate on graph-structured data; exclude graph theory without neural modeling."),
    ("reinforcement learning", "Find methods for learning sequential decisions from rewards or interaction; exclude supervised learning without reinforcement."),
    ("image classification", "Find methods that assign semantic classes to images; detection-only work is partial if useful to classification."),
    ("anomaly detection", "Find methods for identifying unusual observations or events in data; exclude anomaly discussions without detection methods."),
    ("quantum error correction", "Find methods for protecting quantum information from noise using error correction; exclude classical-only error correction."),
    ("differential equations", "Find analytical or numerical methods for solving differential equations; incidental use is partial at most."),
    ("combinatorial optimization", "Find algorithms for optimizing discrete combinatorial problems; exclude continuous-only optimization."),
    ("signal processing", "Find methods for analyzing, filtering or transforming measured signals; exclude unrelated signaling terminology."),
]
QUERIES = [{"id":f"Q{i:02}","query":query,"intent":intent} for i,(query,intent) in enumerate(TOPICS,1)]
# Frozen before retrieval: phrase-like and natural-language needs, no pilot repeats.
MODE_QUERIES = [
    {"id":"M01","query":"federated learning","intent":"Find methods for collaboratively training models without centralizing clients' raw data."},
    {"id":"M02","query":"object detection","intent":"Find methods that locate and classify objects in images or video; image-level classification alone is partial at most."},
    {"id":"M03","query":"speech recognition","intent":"Find methods for converting spoken audio into words; speaker identity or emotion recognition alone is not relevant."},
    {"id":"M04","query":"protein structure prediction","intent":"Find methods predicting three-dimensional protein structure from sequence or related evidence; protein property prediction alone is partial at most."},
    {"id":"M05","query":"privacy preserving medical data","intent":"Find methods protecting patient privacy when sharing or learning from medical data; general privacy methods without a medical application are partial."},
    {"id":"M06","query":"solar flare forecasting","intent":"Find methods predicting future solar flares; solar generation forecasting and unrelated astronomical transients are not relevant."},
]
FIELDS = ["query_id","query","intent","paper_url","title","authors","abstract","grade","reviewer","notes"]


def metric_at_10(run, grades):
    relevance = [grades[url] for url in run[:10]]
    positives = sum(value >= 1 for value in relevance)
    total = sum(value >= 1 for value in grades.values())
    dcg = sum((2**value-1)/math.log2(rank+2) for rank,value in enumerate(relevance))
    ideal = sum((2**value-1)/math.log2(rank+2) for rank,value in enumerate(sorted(grades.values(),reverse=True)[:10]))
    return {"precision@10":positives/10, "MRR@10":next((1/(rank+1) for rank,value in enumerate(relevance) if value>=1),0.0),
            "nDCG@10":dcg/ideal if ideal else None, "pooled_recall@10":positives/total if total else None}


def csv_text(value):
    # Protect spreadsheet users when source metadata begins with a formula.
    return "'"+value if value and value[0] in "=+-@\t\r" else value


def prepare(output, *, experiment="ranking"):
    if experiment not in {"ranking", "matching"}:
        raise ValueError("Unknown experiment")
    queries = MODE_QUERIES if experiment == "matching" else QUERIES
    systems = {mode: {"ranker":"weighted", "match":mode} for mode in ("any", "all", "phrase")} if experiment == "matching" else {name: {"ranker":name} for name in ("weighted", "uniform")}
    output = Path(output)
    if output.exists():
        raise ValueError("Output directory already exists; choose a new directory to preserve judgments.")
    docs = list(Paper.objects.order_by("url").values("id","url","title","summary","authors","published"))
    if not docs:
        raise ValueError("Import a corpus before preparing a benchmark.")
    fingerprint = hashlib.sha256(json.dumps(docs,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    runs, pooled, rows, counts = {}, {}, [], {}
    rng = random.Random(547)
    for query in queries:
        candidates = {name:search_papers(query["query"], **settings) for name,settings in systems.items()}
        counts[query["id"]] = {name:papers.count() for name,papers in candidates.items()}
        runs[query["id"]] = {name:list(papers.values_list("url",flat=True)[:10]) for name,papers in candidates.items()}
        urls = sorted(set(url for run in runs[query["id"]].values() for url in run))
        if not urls and experiment == "ranking":
            raise ValueError(f"No candidates for {query['id']}; revise the pilot query before freezing it.")
        pool = list(Paper.objects.filter(url__in=urls).order_by("url").values("url","title","summary","authors"))
        rng.shuffle(pool)
        pooled[query["id"]] = pool
        for doc in pool:
            rows.append(dict(query_id=query["id"],query=query["query"],intent=query["intent"],paper_url=doc["url"],
                title=doc["title"],authors=doc["authors"],abstract=doc["summary"],grade="",reviewer="",notes=""))
    output.mkdir(parents=True)
    manifest = {"schema_version":2 if experiment == "matching" else 1,"created_utc":datetime.now(timezone.utc).isoformat(),"corpus_count":len(docs),
        "corpus_sha256":fingerprint,"seed":547,"cutoff":10,"queries":queries,
        "rankers":systems if experiment == "matching" else {"weighted":[5,1,2],"uniform":[1,1,1]},
        "experiment":experiment,"result_counts":counts,"matching":"Any=OR, all=AND across fields, phrase=ordered adjacent tokens within a field; FTS5 Porter stemming; weighted BM25 5/1/2 throughout" if experiment == "matching" else "OR, unique Unicode alphanumeric tokens capped at 40; FTS5 Porter stemming",
        "tie_break":"publication date descending, database ID ascending", "runs":runs,"pool":pooled}
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    with (output/"judgments.csv").open("w",encoding="utf-8-sig",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS);writer.writeheader()
        writer.writerows({key:csv_text(str(value)) for key,value in row.items()} for row in rows)
    (output/"JUDGING.md").write_text("""# Human judging instructions

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
""",encoding="utf-8")
    if experiment == "matching":
        (output/"JUDGING.md").write_text("""# Matching-mode pilot

Six fresh query intents were declared before retrieval. Judge the shuffled union
of three top-10 lists using stored titles/abstracts. Do not inspect manifest ranks
while grading. Grade 0 irrelevant, 1 partial/background, 2 directly relevant.
Provide a reviewer and rationale for every pair. AI reviewers must use an AI:
prefix and evaluate with --judgment-source ai. This is provisional AI evidence,
not human ground truth. Keep zero-result queries in the experiment. Precision
uses denominator 10 even for short lists. Recall is relative to the judged pool.
All three modes use weighted BM25 (5/1/2); matching changes both candidates and
FTS scoring behavior. Queries are selected examples, not a random user sample.
""", encoding="utf-8")
    return len(rows)


def evaluate(packet, judgments, output, *, judgment_source="human"):
    if judgment_source not in {"human", "ai"}:
        raise ValueError("Judgment source must be human or ai.")
    packet, output = Path(packet), Path(output)
    if output.exists():
        raise ValueError("Report directory already exists; choose a new directory.")
    manifest=json.loads((packet/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") not in {1,2} or manifest.get("cutoff")!=10:
        raise ValueError("Unsupported benchmark manifest.")
    query_ids = [q["id"] for q in manifest["queries"]]
    if not query_ids or len(query_ids) != len(set(query_ids)) or set(query_ids) != set(manifest["runs"]) or set(query_ids) != set(manifest["pool"]):
        raise ValueError("Manifest query, pool and run IDs must match uniquely.")
    required = {"any", "all", "phrase"} if manifest["schema_version"] == 2 else {"weighted", "uniform"}
    if set(manifest["rankers"]) != required or any(set(runs) != set(manifest["rankers"]) for runs in manifest["runs"].values()):
        raise ValueError("Every query requires both declared rankers." if manifest["schema_version"] == 1 else "Every query requires all three matching modes.")
    if any((not pool and manifest["schema_version"] == 1) or len({doc["url"] for doc in pool}) != len(pool) for pool in manifest["pool"].values()):
        raise ValueError("Manifest pools must contain unique candidates.")
    expected={(qid,doc["url"]) for qid,pool in manifest["pool"].items() for doc in pool}
    grades={qid:{} for qid in manifest["pool"]}
    seen=set()
    with Path(judgments).open(encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle)
        if not {"query_id","paper_url","grade","reviewer"}.issubset(reader.fieldnames or []):
            raise ValueError("Judging sheet lacks required columns.")
        for row in reader:
            if judgment_source == "human" and row.get("reviewer", "").strip().lower().startswith("ai:"):
                raise ValueError("AI reviewer detected; use --judgment-source ai to label the report correctly.")
            key=(row["query_id"],row["paper_url"])
            if key not in expected or key in seen:
                raise ValueError(f"Unexpected or duplicate judgment: {key}")
            if row["grade"].strip() not in {"0","1","2"} or not row["reviewer"].strip():
                raise ValueError(f"Missing/invalid grade or reviewer for {key}; final scores require {judgment_source} review.")
            seen.add(key);grades[key[0]][key[1]]=int(row["grade"].strip())
    if seen!=expected:
        raise ValueError(f"Incomplete judgments: {len(expected-seen)} rows missing.")
    results=[]
    for qid,runs in manifest["runs"].items():
        for ranker,run in runs.items():
            if len(run)>10 or len(set(run))!=len(run) or any(url not in grades[qid] for url in run):
                raise ValueError(f"Invalid saved run: {qid}/{ranker}")
            results.append({"query_id":qid,"ranker":ranker,**metric_at_10(run,grades[qid])})
    macro={}
    for ranker in manifest["rankers"]:
        group=[row for row in results if row["ranker"]==ranker]
        macro[ranker]={}
        for metric in ("precision@10","MRR@10","nDCG@10","pooled_recall@10"):
            values=[row[metric] for row in group if row[metric] is not None]
            macro[ranker][metric]={"value":sum(values)/len(values) if values else None,"queries":len(values)}
    coverage = {}
    if manifest["schema_version"] == 2:
        for system in ("any", "all", "phrase"):
            values = []
            for qid in query_ids:
                count = manifest["result_counts"][qid][system]
                if type(count) is not int or count < 0 or len(manifest["runs"][qid][system]) != min(count, 10):
                    raise ValueError("Invalid result count or truncated run")
                values.append(count)
            coverage[system] = {"zero_result_queries":sum(n == 0 for n in values), "zero_result_rate":sum(n == 0 for n in values)/len(values), "queries":len(values), "mean_returned_at_10":sum(min(n,10) for n in values)/len(values)}
    label = "AI-reviewed" if judgment_source == "ai" else "Human-judged"
    report={"judgment_source":judgment_source,"corpus_sha256":manifest["corpus_sha256"],"corpus_count":manifest["corpus_count"],
        "judgments_sha256":hashlib.sha256(Path(judgments).read_bytes()).hexdigest(),
        "zero_relevance_queries":[qid for qid,g in grades.items() if not any(g.values())],
        "per_query":results,"macro":macro,"coverage":coverage,"result_counts":manifest.get("result_counts", {}),
        "limitations":f"{len(query_ids)}-query {label.lower()} pilot; recall is relative to the pooled top-10 candidates, not the entire corpus. Frozen runs are evaluated without rerunning search." + (" AI judgments are provisional and are not human ground truth or independent validation." if judgment_source == "ai" else "")}
    output.mkdir(parents=True)
    (output/"metrics.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    with (output/"per_query.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    lines=[f"# {label} relevance benchmark", "", report["limitations"], "", "| Ranker | Precision@10 | MRR@10 | nDCG@10 | Pooled recall@10 |", "| --- | --- | --- | --- | --- |"]
    for ranker,metrics in macro.items():
        values=[f"{m['value']:.4f} (n={m['queries']})" if m['value'] is not None else "Undefined (n=0)" for m in metrics.values()]
        lines.append("| "+" | ".join([ranker]+values)+" |")
    if coverage:
        lines.extend(["", "| Mode | Zero-result queries | Zero-result rate | Mean returned@10 |", "| --- | --- | --- | --- |"])
        for system in ("any", "all", "phrase"):
            item = coverage[system]
            lines.append(f"| {system} | {item['zero_result_queries']}/{item['queries']} | {item['zero_result_rate']:.2%} | {item['mean_returned_at_10']:.2f} |")
    lines.extend(["", "Zero-relevance queries: "+(", ".join(report["zero_relevance_queries"]) or "none"),"", "Corpus fingerprint: "+report["corpus_sha256"]])
    (output/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return report
