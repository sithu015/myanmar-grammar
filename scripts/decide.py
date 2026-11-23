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
import re
import sys
from pathlib import Path

try:
    from .common_standards import (
        ALLOWED_15_TAGS,
        CLASSIFIERS as STANDARD_CLASSIFIERS,
        PROFILES,
        SUBSECTION_CONSONANTS,
        TIME_MEASURE_NOUNS,
        TITLES_AND_RANKS,
        normalize_profile,
    )
except ImportError:
    _scripts_dir = str(Path(__file__).resolve().parent)
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)
    from common_standards import (
        ALLOWED_15_TAGS,
        CLASSIFIERS as STANDARD_CLASSIFIERS,
        PROFILES,
        SUBSECTION_CONSONANTS,
        TIME_MEASURE_NOUNS,
        TITLES_AND_RANKS,
        normalize_profile,
    )

ROOT = Path(__file__).resolve().parents[1]
_TABLE_TXT = ROOT / "resources" / "decisions" / "homographs.txt"
_TABLE_TSV = ROOT / "resources" / "decisions" / "homographs.tsv"
TABLE = _TABLE_TXT if _TABLE_TXT.exists() else _TABLE_TSV

PUNCT = set("။၊!?？！…-—–()[]{}「」『』\"'“”‘’,.:;/")
SYMBOLS = set("%$£¥#&@+=×÷λ")
CLASSIFIERS = set(STANDARD_CLASSIFIERS)
TEXTNUMS = {"တ", "တစ်", "နှစ်", "သုံး", "လေး", "ငါး", "ခြောက်", "ခုနစ်", "ရှစ်", "ကိုး", "ဆယ်", "ရာ", "ထောင်", "သိန်း", "သန်း", "သုည"}
TAGS = ALLOWED_15_TAGS
SUBSECTION = set(SUBSECTION_CONSONANTS)
_ASCII_NUM_RE = re.compile(r"^[0-9]+(?:[.,][0-9]+)*$")
_MY_NUM_RE = re.compile(r"^[၀-၉]+(?:[.,၊][၀-၉]+)*$")

