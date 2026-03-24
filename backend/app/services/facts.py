import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from app.rag.normalize import normalize_text

logger = logging.getLogger(__name__)


@dataclass
class FactHit:
    statement: str
    values: str
    source: str
    matched_terms: List[str]
    tags: List[str]
    score: float


FACTS_DIR = os.environ.get(
    "FACTS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "knowledge", "facts"),
)


def _parse_frontmatter(lines: List[str]) -> dict:
    data: dict = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _parse_tags(raw: str) -> List[str]:
    if not raw:
        return []
    cleaned = raw.strip().strip("[]")
    parts = [p.strip().strip("\"'") for p in cleaned.split(",") if p.strip()]
    return parts


def _parse_fact_file(path: Path) -> FactHit | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("fact_read_failed", extra={"path": str(path), "error": str(exc)})
        return None

    if not text.startswith("---"):
        logger.warning("fact_no_frontmatter", extra={"path": str(path)})
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        logger.warning("fact_frontmatter_parse_failed", extra={"path": str(path)})
        return None

    fm_raw = parts[1].strip().splitlines()
    body = parts[2]

    fm = _parse_frontmatter(fm_raw)
    source = fm.get("source", "").strip('"')
    tags = _parse_tags(fm.get("tags", ""))

    statement = ""
    values = ""
    for line in body.splitlines():
        if line.startswith("Statement:"):
            statement = line.replace("Statement:", "").strip()
        elif line.startswith("Value(s):"):
            values = line.replace("Value(s):", "").strip()

    if not statement:
        logger.warning("fact_missing_statement", extra={"path": str(path)})
        return None

    return FactHit(
        statement=statement,
        values=values,
        source=source or str(path),
        matched_terms=[],
        tags=tags,
        score=0.0,
    )


def _canonicalize_token(token: str) -> str:
    canonical = token.strip().lower()
    if len(canonical) > 3 and canonical.startswith("لل"):
        canonical = canonical[1:]
    if len(canonical) > 3 and canonical.startswith("ال"):
        canonical = canonical[2:]
    elif len(canonical) > 3 and canonical.startswith("ل"):
        canonical = canonical[1:]
    return canonical


def _tokenize(text: str) -> List[str]:
    cleaned = normalize_text(text).replace("/", " ")
    tokens = [_canonicalize_token(token) for token in cleaned.split()]
    return [token for token in tokens if len(token) > 1]


AR_STOPWORDS = {"من", "في", "على", "هل", "عندي", "عن", "إلى", "الى", "مع", "ما", "متى", "كم"}
EN_STOPWORDS = {"the", "is", "at", "on", "in", "and", "or", "a", "an", "of"}


def _filter_stopwords(tokens: List[str]) -> List[str]:
    return [
        t
        for t in tokens
        if t not in AR_STOPWORDS and t not in EN_STOPWORDS
    ]


def search_facts(question: str, category: str) -> List[FactHit]:
    facts_dir = Path(FACTS_DIR).resolve()
    if not facts_dir.exists():
        logger.warning("facts_dir_missing", extra={"path": str(facts_dir)})
        return []

    tokens = _filter_stopwords(_tokenize(question))
    hits: List[FactHit] = []

    for path in facts_dir.glob("*.md"):
        fact = _parse_fact_file(path)
        if not fact:
            continue

        haystack_tokens = set(_tokenize(f"{fact.statement} {fact.values}"))
        matched = [token for token in tokens if token in haystack_tokens]
        tag_match = category != "unknown" and category in fact.tags

        if not matched and not tag_match:
            continue
        keyword_score = 0.0
        if tokens:
            keyword_score = len(set(matched)) / len(set(tokens))

        tag_score = 0.0
        if category != "unknown" and category in fact.tags:
            tag_score = 0.35

        fact_score = min(keyword_score + tag_score, 1.0)

        if fact_score < 0.2:
            continue

        fact.matched_terms = matched if matched else [f"tag:{category}"]
        fact.score = fact_score
        hits.append(fact)

    # Sort by score first, then by how many distinct query terms matched. This keeps
    # direct duration facts ahead of generic same-category facts after query normalization.
    hits.sort(
        key=lambda hit: (
            hit.score,
            len(set(hit.matched_terms)),
            hit.statement,
        ),
        reverse=True,
    )
    top_k = 3
    return hits[:top_k]
