# Project checklist

| Requirement | Status | File | Evidence |
|---|---|---|---|
| PDF/TXT ingestion | DONE | app/rag/loader.py | `pytest` passed + `scripts/ingest.py` loaded 3 files / 5 documents |
| Chunking | DONE | app/rag/chunker.py | `pytest` passed + ingest created 5 chunks |
| Embedding | DONE | app/rag/embeddings.py | OpenAI configurable, local fallback used successfully in ingest/eval |
| FAISS | DONE | app/rag/vector_store.py | FAISS interface implemented with numpy fallback validated by retrieval/eval |
| Metadata source/page | DONE | app/rag/loader.py | PDF pages + TXT source verified in `tests/test_ingestion.py` |
| Top-K retrieval | DONE | app/rag/retriever.py | Retrieval logs show ranked docs with score + lexical score |
| Grounded prompt | DONE | app/rag/prompt.py | Refusal text returned for unsupported question in evaluation question 11 |
| Hallucination protection | DONE | app/rag/pipeline.py | Evaluation faithfulness rate = 1.0 |
| Citation | DONE | app/rag/pipeline.py | `sources` returned in cache demo and evaluation CSV |
| Memory | DONE | app/rag/memory.py | Follow-up demo `Còn nhân viên thử việc thì sao?` returned contextual answer |
| Tool | DONE | app/tools/calculator.py; app/tools/weather.py | Calculator + weather tool hoạt động |
| FastAPI /health | DONE | app/api/routes.py | Endpoint covered by `tests/test_api.py` |
| FastAPI /chat | DONE | app/api/routes.py | Endpoint covered by `tests/test_api.py` |
| Cache | DONE | app/core/cache.py | Manual cache demo showed first `cached=false`, second `cached=true` |
| Streamlit | DONE | ui/streamlit_app.py | Streamlit started successfully on `http://localhost:8501` |
| Logging | DONE | app/core/logging_config.py | `logs/app.log` contains retriever, cache, tool, latency, final answer logs |
| Evaluation | DONE | scripts/evaluate.py | `evaluation/evaluation_results.csv` generated |
| Failure cases | DONE | evaluation/failure_cases.md | 2 cases documented |
| Advanced RAG bonus | DONE | app/rag/retriever.py | Query transformation for follow-up questions |
| Tests | DONE | tests/ | `8 passed` |
| Weather tool | DONE | app/tools/weather.py | live query `thời tiết Hà Nội hôm nay` trả kết quả |
| Report 3-5 pages | DONE | docs/report.md | kiến trúc, prompt, evaluation, failure cases, hướng dẫn chạy |
| requirements.txt | DONE | requirements.txt | dependency list committed |
| .env.example | DONE | .env.example | env template committed |
| README.md | DONE | README.md | setup/run guide completed |
| architecture.md | DONE | docs/architecture.md | offline/online architecture documented |
| demo_script.md | DONE | docs/demo_script.md | 10-step demo flow completed |
| rag_explanation.md | DONE | docs/rag_explanation.md | chunking / top-k rationale documented |
| project_checklist.md | DONE | docs/project_checklist.md | validated with actual evidence |