ASPECT_VERBS = {
    "စီစဉ်", "ဆောင်ရွက်", "လျှောက်ထား", "စစ်ဆေး", "ဖော်ပြ", "ကျင်းပ", "တက်ရောက်",
    "ထုတ်ပြန်", "ချမှတ်", "ဆုံးဖြတ်", "ပြော", "လုပ်", "ရေးသား", "ဖတ်", "ကြည့်",
    "သိ", "ဆို", "ပေါ်ပေါက်", "ကျူးလွန်", "ရောက်", "ဖြစ်", "သွား", "လာ", "ပေး",
    "ထား", "ရှိ", "ဝင်", "ပြု", "လိုက်နာ", "ပြောဆို", "ကြား", "ရွေး", "ချယ်", "ခုတ်",
    "ဆောက်", "ကျ", "ချ", "ကျက်", "ချက်", "ပွင့်", "ဖွင့်", "ပျက်", "ဖျက်",
    "လွတ်", "လွှတ်", "မြင့်", "မြှင့်", "စား", "ကျွေး", "သေ", "သတ်", "စေ", "ခိုင်း",
    "တည်ထောင်", "တည်ဆောက်", "ကြိုးစား", "ပြဋ္ဌာန်း", "ထိန်းသိမ်း", "ဟုတ်",
    # Unambiguous causative_pairs verbs (excluding noun/num/part homographs)
    "ကျေ", "ကျိုး", "ချိုး", "ကျွတ်", "ချွတ်", "ကြွေ", "ခြွေ", "ကျဉ်း", "ချဉ်း",
    "ကြွင်း", "ခြွင်း", "ကွာ", "ခွာ", "ကြောက်", "စွတ်", "ဆွတ်", "စန့်", "ဆန့်",
    "စုတ်", "ဆုတ်", "ပေါက်", "ဖောက်", "ပေါ်", "ဖော်", "ပြေ", "ဖြေ", "ပြည့်", "ဖြည့်",
    "ပြတ်", "ဖြတ်", "ပြုတ်", "ဖြုတ်", "ပြန့်", "ဖြန့်", "ပဲ့", "ဖဲ့", "ပြို", "ဖြို",
    "မြုပ်", "မြှုပ်", "မျော", "မျှော", "နု", "နှု", "နိမ့်", "နှိမ့်", "ညွတ်", "ညှွတ်",
    "ညှိ", "လှဲ", "လန်", "လှန်", "လှည့်", "လှိမ့်", "လွင့်", "လွှင့်", "လျော့", "လျှော့",
    "သောက်", "အိပ်", "သိပ်", "မြင်", "ပြ", "ဝတ်",
    # High-frequency unambiguous corpus verbs
    "ဝယ်", "တိုးတက်", "ကူညီ", "ဝယ်ယူ", "နေထိုင်", "အသုံးပြု", "ပြုလုပ်", "ရရှိ",
    "တင်ပြ", "သတ်မှတ်", "ပြောကြား", "ဖွဲ့စည်း", "ရောင်းချ", "စတင်", "ထုတ်လုပ်",
    "ရယူ", "ပြောင်းလဲ", "တင်သွင်း", "ပြင်ဆင်", "ထုတ်ပေး", "သုံးစွဲ", "ထိခိုက်",
    "လက်ခံ", "ခံစား", "လုပ်ဆောင်", "ဝင်ရောက်", "အတည်ပြု", "ပေးအပ်", "ဖြစ်ပွား",
    "စိစစ်", "ကြေညာ", "ခန့်ခွဲ", "ကာကွယ်", "ကြီးကြပ်", "သေဆုံး", "စီရင်",
    "လွှဲပြောင်း", "ရှာဖွေ", "တောင်းဆို", "အရေးယူ", "တိုက်ခိုက်", "တွေ့", "မြင့်တက်",
    "ပိုင်ဆိုင်", "ပြသ", "ဖြစ်ပေါ်", "ပူးပေါင်း", "ဆွေးနွေး", "ကြိုးပမ်း", "စုံစမ်း",
    "ပျက်စီး", "တိုးမြှင့်", "ယှဉ်ပြိုင်", "ပေးပို့", "ညှိနှိုင်း", "ပြုပြင်",
}
VERBAL_CHAIN_AUX = {
    "ခဲ့", "ပြီး", "နိုင်", "ရ", "စေ", "သင့်", "လိုက်", "နေ", "ပေး", "ထား",
    "သွား", "လာ", "ပါ", "ကြ", "မိ", "ချင်", "တတ်", "ထိုက်", "အပ်", "ပိုင်",
    "ဖူး", "ပြန်", "ဦး", "လိမ့်", "တော့",
}
UNAMBIGUOUS_NONINITIAL_VERBAL = {
    "ခဲ့", "ပြီး", "စေ", "သင့်", "လိုက်", "နိုင်", "ရ", "ကြ", "လိမ့်",
}
NEGATABLE = ASPECT_VERBS | {
    "ဟုတ်", "ကောင်း", "မှား", "မှန်", "သင့်", "ရ", "နိုင်", "စေ", "ပြီး", "နေ",
    "ခဲ့", "လိုက်", "များ", "လှ", "ကြီး",
}
_KNOWN_NOMINALS = (
    CLASSIFIERS
    | set(TIME_MEASURE_NOUNS)
    | set(TITLES_AND_RANKS)
    | {
        "ဤ", "ထို", "ယင်း", "၎င်း", "ဒါ", "အဲဒါ", "ဟို", "ဒီ", "ဟိုဟာ",
        "ဤအရာ", "ထိုအရာ", "အဘယ်အရာ", "တစ်စုံတစ်ရာ", "တစုံတရာ",
        "သူ", "သင်", "ငါ", "ကျွန်တော်", "ကျွန်မ", "ကျွန်ုပ်", "ကျုပ်",
        "ခင်ဗျား", "ဘယ်သူ", "မည်သူ", "အဘယ်သူ", "မိမိ", "ကိုယ်",
        "တရားလို", "တရားခံ", "တရားသူကြီး", "ဥပဒေ", "ပုဒ်မ",
        "အစိုးရ", "ပြည်သူ", "နိုင်ငံ", "နိုင်ငံတော်", "လူ", "ကုမ္ပဏီ",
        "ကော်မတီ", "ကော်မရှင်", "အဖွဲ့", "ဌာန", "ရုံး",
    }
)
_NOMINAL_SUFFIXES = (
    "သူ", "သား", "သမီး", "ရေး", "မှု", "ခြင်း", "ခွင့်", "ချက်",
    "တော်", "ဌာန", "ရုံး", "နိုင်ငံ", "အဖွဲ့", "ကောင်စီ", "ကော်မရှင်",
    "ကော်မတီ", "ဥပဒေ", "ပုဒ်မ", "စနစ်", "ပစ္စည်း", "ပုဂ္ဂိုလ်", "အစိုးရ",
    "ကုမ္ပဏီ", "တက္ကသိုလ်", "ကျောင်း", "ဆေးရုံ", "မြို့", "ရွာ", "ပြည်နယ်",
)
_LEGACY_VERBAL_FIN_RULES = frozenset(
    {
        "I_REALIS_LEGACY",
        "THI_FINAL_LEGACY",
        "THI_BEFORE_QUOT_LEGACY",
        "THI_AFTER_VERB_LEGACY",
        "MYI_FINAL_LEGACY",
        "MYI_BEFORE_QUOT_LEGACY",
        "PART_MYI_FINAL_LEGACY",
        "PART_TEH_LEGACY",
        "PART_MEH_LEGACY",
    }
)


