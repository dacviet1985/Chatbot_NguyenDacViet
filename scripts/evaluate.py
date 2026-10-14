from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.logging_config import setup_logging
from app.rag.pipeline import get_rag_pipeline
from app.rag.prompt import NO_ANSWER_TEXT
from app.utils.text import normalize_text, tokenize


def compute_relevance(answer: str, expected_answer: str) -> int:
    answer_tokens = set(tokenize(answer))
    expected_tokens = set(tokenize(expected_answer))
    if not expected_tokens:
        return 0
    overlap = len(answer_tokens & expected_tokens) / len(expected_tokens)
    if overlap >= 0.6:
        return 2
    if overlap >= 0.25:
        return 1
    return 0


def compute_faithfulness(answer: str, sources: list[dict[str, object]], expected_sources: list[str], expected_answer: str) -> int:
    if normalize_text(expected_answer) == normalize_text(NO_ANSWER_TEXT):
        return int(normalize_text(answer) == normalize_text(NO_ANSWER_TEXT))
    returned_sources = {str(item.get("source")) for item in sources}
    if expected_sources and not returned_sources.intersection(expected_sources):
        return 0
    if compute_relevance(answer, expected_answer) == 0:
        return 0
    return 1


if __name__ == "__main__":
    setup_logging()
    pipeline = get_rag_pipeline()
    questions_path = ROOT / "evaluation" / "test_questions.json"
    output_path = ROOT / "evaluation" / "evaluation_results.csv"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    rows: list[dict[str, object]] = []
    for item in questions:
        session_id = f"eval-{item['id']}"
        result = pipeline.chat(session_id=session_id, message=item["question"])
        relevance = compute_relevance(result["answer"], item["expected_answer"])
        faithfulness = compute_faithfulness(
            result["answer"],
            result["sources"],
            item.get("expected_sources", []),
            item["expected_answer"],
        )
        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answer": result["answer"],
                "expected_answer": item["expected_answer"],
                "faithfulness": faithfulness,
                "relevance": relevance,
                "sources": "; ".join(str(source.get("source")) for source in result["sources"]),
                "latency_ms": result["latency_ms"],
                "cached": result["cached"],
                "notes": item.get("notes", ""),
            }
        )

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "question",
                "answer",
                "expected_answer",
                "faithfulness",
                "relevance",
                "sources",
                "latency_ms",
                "cached",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "Total questions": len(rows),
        "Average relevance": round(mean(row["relevance"] for row in rows), 3),
        "Faithfulness rate": round(mean(row["faithfulness"] for row in rows), 3),
        "Average latency": round(mean(float(row["latency_ms"]) for row in rows), 3),
        "Cache hit rate": round(mean(1.0 if row["cached"] else 0.0 for row in rows), 3),
    }
    print("=== EVALUATION SUMMARY ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"Results saved to: {output_path}")
