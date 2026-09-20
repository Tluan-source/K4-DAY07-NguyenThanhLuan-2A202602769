"""Serve the demo UI and a live, offline retrieval API.

Run from the project root:
    python demo_server.py
Then open http://127.0.0.1:8766/src/demo.html
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from bench import load_corpus, run as run_benchmark
from src import Document, EmbeddingStore, HeadingChunker
from src.lexical import TfidfEmbedder


ROOT = Path(__file__).resolve().parent


def load_env_file() -> None:
    """Load simple KEY=VALUE pairs without requiring python-dotenv."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


load_env_file()


class LiveRetriever:
    """Build the Heading-1400 index once and answer queries from that index."""

    def __init__(self) -> None:
        corpus = load_corpus()
        self.embedder = TfidfEmbedder(body for _, _, body in corpus)
        self.store = EmbeddingStore(embedding_fn=self.embedder)
        documents: list[Document] = []

        for doc_id, metadata, body in corpus:
            for index, section in enumerate(HeadingChunker(1400).sections(body)):
                documents.append(
                    Document(
                        id=f"{doc_id}#{index}",
                        content=section["content"],
                        metadata={
                            **metadata,
                            "doc_id": doc_id,
                            "chunk_index": index,
                            "section_path": section["section_path"],
                            "strategy": "heading_1400",
                        },
                    )
                )
        self.store.add_documents(documents)

    @staticmethod
    def _answer(hits: list[dict[str, Any]]) -> str:
        if not hits or hits[0]["score"] <= 0:
            return "Không tìm thấy thông tin đủ liên quan trong bộ tài liệu hiện có."

        content = hits[0]["content"].strip()
        # Remove the repeated heading path from the answer body; it remains visible
        # on the retrieved chunk card and in section_path.
        body = content.split("\n\n", 1)[-1].strip()
        if len(body) > 1200:
            body = body[:1200].rsplit(" ", 1)[0] + "…"
        return f"Theo đoạn chính sách được truy xuất [1]:\n\n{body}"

    def chat(self, query: str, audience: str | None, top_k: int) -> dict[str, Any]:
        started = time.perf_counter()
        metadata_filter = {"audience": audience} if audience in {"buyer", "seller"} else None
        hits = self.store.search_with_filter(query, top_k=top_k, metadata_filter=metadata_filter)
        candidates = [
            record for record in self.store._store
            if not metadata_filter
            or all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        chunks = []
        for hit in hits:
            metadata = hit["metadata"]
            chunks.append(
                {
                    "id": hit["id"],
                    "doc_id": metadata["doc_id"],
                    "audience": metadata.get("audience", "unknown").strip('"'),
                    "title": metadata.get("title", metadata["doc_id"]),
                    "section_path": metadata.get("section_path", ""),
                    "score": hit["score"],
                    "snippet": hit["content"],
                }
            )
        return {
            "query": query,
            "filter": audience,
            "top_k": top_k,
            "candidate_count": len(candidates),
            "total_count": self.store.get_collection_size(),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "backend": self.embedder._backend_name,
            "strategy": "HeadingChunker(1400)",
            "chunks": chunks,
            "answer": self._answer(hits),
        }


RETRIEVER = LiveRetriever()


STRATEGY_INFO = {
    "fixed": {
        "label": "Fixed Size",
        "config": "1000 chars · overlap 100",
        "principle": "Cắt theo số ký tự cố định; phần giao nhau giảm mất ngữ cảnh ở biên.",
    },
    "sentence": {
        "label": "Sentence",
        "config": "3 câu / chunk",
        "principle": "Gom theo ranh giới câu; dễ đọc nhưng có thể tách quy trình nhiều bước.",
    },
    "recursive": {
        "label": "Recursive",
        "config": "1000 chars",
        "principle": "Ưu tiên đoạn, dòng, câu rồi từ để giữ cấu trúc tự nhiên khi có thể.",
    },
    "heading_600": {
        "label": "Heading",
        "config": "600 chars",
        "principle": "Giữ đường dẫn heading cha–con; fallback đệ quy cho mục dài.",
    },
    "heading_1000": {
        "label": "Heading",
        "config": "1000 chars",
        "principle": "Giữ đường dẫn heading với ngưỡng cân bằng giữa độ chi tiết và ngữ cảnh.",
    },
    "heading_1400": {
        "label": "Heading",
        "config": "1400 chars",
        "principle": "Giữ mục chính sách dài hơn để bằng chứng nhiều bước nằm cùng một chunk.",
    },
}


def api_configuration() -> dict[str, Any]:
    base_url = os.getenv("BASE_URL") or os.getenv("OPENAI_BASE_URL") or ""
    model = os.getenv("OPENAI_EMBEDDING_MODEL") or os.getenv("MODEL") or ""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") or ""
    return {
        "configured": bool(api_key and base_url and model),
        "base_url_configured": bool(base_url),
        "model": model,
    }


def build_comparison_payload() -> dict[str, Any]:
    started = time.perf_counter()
    report = run_benchmark("tfidf")
    strategies = []
    for name, result in report["strategies"].items():
        rows = result["results"]
        info = STRATEGY_INFO[name]
        strategies.append(
            {
                "id": name,
                **info,
                "chunk_count": result["count"],
                "avg_chars": round(result["avg_length"], 1),
                "chunking_ms": round(result.get("chunking_ms", 0.0), 3),
                "indexing_ms": round(result.get("indexing_ms", 0.0), 3),
                "avg_query_ms": round(result.get("avg_query_ms", 0.0), 3),
                "document_hit_at_3": sum(row["document_hit"] for row in rows),
                "evidence_complete_at_3": sum(row["evidence_complete"] for row in rows),
                "top1_complete": sum(row["top1_complete"] for row in rows),
                "avg_evidence_coverage_pct": round(
                    sum(row["evidence_coverage"] for row in rows) / len(rows) * 100, 1
                ),
                "queries": [
                    {
                        "id": row["id"],
                        "question": row["question"],
                        "document_hit": row["document_hit"],
                        "evidence_coverage_pct": round(row["evidence_coverage"] * 100, 1),
                        "evidence_complete": row["evidence_complete"],
                        "top1_complete": row["top1_complete"],
                        "top_doc_id": row["hits"][0]["metadata"]["doc_id"] if row["hits"] else None,
                        "top_score": round(row["hits"][0]["score"], 4) if row["hits"] else 0.0,
                    }
                    for row in rows
                ],
            }
        )
    return {
        "backend": report["backend"],
        "evaluation": report["evaluation"],
        "corpus_documents": len(load_corpus()),
        "benchmark_queries": 5,
        "top_k": 3,
        "build_ms": round((time.perf_counter() - started) * 1000, 2),
        "api": api_configuration(),
        "recommended_strategy": "heading_1400",
        "metrics": [
            {
                "id": "document_hit_at_3",
                "label": "Document Hit@3",
                "formula": "Số query có tài liệu chuẩn xuất hiện trong top 3 / 5",
                "purpose": "Đo khả năng tìm đúng nguồn, chưa xét đủ bằng chứng.",
            },
            {
                "id": "evidence_complete_at_3",
                "label": "Complete Evidence@3",
                "formula": "Số query có đủ toàn bộ cụm bằng chứng trong các chunk chuẩn thuộc top 3 / 5",
                "purpose": "Đo độ phủ ngữ cảnh cần thiết để trả lời đầy đủ.",
            },
            {
                "id": "top1_complete",
                "label": "Complete Top-1",
                "formula": "Top 1 phải đúng tài liệu và một chunk chứa đủ mọi cụm bằng chứng / 5",
                "purpose": "Tiêu chí khó nhất: một chunk đầu tiên phải đủ để trả lời.",
            },
            {
                "id": "avg_evidence_coverage_pct",
                "label": "Avg. Evidence Coverage",
                "formula": "Trung bình tỷ lệ cụm bằng chứng tìm thấy trong chunk chuẩn của top 3",
                "purpose": "Cho biết mức độ thiếu bằng chứng ngay cả khi chưa đạt đủ 100%.",
            },
        ],
        "strategies": strategies,
    }


COMPARISON = build_comparison_payload()


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._json(200, {
                "status": "ready",
                "chunks": RETRIEVER.store.get_collection_size(),
                "comparison_strategies": len(COMPARISON["strategies"]),
                "api_configured": COMPARISON["api"]["configured"],
            })
            return
        if self.path == "/api/compare":
            self._json(200, COMPARISON)
            return
        super().do_GET()

    def do_POST(self) -> None:
        global COMPARISON
        if self.path == "/api/compare":
            COMPARISON = build_comparison_payload()
            self._json(200, COMPARISON)
            return
        if self.path != "/api/chat":
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 32_768:
                raise ValueError("Kích thước yêu cầu không hợp lệ")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            query = re.sub(r"\s+", " ", str(payload.get("query", ""))).strip()
            if not query:
                raise ValueError("Vui lòng nhập câu hỏi")
            audience = payload.get("audience")
            if audience not in {None, "none", "buyer", "seller"}:
                raise ValueError("Bộ lọc audience không hợp lệ")
            top_k = int(payload.get("top_k", 3))
            if top_k not in {3, 5}:
                raise ValueError("top_k chỉ hỗ trợ 3 hoặc 5")
            self._json(200, RETRIEVER.chat(query, None if audience == "none" else audience, top_k))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception:
            self._json(500, {"error": "Không thể xử lý câu hỏi"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    print(f"Live demo: http://{args.host}:{args.port}/src/demo.html")
    print(f"Indexed {RETRIEVER.store.get_collection_size()} Heading-1400 chunks")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