def load_table(path: Path = TABLE) -> dict[str, list[dict[str, str]]]:
    table: dict[str, list[dict[str, str]]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        cols = line.split("\t")
        if len(cols) == 5:
            surface, when, tag, rule, note = cols
            profiles = "*"
        elif len(cols) == 6:
            surface, when, tag, rule, note, profiles = cols
        else:
            raise ValueError(f"bad column count ({len(cols)}) on {line!r}")
        if tag not in TAGS:
            raise ValueError(f"bad tag {tag} on {surface}")
        table.setdefault(surface, []).append(
            {
                "when": when,
                "tag": tag,
                "rule": rule,
                "note": note,
                "profiles": profiles.strip() or "*",
            }
        )
    return table


def _row_matches_profile(row_profiles: str, profile: str) -> bool:
    if not row_profiles or row_profiles == "*":
        return True
    parts = [p.strip() for p in row_profiles.split(",") if p.strip()]
    excludes = {p[1:] for p in parts if p.startswith("!")}
    if profile in excludes:
        return False
    includes = {p for p in parts if not p.startswith("!")}
    if includes:
        return profile in includes
    return True


def _is_number(token: str) -> bool:
    if not token:
        return False
    return bool(_ASCII_NUM_RE.match(token) or _MY_NUM_RE.match(token))


def _clause(
    clause: str,
    prev: str,
    nxt: str,
    prev2: str,
    nxt2: str = "",
    *,
    prev_is_verb: bool | None = None,
    prev_is_nominal: bool | None = None,
) -> bool:
    clause = clause.strip()
    if clause.startswith("!"):
        return not _clause(
            clause[1:],
            prev,
            nxt,
            prev2,
            nxt2,
            prev_is_verb=prev_is_verb,
            prev_is_nominal=prev_is_nominal,
        )
    if prev_is_verb is None:
        prev_is_verb = prev in ASPECT_VERBS
    if prev_is_nominal is None:
        prev_is_nominal = (
            prev != ""
            and prev not in ASPECT_VERBS
            and prev not in VERBAL_CHAIN_AUX
            and prev not in PUNCT
            and (
                prev in _KNOWN_NOMINALS
                or any(prev.endswith(suf) and len(prev) > len(suf) for suf in _NOMINAL_SUFFIXES)
            )
        )
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
    if clause == "next_textnum":
        return nxt in TEXTNUMS or _is_number(nxt)
    if clause == "between_num":
        return (_is_number(prev) or prev in TEXTNUMS) and (_is_number(nxt) or nxt in TEXTNUMS)
    if clause == "after_word":
        return prev != "" and prev not in PUNCT
    if clause == "prev_verb":
        return prev_is_verb
    if clause == "prev_nominal":
        return prev_is_nominal
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


def matches(
    when: str,
    prev: str,
    nxt: str,
    prev2: str,
    nxt2: str = "",
    *,
    prev_is_verb: bool | None = None,
    prev_is_nominal: bool | None = None,
) -> bool:
    if when.startswith("all:"):
        return all(
            _clause(
                part.strip(),
                prev,
                nxt,
                prev2,
                nxt2,
                prev_is_verb=prev_is_verb,
                prev_is_nominal=prev_is_nominal,
            )
            for part in when[4:].split("&")
        )
    return _clause(
        when,
        prev,
        nxt,
        prev2,
        nxt2,
        prev_is_verb=prev_is_verb,
        prev_is_nominal=prev_is_nominal,
    )


def _script_token(token: str) -> dict[str, object] | None:
    if not token:
        return None
    if all(ch in PUNCT for ch in token):
        return {"tag": "punc", "rule": "CHAR_PUNC", "status": "closed", "note": "punctuation"}
    if token in SYMBOLS or all(ch in SYMBOLS for ch in token):
        return {"tag": "sb", "rule": "CHAR_SYMBOL", "status": "closed", "note": "symbol"}
    if _MY_NUM_RE.match(token):
        return {"tag": "num", "rule": "CHAR_MYDIGIT", "status": "closed", "note": "Myanmar digits"}
    if _ASCII_NUM_RE.match(token):
        return {"tag": "num", "rule": "CHAR_ASCIIDIGIT", "status": "closed", "note": "ASCII digits"}
    if token.isascii() and any(ch.isalpha() for ch in token):
        return {"tag": "fw", "rule": "CHAR_LATIN", "status": "closed", "note": "Latin word; Myanmar loans stay n"}
    return None


def decide_tokens(
    tokens: list[str],
    table: dict[str, list[dict[str, str]]],
    profile: str = "general",
) -> list[dict[str, object]]:
    profile = normalize_profile(profile, default="general")
    out: list[dict[str, object]] = []
    verbal_chain: list[bool] = []

    def stamp(payload: dict[str, object], prev: str, nxt: str) -> None:
        payload["left"] = prev
        payload["right"] = nxt
        out.append(payload)

    for i, token in enumerate(tokens):
        prev = tokens[i - 1] if i else ""
        prev2 = tokens[i - 2] if i > 1 else ""
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        nxt2 = tokens[i + 2] if i + 2 < len(tokens) else ""
        prev_is_verb = i > 0 and (
            prev in ASPECT_VERBS
            or verbal_chain[i - 1]
            or (
                prev in UNAMBIGUOUS_NONINITIAL_VERBAL
                and i > 1
                and prev2 not in PUNCT
                and out[i - 1]["tag"] in (None, "v", "part")
            )
        )
        prev_is_nominal = i > 0 and (
            out[i - 1]["tag"] in {"n", "pron", "num", "tn", "abb", "fw"}
            or (
                prev not in ASPECT_VERBS
                and prev not in VERBAL_CHAIN_AUX
                and prev not in PUNCT
                and (
                    prev in _KNOWN_NOMINALS
                    or any(prev.endswith(suf) and len(prev) > len(suf) for suf in _NOMINAL_SUFFIXES)
                )
            )
        )

        if token in SUBSECTION and prev in "([" and nxt in ")]":
            stamp({
                "i": i, "w": token, "tag": "sb", "rule": "SUBSECTION_SB",
                "status": "closed", "note": "parenthetical subsection letter, not a word",
                "readings": [],
            }, prev, nxt)
            verbal_chain.append(False)
            continue

        scripted = _script_token(token)
        if scripted is not None:
            stamp({"i": i, "w": token, **scripted, "readings": []}, prev, nxt)
            verbal_chain.append(False)
            continue

        rows = [
            row for row in table.get(token, [])
            if _row_matches_profile(row.get("profiles", "*"), profile)
        ]
        hit = None
        for row in rows:
            if matches(
                row["when"],
                prev,
                nxt,
                prev2,
                nxt2,
                prev_is_verb=prev_is_verb,
                prev_is_nominal=prev_is_nominal,
            ):
                hit = row
                break
        readings = [
            {"tag": row["tag"], "when": row["when"], "rule": row["rule"], "note": row["note"]}
            for row in rows
            if row["when"] == "reading" or hit is None
        ]
        if hit is not None:
            resolved_tag = hit["tag"]
            stamp(
                {
                    "i": i,
                    "w": token,
                    "tag": resolved_tag,
                    "rule": hit["rule"],
                    "status": "closed",
                    "note": hit["note"],
                    "readings": [r for r in readings if r["rule"] != hit["rule"]],
                },
                prev,
                nxt,
            )
        elif rows:
            resolved_tag = None
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
            resolved_tag = None
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
        is_verbal_here = (
            resolved_tag == "v"
            or (token in ASPECT_VERBS and resolved_tag is None)
            or (resolved_tag == "part" and token in VERBAL_CHAIN_AUX and prev_is_verb)
        )
        verbal_chain.append(is_verbal_here)
    return out


def lookup_word(
    word: str,
    table: dict[str, list[dict[str, str]]],
    profile: str = "general",
) -> dict[str, object]:
    profile = normalize_profile(profile, default="general")
    rows = [
        row for row in table.get(word, [])
        if _row_matches_profile(row.get("profiles", "*"), profile)
    ]
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
    _expect("တည်ထောင် ရန်", 1, "conj")
    _expect("ခန့်မှန်းချက် ထက် ပိုမို", 1, "ppm")
    _expect("ယင်း ဥပဒေ", 0, "adj")
    _expect("ယင်း သည်", 0, "pron")
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
    parser.add_argument(
        "--profile",
        choices=list(PROFILES),
        default="general",
        help="Workflow profile (general, legal70k, news_unified, legacy_mypos_alt)",
    )
    parser.add_argument("--hd", action="store_true", help="Also emit myPOS-HD / UPOS projection for closed tags")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    profile = normalize_profile(args.profile, default="general")
    table = load_table()
    if args.self_test:
        self_test()
        return
    if args.word:
        print(json.dumps(lookup_word(args.word, table, profile=profile), ensure_ascii=False, indent=2))
        return
    if args.tokens:
        tokens = args.tokens.split()
    elif args.text:
        sys.path.insert(0, str(ROOT / "scripts"))
        from word_segmenter import WordSegmenter

        tokens = WordSegmenter(profile=profile).segment(args.text)
    else:
        parser.error("give --tokens, --text, --word, or --self-test")
        return
    decisions = decide_tokens(tokens, table, profile=profile)
    payload: dict[str, object] = {"tokens": tokens, "decisions": decisions}
    if args.hd:
        sys.path.insert(0, str(ROOT / "scripts"))
        from project_mypos_hd import project_sentence_to_mypos_hd

        base_pairs = [(str(d["w"]), str(d["tag"] or "open")) for d in decisions]
        hd_profile = "legacy_mypos_alt" if profile == "legacy_mypos_alt" else "unified_modern"
        hd_rows = project_sentence_to_mypos_hd(base_pairs, profile=hd_profile)
        for d, row in zip(decisions, hd_rows):
            if d["tag"] is None:
                row["mypos15"] = "open"
                row["mypos_hd"] = "open"
                row["mypos_core"] = "open"
            elif (
                profile == "legacy_mypos_alt"
                and d.get("rule") in _LEGACY_VERBAL_FIN_RULES
                and row["mypos15"] == "ppm"
            ):
                row["mypos_hd"] = "ppm:fin"
                row["mypos_core"] = "sfp"
                row["upos"] = "PART"
                row["feats"] = "Mood=Ind"
        payload["mypos_hd"] = hd_rows
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
