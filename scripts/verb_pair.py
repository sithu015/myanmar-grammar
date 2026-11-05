#!/usr/bin/env python3
"""Look up a simplex or causative verb. The myPOS tag stays v either way.

  python3 scripts/verb_pair.py --word ပွင့်
  python3 scripts/verb_pair.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "resources" / "decisions" / "causative_pairs.tsv"


def load_pairs(path: Path = TABLE) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        simplex, causative, kind, s_gloss, c_gloss = line.split("\t")
        row = {
            "simplex": simplex,
            "causative": causative,
            "kind": kind,
            "simplex_gloss": s_gloss,
            "causative_gloss": c_gloss,
        }
        index[simplex] = {**row, "role": "simplex", "pair": causative, "gloss": s_gloss}
        index[causative] = {**row, "role": "causative", "pair": simplex, "gloss": c_gloss}
    return index


def lookup(word: str, index: dict[str, dict[str, str]] | None = None) -> dict[str, object]:
    index = load_pairs() if index is None else index
    row = index.get(word)
    if row is None:
        return {"w": word, "status": "open", "tag": "v", "note": "not an Okell pair; tag stays v if it is a verb"}
    note = "modal part when it follows a verb" if word == "လိမ့်" else "same myPOS tag v; valency differs"
    return {"w": word, "status": "closed", "tag": "v", "note": note, **row}


def self_test() -> None:
    index = load_pairs()
    opened = lookup("ပွင့်", index)
    closed = lookup("ဖွင့်", index)
    if opened["role"] != "simplex" or opened["pair"] != "ဖွင့်":
        raise AssertionError(opened)
    if closed["role"] != "causative" or closed["pair"] != "ပွင့်":
        raise AssertionError(closed)
    if lookup("စား", index)["pair"] != "ကျွေး":
        raise AssertionError("suppletive")
    if lookup("စေ", index)["status"] != "open":
        raise AssertionError("စေ is a particle, not a pair member")
    print(f"SELF-TEST PASSED: {len(index)} verb forms, simplex and causative share tag v.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up a simplex/causative pair.")
    parser.add_argument("--word")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.word:
        parser.error("pass --word or --self-test")
    json.dump(lookup(args.word), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
