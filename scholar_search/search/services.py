"""SQLite FTS5 retrieves candidates and ranks with title-weighted BM25."""
import re
from .models import Paper


def search_papers(query, year=None, sort="relevance", year_mode="since", *, ranker="weighted", match="any"):
    # Quote each token: user input cannot become an FTS operator or SQL.
    words = re.findall(r"[^\W_]+", query.casefold(), re.UNICODE)
    tokens = words[:40] if match == "phrase" else list(dict.fromkeys(words))[:40]
    if year_mode not in {"since", "exact"} or ranker not in {"weighted", "uniform"} or match not in {"any", "all", "phrase"}:
        raise ValueError("Invalid search mode or ranker")
    if not tokens:
        if query.strip() or not year:
            return Paper.objects.none()
        lookup = "published__year" if year_mode == "exact" else "published__year__gte"
        return Paper.objects.filter(**{lookup: year}).order_by("-published", "id")
    if match == "phrase":
        expression = '"' + " ".join(tokens) + '"'
    else:
        expression = (" AND " if match == "all" else " OR ").join('"' + token + '"' for token in tokens)
    # FTS5 ranking must execute in the MATCH cursor. Joining the virtual table
    # avoids rerunning the match once per candidate through a correlated query.
    papers = Paper.objects.extra(
        tables=["paper_fts"],
        where=["paper_fts MATCH %s", "paper_fts.rowid = search_paper.id"],
        params=[expression],
        select={"rank": "bm25(paper_fts, 5.0, 1.0, 2.0)" if ranker == "weighted" else "bm25(paper_fts, 1.0, 1.0, 1.0)"},
    )
    if year:
        lookup = "published__year" if year_mode == "exact" else "published__year__gte"
        papers = papers.filter(**{lookup: year})
    if sort == "newest":
        return papers.order_by("-published", "id")
    return papers.order_by("rank", "-published", "id")
