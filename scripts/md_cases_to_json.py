from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEADER_RE = re.compile(r"^#\s*验案\b.*$", re.MULTILINE)


def split_cases(md_text: str) -> list[dict]:
    matches = list(HEADER_RE.finditer(md_text))
    if not matches:
        content = md_text.strip("\n")
        if not content:
            return []
        return [{"title": None, "content": content}]

    cases: list[dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        chunk = md_text[start:end].strip("\n")
        lines = chunk.splitlines()
        title = lines[0].strip() if lines else None
        content = "\n".join(lines[1:]).strip("\n") if len(lines) > 1 else ""
        cases.append({"title": title, "content": content})

    return cases


def convert_one(md_path: Path, output_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    cases = split_cases(text)

    doc = {
        "source_md": md_path.name,
        "case_count": len(cases),
        "cases": [
            {
                "index": idx + 1,
                "title": c.get("title"),
                "content": c.get("content"),
            }
            for idx, c in enumerate(cases)
        ],
    }

    output_path.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-dir",
        default=str(Path(__file__).resolve().parents[1] / "corpus"),
    )
    parser.add_argument("--pattern", default="*.md")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--merge-name", default="_all_cases.json")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    md_files = sorted(corpus_dir.glob(args.pattern))

    merged: list[dict] = []
    for md_path in md_files:
        if not md_path.is_file():
            continue
        out_path = md_path.with_suffix(".json")
        doc = convert_one(md_path, out_path)
        if args.merge:
            for c in doc.get("cases", []):
                merged.append({"source_md": doc.get("source_md"), **c})

    if args.merge:
        (corpus_dir / args.merge_name).write_text(
            json.dumps({"count": len(merged), "cases": merged}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
