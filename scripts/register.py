#!/usr/bin/env python3
"""Map a spoken form to its written counterpart, or the reverse.

The tag does not change. Do not rewrite the text.

  python3 scripts/register.py --word တယ်
  python3 scripts/register.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "resources" / "decisions" / "register.tsv"


def load_rows(path: Path = TABLE) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        form, register, function, pair, tag, note = line.split("\t")
        index.setdefault(form, []).append({
            "form": form,
            "register": register,
            "function": function,
            "pair": pair,
            "tag": tag,
            "note": note,
        })
    return index


def lookup(word: str, index: dict[str, list[dict[str, str]]] | None = None) -> dict[str, object]:
    index = load_rows() if index is None else index
    rows = index.get(word, [])
    if not rows:
        return {"w": word, "status": "open", "note": "no register pair; leave the word as written"}
    return {
        "w": word,
        "status": "closed",
        "note": "same function in the other register; do not rewrite",
        "rows": rows,
    }


def self_test() -> None:
    index = load_rows()
    spoken = lookup("တယ်", index)
    if spoken["rows"][0]["pair"] != "သည်" or spoken["rows"][0]["tag"] != "part":
        raise AssertionError(spoken)
    written = lookup("သည်", index)
    if written["rows"][0]["pair"] != "တယ်":
        raise AssertionError(written)
    if lookup("ပွင့်", index)["status"] != "open":
        raise AssertionError("a verb has no register pair")
    print(f"SELF-TEST PASSED: {sum(len(v) for v in index.values())} register links, text is not rewritten.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up spoken/written register pairs.")
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
