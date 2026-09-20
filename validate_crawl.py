#!/usr/bin/env python3
"""Kiểm tra metadata, sources.csv và số lượng tài liệu crawl K4-L3B."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path


REQUIRED_METADATA = (
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
)
FILTER_FIELDS = ("category", "language", "platform", "policy_type")
VALID_AUDIENCES = {"buyer", "seller", "both"}


def parse_frontmatter(path: Path) -> dict[str, str]:
    """Đọc YAML frontmatter đơn giản mà không cần cài PyYAML."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---(?:\s*\r?\n|\s*$)", text, re.DOTALL)
    if not match:
        return {}

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if not item:
            continue
        key, value = item.groups()
        metadata[key] = value.strip().strip('"\'')
    return metadata


def load_source_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def validate(data_dir: Path) -> int:
    errors: list[str] = []
    markdown_files = sorted(data_dir.glob("*.md"))
    csv_path = data_dir / "sources.csv"

    if not data_dir.is_dir():
        print(f"LOI: Khong tim thay thu muc: {data_dir}")
        return 1

    if not csv_path.is_file():
        print(f"LOI: Khong tim thay file: {csv_path}")
        return 1

    try:
        source_rows = load_source_rows(csv_path)
    except (OSError, csv.Error) as exc:
        print(f"LOI: Khong doc duoc {csv_path}: {exc}")
        return 1

    document_ids: list[str] = []
    audience_counts: Counter[str] = Counter()

    print(f"Thu muc : {data_dir}")
    print("-" * 76)

    for path in markdown_files:
        metadata = parse_frontmatter(path)
        missing = [key for key in REQUIRED_METADATA if not metadata.get(key)]
        has_extra_filter = any(metadata.get(key) for key in FILTER_FIELDS)
        doc_id_matches = metadata.get("doc_id") == path.stem
        audience = metadata.get("audience", "")
        audience_valid = audience in VALID_AUDIENCES

        problems: list[str] = []
        if missing:
            problems.append("thieu: " + ", ".join(missing))
        if not has_extra_filter:
            problems.append("thieu truong loc bo sung")
        if metadata.get("doc_id") and not doc_id_matches:
            problems.append("doc_id khong khop ten file")
        if audience and not audience_valid:
            problems.append("audience khong hop le")

        status = "OK" if not problems else "THIEU METADATA"
        print(f"{path.name:46} {status}")
        for problem in problems:
            print(f"  - {problem}")
            errors.append(f"{path.name}: {problem}")

        if metadata.get("doc_id"):
            document_ids.append(metadata["doc_id"])
        if audience:
            audience_counts[audience] += 1

    duplicate_ids = sorted(
        doc_id for doc_id, count in Counter(document_ids).items() if count > 1
    )
    if duplicate_ids:
        errors.append("doc_id bi trung: " + ", ".join(duplicate_ids))

    if not 5 <= len(markdown_files) <= 10:
        errors.append(f"so file Markdown la {len(markdown_files)}, yeu cau tu 5 den 10")

    if "doc_id" not in (source_rows[0].keys() if source_rows else []):
        csv_ids: list[str] = []
        errors.append("sources.csv thieu cot doc_id hoac khong co du lieu")
    else:
        csv_ids = [row.get("doc_id", "") for row in source_rows if row.get("doc_id")]

    csv_matches = sorted(csv_ids) == sorted(document_ids)
    if not csv_matches:
        errors.append("doc_id trong sources.csv khong khop cac file Markdown")

    if audience_counts["buyer"] == 0:
        errors.append("chua co tai lieu audience: buyer")
    if audience_counts["seller"] == 0:
        errors.append("chua co tai lieu audience: seller")

    print("-" * 76)
    print(f"So file : {len(markdown_files)} (can 5-10)")
    print(f"CSV     : {'KHOP' if csv_matches else 'LECH'}")
    print(f"Audience: {dict(audience_counts)}")

    if errors:
        print("\nKET QUA: CHUA DAT")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nKET QUA: DAT")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Kiem tra bo du lieu crawl K4-L3B."
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data/exchange_policy",
        type=Path,
        help="Thu muc chua cac file .md va sources.csv (mac dinh: data/exchange_policy)",
    )
    args = parser.parse_args()
    return validate(args.data_dir)


if __name__ == "__main__":
    sys.exit(main())