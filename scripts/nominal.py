#!/usr/bin/env python3
"""Noun, pronoun, and adjective classes. One tag per class, never DET or PROPN.

  python3 scripts/nominal.py --class pronoun
  python3 scripts/nominal.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "resources" / "decisions" / "nominals.tsv"


def load_rows(path: Path = TABLE) -> list[dict[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        kind, function, tag, ud, nlp = line.split("\t")
        rows.append({"class": kind, "function": function, "tag": tag, "ud": ud, "nlp": nlp})
    return rows


def lookup(kind: str, rows: list[dict[str, str]] | None = None) -> dict[str, object]:
    rows = load_rows() if rows is None else rows
    hit = [row for row in rows if row["class"] == kind or row["class"].startswith(kind + "-")]
    if not hit:
        return {"class": kind, "status": "open", "note": "not a noun, pronoun, or adjective class"}
    return {"class": kind, "status": "closed", "rows": hit}


def self_test() -> None:
    rows = load_rows()
    noun = lookup("noun", rows)
    if noun["rows"][0]["tag"] != "n":
        raise AssertionError(noun)
    if any(row["tag"] == "DET" or row["ud"] == "DET" for row in rows):
        raise AssertionError("DET is not a myPOS tag")
    pron = lookup("pronoun-demonstrative", rows)
    if pron["rows"][0]["tag"] != "pron":
        raise AssertionError(pron)
    adj = lookup("adjective-quality", rows)
    if adj["rows"][0]["tag"] != "adj":
        raise AssertionError(adj)
    print(f"SELF-TEST PASSED: {len(rows)} nominal classes, one tag each, no DET.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up noun, pronoun, and adjective classes.")
    parser.add_argument("--class", dest="kind")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.kind:
        parser.error("pass --class or --self-test")
    json.dump(lookup(args.kind), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
