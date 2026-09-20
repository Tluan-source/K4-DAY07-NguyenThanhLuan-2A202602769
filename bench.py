"""Controlled chunking comparison. Gold evidence is used ONLY after retrieval."""
import argparse
import json
import re
import time
from pathlib import Path

from src import Document, EmbeddingStore, FixedSizeChunker, SentenceChunker, RecursiveChunker
from src.heading import HeadingChunker
from src.lexical import TfidfEmbedder, tokens
from src.embeddings import MockEmbedder, LocalEmbedder
from validate_crawl import parse_frontmatter

ROOT = Path(__file__).resolve().parent
# Evidence checks are a transparent proxy, NOT an LLM answer correctness score.
EVIDENCE = [
    ["bước 1", "bước 2", "bước 3", "bước 4", "bước 5", "bước 6", "gửi yêu cầu"],
    ["02 ngày làm việc", "48 giờ", "tự động chấp nhận"],
    ["9.818.180", "100%", "07 ngày lịch", "02 lần vi phạm"],
    ["100%", "lấy hàng tại nhà", "gửi hàng tại bưu cục", "mã vận đơn"],
    ["danh sách hạn chế trả hàng", "shopee mart", "từng thời điểm"],
]


def normalize(text):
    return " ".join(tokens(text))


def load_queries():
    queries = []
    for line in (ROOT / "benchmark.md").read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        filter_match = re.search(r'metadata_filter=(\{.*?\})', cells[1])
        question = re.sub(r"\s*\*\(Cần.*", "", cells[1]).strip()
        queries.append({"id": int(cells[0]), "question": question,
                        "gold_answer": cells[2],
                        "doc_id": re.search(r"`([^`]+)\.md`", cells[3])[1],
                        "filter": json.loads(filter_match[1]) if filter_match else None})
    if len(queries) != 5:
        raise ValueError("benchmark.md must contain exactly five queries")
    return queries


def load_corpus():
    corpus = []
    for path in sorted((ROOT / "data/exchange_policy").glob("*.md")):
        metadata = parse_frontmatter(path)
        content = re.sub(r"\A---\s*\n.*?\n---\s*(?:\n|$)", "",
                         path.read_text(encoding="utf-8"), count=1, flags=re.S).strip()
        corpus.append((path.stem, metadata, content))
    return corpus


def evaluate(store, queries, use_filter=True):
    rows = []
    for query in queries:
        hits = store.search_with_filter(query["question"], top_k=3,
                                       metadata_filter=query["filter"] if use_filter else None)
        expected = EVIDENCE[query["id"] - 1]
        gold_hits = [h for h in hits if h["metadata"]["doc_id"] == query["doc_id"]]
        context = normalize("\n".join(h["content"] for h in gold_hits))
        coverage = sum(normalize(term) in context for term in expected) / len(expected)
        top1_complete = bool(hits and hits[0]["metadata"]["doc_id"] == query["doc_id"] and
                             all(normalize(term) in normalize(hits[0]["content"]) for term in expected))
        rows.append({**query, "filtered": use_filter, "document_hit": bool(gold_hits),
                     "evidence_coverage": coverage, "evidence_complete": coverage == 1,
                     "top1_complete": top1_complete, "hits": hits})
    return rows


def run(backend="tfidf"):
    corpus, queries = load_corpus(), load_queries()
    # Fit on raw corpus ONCE so IDF and vocabulary do not change with chunking.
    embedder = {"tfidf": lambda: TfidfEmbedder(c[2] for c in corpus),
                "mock": MockEmbedder, "local": LocalEmbedder}[backend]()
    strategies = {"fixed": FixedSizeChunker(1000, 100), "sentence": SentenceChunker(3),
                  "recursive": RecursiveChunker(chunk_size=1000),
                  **{f"heading_{size}": HeadingChunker(size) for size in (600, 1000, 1400)}}
    report = {"backend": embedder._backend_name, "evaluation": "evidence proxy; no LLM evaluation",
              "strategies": {}}
    for name, chunker in strategies.items():
        chunk_started = time.perf_counter()
        documents = []
        for doc_id, metadata, body in corpus:
            sections = (chunker.sections(body) if isinstance(chunker, HeadingChunker)
                        else [{"content": c, "section_path": ""} for c in chunker.chunk(body)])
            for i, section in enumerate(sections):
                documents.append(Document(id=f"{doc_id}#{i}", content=section["content"],
                    metadata={**metadata, "doc_id": doc_id, "chunk_index": i,
                              "section_path": section["section_path"], "strategy": name}))
        chunking_ms = (time.perf_counter() - chunk_started) * 1000

        indexing_started = time.perf_counter()
        store = EmbeddingStore(embedding_fn=embedder)
        store.add_documents(documents)
        indexing_ms = (time.perf_counter() - indexing_started) * 1000

        query_started = time.perf_counter()
        rows = evaluate(store, queries)
        query_ms = (time.perf_counter() - query_started) * 1000
        report["strategies"][name] = {"count": len(documents),
            "avg_length": sum(len(d.content) for d in documents) / len(documents),
            "chunking_ms": chunking_ms,
            "indexing_ms": indexing_ms,
            "avg_query_ms": query_ms / len(queries),
            "results": rows, "filter_ab": evaluate(store, [queries[1]], False)}
        print(f"{name:15} chunks={len(documents):3} "
              f"doc-hit@3={sum(r['document_hit'] for r in rows)}/5 "
              f"complete-evidence@3={sum(r['evidence_complete'] for r in rows)}/5 "
              f"complete-top1={sum(r['top1_complete'] for r in rows)}/5")
    return report


def save(report, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "benchmark_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"Backend: {report['backend']}", report["evaluation"],
             "Evidence matched only inside retrieved gold-document chunks; gold never used for ranking.",
             "These five questions are development data; results are not held-out accuracy."]
    for name, result in report["strategies"].items():
        lines.append(f"\n=== {name}: {result['count']} chunks; avg={result['avg_length']:.1f} ===")
        for row in result["results"] + result["filter_ab"]:
            lines.append(f"\nQ{row['id']} filter={row['filter'] if row['filtered'] else None}: {row['question']}\n"
                         f"Evidence coverage={row['evidence_coverage']:.0%}; complete-top1={row['top1_complete']}")
            for i, hit in enumerate(row["hits"], 1):
                lines.append(f"{i}. {hit['id']} score={hit['score']:.4f}\n{hit['content']}")
    (output / "ket_qua_benchmark.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["tfidf", "mock", "local"], default="tfidf")
    parser.add_argument("--output", type=Path, default=ROOT / "report/strategy")
    args = parser.parse_args()
    save(run(args.backend), args.output)
