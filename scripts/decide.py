#!/usr/bin/env python3
"""Fast myPOS decision for one Burmese line.

Reads resources/decisions/homographs.tsv. Closed rows fire immediately.
Homographs that miss every frame return status=review and the legal readings,
so the agent does not hunt the long guides.

  python3 scripts/decide.py --tokens 'တရားလို သည် လျှောက်ထား သည် ။'
  python3 scripts/decide.py --text 'တရားလိုသည်လျှောက်ထားသည်။'
  python3 scripts/decide.py --word နှစ်
  python3 scripts/decide.py --self-test
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "resources" / "decisions" / "homographs.tsv"

PUNCT = set("။၊၊!?？！…-—–()[]{}「」『』\"'“”‘’")
SYMBOLS = set("%$£¥#&@+=×÷λ")
CLASSIFIERS = {"ဦး", "ယောက်", "ခု", "ရပ်", "ပါး", "ကြိမ်", "မျိုး", "စုံ", "လုံး", "ကောင်", "စီး", "အုပ်"}
TEXTNUMS = {"တ", "တစ်", "နှစ်", "သုံး", "လေး", "ငါး", "ခြောက်", "ခုနစ်", "ရှစ်", "ကိုး", "ဆယ်", "ရာ", "ထောင်", "သိန်း", "သန်း", "သုည"}
TAGS = {"abb", "adj", "adv", "conj", "fw", "int", "n", "num", "part", "ppm", "pron", "punc", "sb", "tn", "v"}
SUBSECTION = set("ကခဂဃငစဆဇဈဉညဋဌဍဎဏတထဒဓနပဖဗဘမယရလဝသဟဠအဣဤဥဦဧဩဪ")
ASPECT_AFTER_VERB = {"နေ", "ခဲ့"}
ASPECT_VERBS = {
    "စီစဉ်", "ဆောင်ရွက်", "လျှောက်ထား", "စစ်ဆေး", "ဖော်ပြ", "ကျင်းပ", "တက်ရောက်",
    "ထုတ်ပြန်", "ချမှတ်", "ဆုံးဖြတ်", "ပြော", "လုပ်", "ရေးသား", "ဖတ်", "ကြည့်",
    "သိ", "ဆို", "ပေါ်ပေါက်", "ကျူးလွန်", "ရောက်", "ဖြစ်", "သွား", "လာ", "ပေး",
    "ထား", "ရှိ", "ဝင်", "ပြု", "လိုက်နာ", "ပြောဆို", "ကြား", "ရွေး", "ချယ်", "ခုတ်",
    "ဆောက်", "ကျ", "ချ", "ကျက်", "ချက်", "ပွင့်", "ဖွင့်", "ပျက်", "ဖျက်",
    "လွတ်", "လွှတ်", "မြင့်", "မြှင့်", "စား", "ကျွေး", "သေ", "သတ်", "စေ", "ခိုင်း",
    "ဟုတ်",
}
NEGATABLE = ASPECT_VERBS | {
    "ဟုတ်", "ကောင်း", "မှား", "မှန်", "သင့်", "ရ", "နိုင်", "စေ", "ပြီး", "နေ",
    "ခဲ့", "လိုက်", "များ", "လှ", "ကြီး",
}


def load_table(path: Path = TABLE) -> dict[str, list[dict[str, str]]]:
    table: dict[str, list[dict[str, str]]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        surface, when, tag, rule, note = line.split("\t")
        if tag not in TAGS:
            raise ValueError(f"bad tag {tag} on {surface}")
        table.setdefault(surface, []).append(
            {"when": when, "tag": tag, "rule": rule, "note": note}
        )
    return table


def _is_number(token: str) -> bool:
    if not token:
        return False
    core = token.replace(",", "").replace("၊", "")
    return core.isdigit() or all("၀" <= ch <= "၉" for ch in core)


def _clause(clause: str, prev: str, nxt: str, prev2: str, nxt2: str = "") -> bool:
    clause = clause.strip()
    if clause == "always":
        return True
    if clause == "at_end":
        return nxt == "" or nxt in PUNCT
    if clause == "medial":
        return prev != "" and nxt not in ("",) and nxt not in PUNCT
    if clause == "next_word":
        return nxt not in ("",) and nxt not in PUNCT
    if clause == "next_clf":
        return nxt in CLASSIFIERS
    if clause == "prev_textnum":
        return prev in TEXTNUMS or _is_number(prev)
    if clause == "between_num":
        return (_is_number(prev) or prev in TEXTNUMS) and (_is_number(nxt) or nxt in TEXTNUMS)
    if clause == "after_word":
        return prev != "" and prev not in PUNCT
    if clause == "prev_verb":
        return prev in ASPECT_VERBS
    if clause == "next_neg":
        return nxt in NEGATABLE
    if clause == "next_verb":
        return nxt in ASPECT_VERBS
    if clause == "initial":
        return prev == "" or prev in PUNCT
    if clause == "reading":
        return False
    if clause.startswith("prev2:"):
        return prev2 == clause[6:]
    if clause.startswith("prev_in:"):
        return prev in clause[8:].split("|")
    if clause.startswith("next_in:"):
        return nxt in clause[8:].split("|")
    if clause.startswith("prev:"):
        return prev == clause[5:]
    if clause.startswith("next:"):
        return nxt == clause[5:]
    if clause == "next_end":
        return nxt2 == "" or nxt2 in PUNCT
    if clause == "next2_word":
        return nxt2 not in ("",) and nxt2 not in PUNCT
    if clause.startswith("next2:"):
        return nxt2 == clause[6:]
    raise ValueError(f"unknown when-clause {clause}")


def matches(when: str, prev: str, nxt: str, prev2: str, nxt2: str = "") -> bool:
    if when.startswith("all:"):
        return all(_clause(part.strip(), prev, nxt, prev2, nxt2) for part in when[4:].split("&"))
    return _clause(when, prev, nxt, prev2, nxt2)


def _script_token(token: str) -> dict[str, object] | None:
    if all(ch in PUNCT for ch in token):
        return {"tag": "punc", "rule": "CHAR_PUNC", "status": "closed", "note": "punctuation"}
    if token in SYMBOLS or all(ch in SYMBOLS for ch in token):
        return {"tag": "sb", "rule": "CHAR_SYMBOL", "status": "closed", "note": "symbol"}
    if _is_number(token) and any("၀" <= ch <= "၉" for ch in token):
        return {"tag": "num", "rule": "CHAR_MYDIGIT", "status": "closed", "note": "Myanmar digits"}
    if token.isascii() and any(ch.isalpha() for ch in token):
        return {"tag": "fw", "rule": "CHAR_LATIN", "status": "closed", "note": "Latin word; Myanmar loans stay n"}
    return None


def decide_tokens(tokens: list[str], table: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []

    def stamp(payload: dict[str, object], prev: str, nxt: str) -> None:
        payload["left"] = prev
        payload["right"] = nxt
        out.append(payload)

    for i, token in enumerate(tokens):
        prev = tokens[i - 1] if i else ""
        prev2 = tokens[i - 2] if i > 1 else ""
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        nxt2 = tokens[i + 2] if i + 2 < len(tokens) else ""
        if token in SUBSECTION and prev in "([" and nxt in ")]":
            stamp({
                "i": i, "w": token, "tag": "sb", "rule": "SUBSECTION_SB",
                "status": "closed", "note": "parenthetical subsection letter, not a word",
                "readings": [],
            }, prev, nxt)
            continue
        if token in ASPECT_AFTER_VERB and prev in ASPECT_VERBS:
            stamp({
                "i": i, "w": token, "tag": "part", "rule": "ASPECT_AFTER_V",
                "status": "closed", "note": "aspect after a listed verb; ပြီး stays review",
                "readings": [],
            }, prev, nxt)
            continue
        scripted = _script_token(token)
        if scripted is not None:
            stamp({"i": i, "w": token, **scripted, "readings": []}, prev, nxt)
            continue
        rows = table.get(token, [])
        hit = None
        for row in rows:
            if matches(row["when"], prev, nxt, prev2, nxt2):
                hit = row
                break
        readings = [
            {"tag": row["tag"], "when": row["when"], "rule": row["rule"], "note": row["note"]}
            for row in rows
            if row["when"] == "reading" or hit is None
        ]
        if hit is not None:
            stamp(
                {
                    "i": i,
                    "w": token,
                    "tag": hit["tag"],
                    "rule": hit["rule"],
                    "status": "closed",
                    "note": hit["note"],
                    "readings": [r for r in readings if r["rule"] != hit["rule"]],
                },
                prev,
                nxt,
            )
        elif rows:
            stamp(
                {
                    "i": i,
                    "w": token,
                    "tag": None,
                    "rule": None,
                    "status": "review",
                    "note": "frame matched no closed row; pick one reading or leave for review",
                    "readings": readings or [
                        {"tag": row["tag"], "when": row["when"], "rule": row["rule"], "note": row["note"]}
                        for row in rows
                    ],
                },
                prev,
                nxt,
            )
        else:
            stamp(
                {
                    "i": i,
                    "w": token,
                    "tag": None,
                    "rule": None,
                    "status": "open",
                    "note": "content word; do not invent a function tag",
                    "readings": [],
                },
                prev,
                nxt,
            )
    return out


def lookup_word(word: str, table: dict[str, list[dict[str, str]]]) -> dict[str, object]:
    rows = table.get(word, [])
    if not rows:
        return {"w": word, "status": "open", "note": "no closed rule; content word or unseen", "readings": []}
    return {
        "w": word,
        "status": "catalog",
        "readings": [
            {"tag": row["tag"], "when": row["when"], "rule": row["rule"], "note": row["note"]}
            for row in rows
        ],
    }


def _expect(tokens: str, index: int, tag: str, status: str = "closed") -> None:
    decided = decide_tokens(tokens.split(), load_table())
    got = decided[index]
    if got["tag"] != tag or got["status"] != status:
        raise AssertionError(f"{tokens!r} [{index}] got {got['tag']}/{got['status']} want {tag}/{status}")


def self_test() -> None:
    _expect("တရားလို သည် လျှောက်ထား သည် ။", 1, "ppm")
    _expect("တရားလို သည် လျှောက်ထား သည် ။", 3, "part")
    _expect("ဆို သည် မှာ", 1, "part")
    _expect("ဆို သည် မှာ", 2, "ppm")
    _expect("နှစ် ဦး", 0, "tn")
    _expect("နှစ် ဦး", 1, "part")
    _expect("သုံး နှစ် ကြာ", 0, "tn")
    _expect("သုံး နှစ် ကြာ", 1, "n")
    _expect("တ ရာ", 1, "tn")
    _expect("ဆောင်ရွက် ရာ တွင်", 1, "part")
    _expect("တပြိုင်နက်", 0, "adv")
    _expect("( က )", 1, "sb")
    _expect("လိုအပ် ပါ က", 2, "conj")
    _expect("ဥပဒေ နှင့် အညီ", 1, "ppm")
    _expect("မ သွား", 0, "part")
    _expect("ကျား - မ ဘာဝ", 2, "n")
    _expect("သုည ဒသမ တစ်", 1, "n")
    _expect("ဒသမ အကြိမ်", 0, "adj")
    _expect("တစ်စုံတစ်ရာ ကို", 0, "pron")
    _expect("( ဂ )", 1, "sb")
    _expect("စီစဉ် နေ", 1, "part")
    _expect("ဒဏ်ရာ ရ", 1, "v")
    _expect("အပါအဝင်", 0, "ppm")
    _expect("နှင့်တကွ", 0, "conj")
    _expect("၇ နာရီ", 1, "n")
    _expect("ဆောင်ရွက် သည် ဟု", 1, "part")
    _expect("တရားလို သည် မှာ", 1, "ppm")
    _expect("ဆောင်ရွက် သည် ကို", 1, "part")
    _expect("ဆောင်ရွက် ရာ နေရာ", 1, "part")
    _expect("ဆောင်ရွက် ရ မည်", 1, "part")
    _expect("မ ရ", 1, "v")
    _expect("နှစ် ရာ", 0, "tn")
    _expect("နှစ် လ", 0, "tn")
    _expect("နှစ် လ", 1, "n")
    _expect("အား ရှိ", 0, "n")
    _expect("တရားခံ အား စစ်ဆေး", 1, "ppm")
    _expect("တရားခံ ကို စစ်ဆေး", 1, "ppm")
    _expect("မ သွား", 0, "part")
    _expect("မ များ", 1, "v")
    _expect("လူ များ", 1, "part")
    _expect("သွား သင့်", 1, "part")
    _expect("မ သင့်", 1, "v")
    _expect("မ သွား နှင့်", 2, "part")
    _expect("သွား နှင့် ပြီ", 1, "part")
    _expect("ဓား နှင့် ခုတ်", 1, "ppm")
    _expect("မောင်ဘ နှင့် မောင်လှ", 1, "conj")
    _expect("ဥပဒေ နှင့် အညီ", 1, "ppm")
    _expect("စာအုပ် ၏", 1, "ppm")
    _expect("ဆောင်ရွက် ၏", 1, "part")
    _expect("ရန်ကုန် တွင်", 1, "ppm")
    _expect("သူ က လာ", 1, "ppm")
    _expect("သွား က", 1, "conj")
    _expect("ဆောက် စေ", 1, "part")
    _expect("လုပ် ခိုင်း", 1, "part")
    _expect("ပွင့် သည်", 1, "part")
    _expect("စာအုပ် တွေ", 1, "part")
    _expect("မ ဟုတ် ဘူး", 2, "part")
    _expect("သွား လော့", 1, "part")
    _expect("ဒီ စာအုပ်", 0, "adj")
    _expect("ဒါ", 0, "pron")
    _expect("ပန်း သည် လှ သည်", 2, "v")
    _expect("လှ သော ပန်း", 0, "adj")
    _expect("လူ ကောင်း သည် စာ ဖတ် သည်", 1, "adj")
    _expect("လူ ကောင်း သည် စာ ဖတ် သည်", 2, "ppm")
    _expect("သူ သည်", 0, "pron")
    _expect("ဘာ လဲ", 0, "pron")
    _expect("ဘာ စာအုပ်", 0, "adj")
    _expect("ပထမ ဆု", 0, "adj")
    _expect("သင် သည် ကျောင်းသား ဖြစ် သည်", 0, "pron")
    _expect("စာ သင် သည်", 1, "v")
    _expect("သူ ဟာ လာ", 1, "ppm")
    _expect("သွား ဖို့", 1, "part")
    _expect("ကောင်းကောင်း သွား", 0, "adv")
    _expect("အိမ် ကောင်းကောင်း", 1, "adj")
    _expect("အပေါ် တွင်", 0, "n")
    _expect("နည်းနည်း စား", 0, "adv")
    table = load_table()
    for tokens, index in (("မ သီရိ", 0), ("ကို မင်း", 0), ("နောက်ဆုံး ရောက်", 0), ("တွင်", 0), ("ရေ ဘူး", 1)):
        got = decide_tokens(tokens.split(), table)[index]
        if got["status"] != "review":
            raise AssertionError(f"{tokens} [{index}] closed as {got['tag']} via {got['rule']}")
    hosted = decide_tokens("ရန်ကုန် တွင်".split(), table)[1]
    if hosted["left"] != "ရန်ကုန်" or hosted["right"] != "":
        raise AssertionError(hosted)
    review = decide_tokens("ကား ကောင်း".split(), table)
    if review[0]["status"] != "review" or not review[0]["readings"]:
        raise AssertionError(review[0])
    catalog = lookup_word("ကား", load_table())
    if catalog["status"] != "catalog" or len(catalog["readings"]) < 2:
        raise AssertionError(catalog)
    print("SELF-TEST PASSED: closed frames, review payload, and catalog lookup.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decide myPOS tags for one Burmese line.")
    parser.add_argument("--tokens", help="Whitespace-tokenized line")
    parser.add_argument("--text", help="Raw Burmese; segmented before tagging")
    parser.add_argument("--word", help="Show the catalog readings for one surface")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    table = load_table()
    if args.self_test:
        self_test()
        return
    if args.word:
        print(json.dumps(lookup_word(args.word, table), ensure_ascii=False, indent=2))
        return
    if args.tokens:
        tokens = args.tokens.split()
    elif args.text:
        sys.path.insert(0, str(ROOT / "scripts"))
        from word_segmenter import WordSegmenter

        tokens = WordSegmenter().segment(args.text)
    else:
        parser.error("give --tokens, --text, --word, or --self-test")
        return
    print(json.dumps({"tokens": tokens, "decisions": decide_tokens(tokens, table)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
