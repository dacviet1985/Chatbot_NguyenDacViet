from __future__ import annotations

import re
import unicodedata
from collections import Counter


STOPWORDS = {
    "a",
    "an",
    "and",
    "bao",
    "bi",
    "cho",
    "co",
    "có",
    "cua",
    "của",
    "duoc",
    "được",
    "gi",
    "gì",
    "khi",
    "khong",
    "không",
    "la",
    "là",
    "mấy",
    "mot",
    "một",
    "neu",
    "nếu",
    "nao",
    "nào",
    "nhieu",
    "nhiều",
    "so",
    "số",
    "sao",
    "sự",
    "the",
    "thì",
    "thi",
    "theo",
    "toi",
    "tôi",
    "trong",
    "tu",
    "từ",
    "va",
    "và",
    "voi",
    "với",
}


def normalize_text(text: str) -> str:
    cleaned = unicodedata.normalize("NFKC", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    tokens = re.findall(r"[\wÀ-ỹ]+", normalized)
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def keyword_overlap_score(query: str, content: str) -> float:
    query_tokens = tokenize(query)
    content_tokens = tokenize(content)
    if not query_tokens or not content_tokens:
        return 0.0
    query_counts = Counter(query_tokens)
    content_set = set(content_tokens)
    matched = sum(weight for token, weight in query_counts.items() if token in content_set)
    return matched / max(len(query_tokens), 1)


def deduplicate_sources(items: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, object]] = set()
    unique: list[dict[str, object]] = []
    for item in items:
        key = (str(item.get("source", "")), item.get("page"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
