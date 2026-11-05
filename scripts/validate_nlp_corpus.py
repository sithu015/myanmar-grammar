#!/usr/bin/env python3
"""
Myanmar Grammar & NLP Corpus Validator (validate_nlp_corpus.py)

Validates Myanmar Word Segmentation (WS), POS-tagged lines (word/tag),
TSV token tables, and bracketed compound research layers ([w1/p1 | w2/p2]/p_outer)
against Myanmar Language Commission (MLC) orthography and Legal70k / myPOS v3.0
owner standards.

Usage:
  python3 scripts/validate_nlp_corpus.py --input <file> [--reference <orig_file>] [--mode ws|pos|bracket] [--json]
  python3 scripts/validate_nlp_corpus.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

# 15 allowed lowercase myPOS / Legal70k tags
ALLOWED_15_TAGS: frozenset[str] = frozenset(
    {
        "abb",
        "adj",
        "adv",
        "conj",
        "fw",
        "int",
        "n",
        "num",
        "part",
        "ppm",
        "pron",
        "punc",
        "sb",
        "tn",
        "v",
    }
)

# 15 allowed canonical NER classes (ner-mya-v2)
ALLOWED_15_NER_CLASSES: frozenset[str] = frozenset(
    {
        "GPE",
        "LOC",
        "ORG",
        "PER",
        "DATE",
        "TIME",
        "NUM",
        "MONEY",
        "TERM",
        "EVENT",
        "PRODUCT",
        "FACILITY",
        "NORP",
        "DISEASE_PHENOMENON",
        "MISC",
    }
)

# Common clitics that must never bleed into NER spans (Zero-Clitic Invariant)
COMMON_NER_CLITICS: frozenset[str] = frozenset(
    {"သည်", "က", "ကို", "အား", "၌", "တွင်", "မှ", "သို့", "၏", "ရဲ့", "ဖြင့်", "နှင့်", "နဲ့", "အတွက်", "ကြောင့်"}
)

# Protected foreign, geographical, and institutional proper names ending in characters like 'က' or 'ကို'
PROTECTED_LEXEMES_ENDING_IN_CLITIC_CHARS: frozenset[str] = frozenset(
    {
        "မက္ကဆီကို",
        "မိုနာကို",
        "မော်ရိုကို",
        "မော်စကို",
        "တိုကျို",
        "ဆန်ဖရန်စစ္စကို",
        "အက်သလက်တီကို",
        "တက်ဒက်စ်ကို",
        "ဇီကို",
        "အမ်ဘိုကို",
        "မဘိုကို",
        "အာဖရိက",
        "တောင်အာဖရိက",
        "မြောက်အမေရိက",
        "လက်တင်အမေရိက",
        "အမေရိက",
        "အန္တာတိက",
        "ပုဂ္ဂလိက",
        "ကော့စတာရီကာ",
        "သီရိလင်္ကာ",
        "ဒါကာ",
        "ကာတာ",
        "ပုဂ္ဂိုလ်",
        "ကုမ္ပဏီ",
        "အစိုးရ",
        "အိုနိုပရီယန်ကို",
        "ဆဲကို",
        "နီကို",
        "ဖရန်ကို",
        "ဒါ့စ်ကို",
        "မာကို",
    }
)

# Known titles, ranks, and status honors that must be tagged 'O', never inside 'PER'
TITLES_AND_RANKS: frozenset[str] = frozenset(
    {
        "သမ္မတ", "ဝန်ကြီး", "ဝန်ကြီးချုပ်", "ဒုတိယသမ္မတ", "ဒုတိယဝန်ကြီး",
        "ဗိုလ်ချုပ်", "ဗိုလ်ချုပ်ကြီး", "ဒုတိယဗိုလ်ချုပ်ကြီး", "ဗိုလ်မှူးချုပ်",
        "ဗိုလ်မှူးကြီး", "ဗိုလ်မှူး", "ဗိုလ်ကြီး", "ဗိုလ်", "စစ်ဗိုလ်ချုပ်",
        "စော်ဘွား", "စော်ဘွားကြီး", "သံအမတ်", "သံအမတ်ကြီး", "ဒေါက်တာ",
        "ပုပ်ရဟန်းမင်းကြီး", "ဥက္ကဋ္ဌ"
    }
)

# 11 Owner fixed-tag exact archaic/standard surfaces (2026-10-26 ruling)
OWNER_FIXED_TAG_SURFACES: dict[str, str] = {
    "တမျိုးတည်း": "adj",
    "တဖက်သတ်": "adv",
    "တဆက်တည်း": "adv",
    "တဦးတည်းပိုင်": "adj",
    "တချိန်တည်း": "adv",
    "တပြိုင်နက်": "adv",
    "တခါတရံ": "adv",
    "အခါတမျိုးမျိုး": "adv",
    "တချက်လွှတ်": "adj",
    "တကျွန်းပို့ဒဏ်": "n",
    "တသီးတခြား": "adv",
}

# 10 Owner component-standard rows (complete lexical surfaces -> flat POS tokens)
OWNER_COMPONENT_STANDARDS: dict[str, list[tuple[str, str]]] = {
    "မြန်မာနိုင်ငံ": [("မြန်မာ", "n"), ("နိုင်ငံ", "n")],
    "မြန်မာနိုင်ငံတော်": [("မြန်မာ", "n"), ("နိုင်ငံတော်", "n")],
    "ပြည်ထောင်စုအစိုးရ": [("ပြည်ထောင်စု", "n"), ("အစိုးရ", "n")],
    "အစိုးရအဖွဲ့": [("အစိုးရ", "n"), ("အဖွဲ့", "n")],
    "အစိုးရအဖွဲ့ဝင်": [("အစိုးရ", "n"), ("အဖွဲ့ဝင်", "n")],
    "ပြည်နယ်အစိုးရ": [("ပြည်နယ်", "n"), ("အစိုးရ", "n")],
    "ပြည်နယ်အစိုးရအဖွဲ့": [("ပြည်နယ်", "n"), ("အစိုးရ", "n"), ("အဖွဲ့", "n")],
    "အာဏာပိုင်နက်": [("အာဏာ", "n"), ("ပိုင်နက်", "n")],
    "ဝန်ကြီးရုံး": [("ဝန်ကြီး", "n"), ("ရုံး", "n")],
    "ဘာသာသာသနာ": [("ဘာသာ", "n"), ("သာသနာ", "n")],
    "စီးပွားရေးစနစ်": [("စီးပွားရေး", "n"), ("စနစ်", "n")],
    "သယံဇာတပစ္စည်း": [("သယံဇာတ", "n"), ("ပစ္စည်း", "n")],
    "ရေပေါ်ရေအောက်": [("ရေပေါ်", "n"), ("ရေအောက်", "n")],
    "မြေပေါ်မြေအောက်": [("မြေပေါ်", "n"), ("မြေအောက်", "n")],
}

# Dependent signs / combining marks that can NEVER start a valid Myanmar word token
ILLEGAL_WORD_START_CHARS: frozenset[str] = frozenset(
    chr(c) for c in list(range(0x102B, 0x103F)) + list(range(0x1056, 0x105A))
)

# Common Zawgyi-only codepoints/sequences for quick contamination check
# Note: In Unicode, \u1031 after a consonant/medial followed by the next syllable's consonant (e.g. နေထိုင်) is valid;
# Zawgyi visual-order \u1031 occurs at token start or after a tone/asat/punctuation before a consonant.
ZAWGYI_INDICATORS: re.Pattern[str] = re.compile(
    r"[\u1033\u1034\u105a\u1060-\u1097]|(?:(?:^|[\s\u1037\u1038\u103a\u104a\u104b])\u1031[\u1000-\u1021])"
)

# Bracketed compound pattern: [w1/p1 | w2/p2]/outer_pos
BRACKET_COMPOUND_RE: re.Pattern[str] = re.compile(
    r"\[([^\[\]]+?)\]/([a-z]+)"
)


def strip_ws(text: str) -> str:
    """Remove all whitespace characters and normalize standard orthographic typos for exact conservation checks."""
    t = re.sub(r"\s+", "", text)
    t = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]", "", t)
    t = t.replace("စျ", "ဈ").replace("ဦး", "ဦး")
    t = t.replace("\u103a\u1037", "\u1037\u103a")
    return t


def parse_pos_token(token: str) -> tuple[str, str] | None:
    """Parse a flat 'word/tag' token using the last unescaped '/' delimiter."""
    idx = token.rfind("/")
    if idx <= 0 or idx == len(token) - 1:
        return None
    # Support literal backslash '\/tag' and escaped backslash '\\/tag'
    if token[:idx] in ("\\", "\\\\"):
        tag = token[idx + 1 :]
        return "\\", tag
    # Check if the slash was escaped by an odd number of backslashes
    j = idx - 1
    bs_count = 0
    while j >= 0 and token[j] == "\\":
        bs_count += 1
        j -= 1
    if bs_count % 2 == 1:
        return None
    surface = token[:idx].replace("\\\\", "\\").replace("\\/", "/")
    tag = token[idx + 1 :]
    return surface, tag


def flatten_bracket_line(line: str) -> tuple[str, list[str]]:
    """
    Convert a bracket-annotated compound research line into a flat POS line,
    verifying that outer tags are not emitted as extra tokens and inner components
    reconstruct the exact surface characters.
    """
    errors: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        outer_tag = match.group(2).strip()
        if outer_tag not in ALLOWED_15_TAGS:
            errors.append(f"Invalid outer compound tag '{outer_tag}' in '{match.group(0)}'")
        parts = [p.strip() for p in inner.split("|")]
        if len(parts) < 2:
            errors.append(f"Bracket group '{match.group(0)}' has fewer than 2 components")
        flat_tokens: list[str] = []
        for part in parts:
            parsed = parse_pos_token(part)
            if not parsed:
                errors.append(f"Malformed component '{part}' in '{match.group(0)}'")
                flat_tokens.append(part)
            else:
                surf, tag = parsed
                if tag not in ALLOWED_15_TAGS:
                    errors.append(f"Invalid component tag '{tag}' on '{surf}'")
                flat_tokens.append(f"{surf}/{tag}")
        return " ".join(flat_tokens)

    flattened = BRACKET_COMPOUND_RE.sub(_replace, line)
    return flattened, errors


def scan_token_consistency(
    input_lines: list[str],
    mode: str = "ws",
) -> list[dict[str, Any]]:
    """
    Scan all lines for intra-corpus token-level segmentation inconsistency.
    Reports tokens that appear both merged and split across lines.
    Only meaningful for ws mode (surface form comparison).
    """
    from collections import defaultdict

    # Map: surface_chars (no whitespace) -> set of observed segmented forms
    form_map: dict[str, set[str]] = defaultdict(set)

    for line in input_lines:
        clean = line.rstrip("\r\n")
        if mode == "pos":
            tokens = [parse_pos_token(t) for t in clean.split()]
            surfaces = [s for s, _ in tokens if s]
        else:
            surfaces = clean.split()

        # Build sliding window of 2–4 adjacent tokens to detect merge candidates
        for window_size in (2, 3, 4):
            for i in range(len(surfaces) - window_size + 1):
                window = surfaces[i : i + window_size]
                merged_key = "".join(window)
                form_map[merged_key].add(" ".join(window))

        # Also register each single token
        for surf in surfaces:
            no_ws = strip_ws(surf)
            if no_ws:
                form_map[no_ws].add(surf)

    issues: list[dict[str, Any]] = []
    for chars, forms in form_map.items():
        if len(forms) > 1:
            issues.append(
                {
                    "type": "segmentation_inconsistency",
                    "surface_chars": chars,
                    "observed_forms": sorted(forms),
                    "message": (
                        f"Surface '{chars}' appears in {len(forms)} different segmented forms: "
                        + " | ".join(f'"{f}"' for f in sorted(forms))
                    ),
                }
            )
    return issues


def audit_line(
    line: str,
    line_no: int,
    mode: str = "ws",
    ref_line: str | None = None,
) -> list[dict[str, Any]]:
    """Audit a single line for orthographic fidelity, Unicode/dependent signs, and POS rules."""
    issues: list[dict[str, Any]] = []
    clean_line = line.rstrip("\r\n")

    # 1. NFC check
    if not unicodedata.is_normalized("NFC", clean_line):
        issues.append(
            {
                "line": line_no,
                "type": "non_nfc",
                "message": "Line is not in Unicode NFC canonical form.",
            }
        )

    # 2. Zawgyi indicator check
    if ZAWGYI_INDICATORS.search(clean_line):
        issues.append(
            {
                "line": line_no,
                "type": "possible_zawgyi",
                "message": "Line contains codepoints or sequences strongly indicative of Zawgyi encoding.",
            }
        )

    working_line = clean_line
    if mode == "bracket":
        working_line, bracket_errors = flatten_bracket_line(clean_line)
        for b_err in bracket_errors:
            issues.append(
                {
                    "line": line_no,
                    "type": "bracket_syntax_error",
                    "message": b_err,
                }
            )

    tokens = working_line.split()
    surfaces: list[str] = []
    parsed_pairs: list[tuple[str, str]] = []

    for tok_idx, tok in enumerate(tokens, start=1):
        if mode in ("pos", "bracket"):
            parsed = parse_pos_token(tok)
            if not parsed:
                issues.append(
                    {
                        "line": line_no,
                        "token_index": tok_idx,
                        "type": "missing_pos_tag",
                        "message": f"Token '{tok}' is missing a valid '/tag' suffix.",
                    }
                )
                surf = tok
                tag = ""
            else:
                surf, tag = parsed
                if tag not in ALLOWED_15_TAGS:
                    issues.append(
                        {
                            "line": line_no,
                            "token_index": tok_idx,
                            "type": "invalid_pos_tag",
                            "message": f"Tag '{tag}' on '{surf}' is outside the 15-tag vocabulary.",
                        }
                    )
                if tag == "fw" and re.search(r"[\u1000-\u109F]", surf):
                    issues.append(
                        {
                            "line": line_no,
                            "token_index": tok_idx,
                            "type": "burmese_script_tagged_fw",
                            "message": f"Burmese script token '{surf}' must not be tagged as 'fw'.",
                        }
                    )
                if surf in OWNER_FIXED_TAG_SURFACES:
                    expected_tag = OWNER_FIXED_TAG_SURFACES[surf]
                    if tag != expected_tag:
                        issues.append(
                            {
                                "line": line_no,
                                "token_index": tok_idx,
                                "type": "owner_fixed_tag_violation",
                                "message": (
                                    f"Exact surface '{surf}' has tag '{tag}', "
                                    f"expected owner fixed tag '{expected_tag}'."
                                ),
                            }
                        )
                if surf in OWNER_COMPONENT_STANDARDS:
                    expected_flat = " ".join(
                        f"{w}/{t}" for w, t in OWNER_COMPONENT_STANDARDS[surf]
                    )
                    issues.append(
                        {
                            "line": line_no,
                            "token_index": tok_idx,
                            "type": "unsplit_component_standard",
                            "message": (
                                f"Surface '{surf}' should be split per 10-row component standard "
                                f"into '{expected_flat}'."
                            ),
                        }
                    )
            parsed_pairs.append((surf, tag))
        else:
            surf = tok
            if surf in OWNER_COMPONENT_STANDARDS:
                expected_ws = " ".join(w for w, _ in OWNER_COMPONENT_STANDARDS[surf])
                issues.append(
                    {
                        "line": line_no,
                        "token_index": tok_idx,
                        "type": "unsplit_component_standard",
                        "message": (
                            f"Surface '{surf}' should be split per 10-row component standard "
                            f"into '{expected_ws}'."
                        ),
                    }
                )

        # Check for title/rank unsplit from personal names (Title must be split: e.g. ဗိုလ်ချုပ် အောင်ဆန်း, ဗိုလ်ကြီး ဇင်ယော်)
        KNOWN_TITLES_TO_SPLIT = ("ဗိုလ်ချုပ်", "ဗိုလ်ကြီး", "ဗိုလ်မှူး", "စော်ဘွားကြီး", "သံအမတ်ကြီး", "ဒေါက်တာ")
        KNOWN_NAMES_AFTER_TITLE = ("အောင်ဆန်း", "ဇင်ယော်", "စောမုတ်သုန်", "စဝ်စံထွန်း", "တေဇာဆန်း")
        for title in KNOWN_TITLES_TO_SPLIT:
            if surf.startswith(title) and len(surf) > len(title):
                rem = surf[len(title):]
                if rem in KNOWN_NAMES_AFTER_TITLE:
                    issues.append(
                        {
                            "line": line_no,
                            "token_index": tok_idx,
                            "type": "unsplit_title_name",
                            "message": (
                                f"Title/Rank '{title}' must be split from personal name '{rem}' "
                                f"into '{title}/{'n' if mode in ('pos', 'bracket') else ''} {rem}/{'n' if mode in ('pos', 'bracket') else ''}'."
                            ),
                        }
                    )

        surfaces.append(surf)

        # Check illegal word-initial dependent signs
        if surf and surf[0] in ILLEGAL_WORD_START_CHARS:
            issues.append(
                {
                    "line": line_no,
                    "token_index": tok_idx,
                    "type": "illegal_word_start_dependent_sign",
                    "message": (
                        f"Token '{surf}' begins with dependent sign U+{ord(surf[0]):04X}; "
                        "indicates shattered syllable or broken boundary."
                    ),
                }
            )

        # Check space-broken kinzi tail (\u1004\u103A\u1039 at end of token)
        if surf.endswith("\u1004\u103a\u1039") or surf.endswith("\u1039"):
            issues.append(
                {
                    "line": line_no,
                    "token_index": tok_idx,
                    "type": "dangling_virama_or_kinzi",
                    "message": (
                        f"Token '{surf}' ends with a dangling virama/kinzi (U+1039); "
                        "stacked consonant was split across a space."
                    ),
                }
            )

    # Word segmentation checks for WS mode
    if mode == "ws" and surfaces:
        n_surfs = len(surfaces)
        for i, surf in enumerate(surfaces):
            prv_s = surfaces[i - 1] if i > 0 else ""
            nxt_s = surfaces[i + 1] if i + 1 < n_surfs else ""
            if surf.endswith("ပေါင်း") and (nxt_s == "များစွာ" or (nxt_s == "များ" and i + 2 < n_surfs and surfaces[i + 2] == "စွာ")):
                issues.append(
                    {
                        "line": line_no,
                        "token_index": i + 1,
                        "type": "split_paung_myarswar_violation",
                        "message": (
                            f"Indefinite multiplier compound '{surf} {nxt_s}' must not be split. "
                            f"Unify into '{surf}များစွာ'."
                        ),
                    }
                )
            if surf == "ပေါင်း" and prv_s and nxt_s and re.search(r"[\d၀-၉]", nxt_s):
                if prv_s not in ("စုစု", "ဓာတ်", "တပ်"):
                    issues.append(
                        {
                            "line": line_no,
                            "token_index": i + 1,
                            "type": "split_noun_paung_numeral_violation",
                            "message": (
                                f"Counting compound '{prv_s} {surf} {nxt_s}' must not split '{surf}'. "
                                f"Unify into '{prv_s}ပေါင်း {nxt_s}'."
                            ),
                        }
                    )

    # Contextual POS pattern checks (ဆိုသည်မှာ, post-verbal ရာ, quotative ဟု/ဟူ၍/ဟူသော/ဟူသည်)
    if mode in ("pos", "bracket") and parsed_pairs:
        n_pairs = len(parsed_pairs)
        for i, (surf, tag) in enumerate(parsed_pairs):
            prv_w, prv_t = parsed_pairs[i - 1] if i > 0 else ("", "")
            nxt_w, nxt_t = parsed_pairs[i + 1] if i + 1 < n_pairs else ("", "")

            if surf == "သည်" and prv_w == "ဆို" and prv_t == "v" and tag != "part":
                issues.append(
                    {
                        "line": line_no,
                        "token_index": i + 1,
                        "type": "so_thi_pos_violation",
                        "message": f"Nominalizer 'သည်' after 'ဆို/v' must be 'part', got '{tag}'.",
                    }
                )
            if surf == "မှာ" and prv_w == "သည်" and i >= 2 and parsed_pairs[i - 2][0] == "ဆို" and tag != "ppm":
                issues.append(
                    {
                        "line": line_no,
                        "token_index": i + 1,
                        "type": "so_thi_hma_pos_violation",
                        "message": f"Topic marker 'မှာ' in 'ဆို သည် မှာ' must be 'ppm', got '{tag}'.",
                    }
                )
            if surf == "ရာ" and tag in ("v", "n") and prv_t in ("v", "part"):
                issues.append(
                    {
                        "line": line_no,
                        "token_index": i + 1,
                        "type": "post_verbal_yar_pos_violation",
                        "message": (
                            f"Post-verbal 'ရာ' after '{prv_w}/{prv_t}' must be 'part' "
                            f"(not '{tag}')."
                        ),
                    }
                )
            if surf in ("ဟု", "ဟူ၍", "ဟူသော", "ဟူသည်") and tag != "part":
                issues.append(
                    {
                        "line": line_no,
                        "token_index": i + 1,
                        "type": "quotative_pos_violation",
                        "message": f"Quotative particle '{surf}' must be 'part', got '{tag}'.",
                    }
                )

            # Check for prohibited split personal name prefix (Name prefixes must NOT be split from the name)
            KNOWN_NAME_PREFIXES = ("ဦး", "ဒေါ်", "စဝ်", "စော", "နော်", "ဆလိုင်း")
            KNOWN_NAMES_WITH_PREFIX = ("မင်းအောင်လှိုင်", "အောင်ဆန်းစုကြည်", "ကျော်မိုးထွန်း", "စံထွန်း", "မုတ်သုန်")
            if surf in KNOWN_NAME_PREFIXES and nxt_w in KNOWN_NAMES_WITH_PREFIX:
                if prv_t not in ("num", "tn") and prv_w not in ("တစ်", "နှစ်", "သုံး", "လေး", "ငါး", "အချို့", "အနည်းဆုံး", "အများဆုံး", "စုစုပေါင်း"):
                    issues.append(
                        {
                            "line": line_no,
                            "token_index": i + 1,
                            "type": "split_name_prefix_violation",
                            "message": (
                                f"Personal name prefix '{surf}' must not be split from '{nxt_w}'. "
                                f"Unify into '{surf}{nxt_w}/n'."
                            ),
                        }
                    )

            # Check for prohibited split of -ပေါင်းများစွာ (Indefinite multiplier compounds must be 1 token)
            if surf.endswith("ပေါင်း") and (nxt_w == "များစွာ" or (nxt_w == "များ" and i + 2 < n_pairs and parsed_pairs[i + 2][0] == "စွာ")):
                issues.append(
                    {
                        "line": line_no,
                        "token_index": i + 1,
                        "type": "split_paung_myarswar_violation",
                        "message": (
                            f"Indefinite multiplier compound '{surf} {nxt_w}' must not be split. "
                            f"Unify into '{surf}များစွာ'."
                        ),
                    }
                )

            # Check for prohibited split of [Noun] + ပေါင်း + Numeral
            if surf == "ပေါင်း" and prv_w and nxt_w and (nxt_t in ("num", "tn") or re.search(r"[\d၀-၉]", nxt_w)):
                if prv_t in ("n", "fw") and prv_w not in ("စုစု", "ဓာတ်", "တပ်"):
                    issues.append(
                        {
                            "line": line_no,
                            "token_index": i + 1,
                            "type": "split_noun_paung_numeral_violation",
                            "message": (
                                f"Counting compound '{prv_w} {surf} {nxt_w}' must not split '{surf}'. "
                                f"Unify into '{prv_w}ပေါင်း/n {nxt_w}/{nxt_t}'."
                            ),
                        }
                    )

    # 3. Non-whitespace character conservation against reference line
    if ref_line is not None:
        ref_clean = ref_line.rstrip("\r\n")
        reconstructed = strip_ws("".join(surfaces))
        expected_chars = strip_ws(ref_clean)
        if reconstructed != expected_chars:
            issues.append(
                {
                    "line": line_no,
                    "type": "character_conservation_mismatch",
                    "message": (
                        "Non-whitespace characters do not match reference line "
                        f"(len {len(reconstructed)} vs {len(expected_chars)})."
                    ),
                }
            )

    return issues


def audit_ner_tsv(lines: list[str]) -> list[dict[str, Any]]:
    """Audit Token-Level POS & BIO NER TSV dataset against 15-class canonical taxonomy,

    BIO transitions, Zero-Clitic Bleed, and Title/Rank separation invariants.
    """
    issues: list[dict[str, Any]] = []
    if not lines:
        return issues
    header = lines[0].strip().split("\t")
    col_map = {col.lower(): idx for idx, col in enumerate(header)}
    ner_col = col_map.get("ner_bio", col_map.get("ner"))
    pos_col = col_map.get("pos")
    tok_col = col_map.get("token")
    line_col = col_map.get("line_number", col_map.get("sentence_id"))

    if ner_col is None or pos_col is None or tok_col is None:
        issues.append(
            {
                "line": 1,
                "type": "invalid_ner_tsv_header",
                "message": f"TSV header must contain 'token', 'pos', and 'ner_bio' (or 'ner'). Got: {header}",
            }
        )
        return issues

    prev_line_id = None
    prev_bio = "O"
    prev_etype: str | None = None

    for row_idx, raw_line in enumerate(lines[1:], start=2):
        if not raw_line.strip():
            continue
        parts = raw_line.rstrip("\r\n").split("\t")
        if len(parts) <= max(ner_col, pos_col, tok_col):
            issues.append(
                {
                    "line": row_idx,
                    "type": "malformed_tsv_row",
                    "message": f"Expected at least {max(ner_col, pos_col, tok_col) + 1} columns, got {len(parts)}",
                }
            )
            continue

        token = parts[tok_col]
        pos = parts[pos_col]
        ner = parts[ner_col]
        curr_line_id = parts[line_col] if line_col is not None and len(parts) > line_col else str(row_idx)

        # 1. POS canonical check
        if pos not in ALLOWED_15_TAGS:
            issues.append(
                {
                    "line": row_idx,
                    "token": token,
                    "type": "invalid_pos_tag",
                    "message": f"Tag '{pos}' is not one of the allowed 15 canonical tags.",
                }
            )

        # 2. NER Syntax check
        if ner == "O":
            prev_bio = "O"
            prev_etype = None
            prev_line_id = curr_line_id
            continue

        m = re.match(r"^(B|I)-([A-Za-z_]+)$", ner)
        if not m:
            issues.append(
                {
                    "line": row_idx,
                    "token": token,
                    "type": "invalid_ner_syntax",
                    "message": f"Invalid NER tag syntax '{ner}'. Must be 'O' or 'B-[CLASS]' or 'I-[CLASS]'.",
                }
            )
            prev_bio = "O"
            prev_etype = None
            prev_line_id = curr_line_id
            continue

        prefix, etype = m.group(1), m.group(2)
        if etype not in ALLOWED_15_NER_CLASSES:
            issues.append(
                {
                    "line": row_idx,
                    "token": token,
                    "type": "invalid_ner_class",
                    "message": f"NER class '{etype}' is not in the canonical 15-class taxonomy: {sorted(ALLOWED_15_NER_CLASSES)}",
                }
            )

        # 3. BIO Transition Invariant Check
        if prefix == "I":
            if curr_line_id != prev_line_id:
                issues.append(
                    {
                        "line": row_idx,
                        "token": token,
                        "type": "orphan_i_tag_across_sentence",
                        "message": f"Orphan '{ner}' tag cannot begin a new sentence without preceding B-{etype}.",
                    }
                )
            elif prev_bio not in ("B", "I") or prev_etype != etype:
                issues.append(
                    {
                        "line": row_idx,
                        "token": token,
                        "type": "invalid_bio_transition",
                        "message": f"Invalid BIO transition: '{ner}' cannot follow '{prev_bio}-{prev_etype if prev_etype else 'O'}'.",
                    }
                )

        # 4. Zero-Clitic Bleed Check
        if pos == "ppm":
            issues.append(
                {
                    "line": row_idx,
                    "token": token,
                    "type": "clitic_bleed_ppm_tagged",
                    "message": f"Postposition token '{token}/ppm' must not have entity tag '{ner}' (Zero-Clitic Invariant).",
                }
            )
        for cl in COMMON_NER_CLITICS:
            if token.endswith(cl) and len(token) > len(cl) and token not in PROTECTED_LEXEMES_ENDING_IN_CLITIC_CHARS:
                issues.append(
                    {
                        "line": row_idx,
                        "token": token,
                        "type": "clitic_bleed_in_token",
                        "message": f"Token '{token}' ends with postposition clitic '{cl}'. Separate clitic before tagging '{ner}'.",
                    }
                )
                break

        # 5. Title Leak Invariant
        if token in TITLES_AND_RANKS and etype == "PER":
            issues.append(
                {
                    "line": row_idx,
                    "token": token,
                    "type": "title_in_per_span",
                    "message": f"Title/rank '{token}' must not be tagged as PER entity (Title/Rank vs. Name Invariant).",
                }
            )

        prev_bio = prefix
        prev_etype = etype
        prev_line_id = curr_line_id

    return issues


def run_self_test() -> int:
    """Run built-in verification tests for all validator capabilities."""
    # Test 1: Valid POS line with owner fixed forms, component splits, ဆိုသည်မှာ, and post-verbal ရာ/part
    valid_pos = "ပြည်နယ်/n အစိုးရ/n အဖွဲ့/n ဆို/v သည်/part မှာ/ppm တပြိုင်နက်/adv ဆောင်ရွက်/v ရာ/part တွင်/ppm အတည်/n ဖြစ်/v သည်/part ။/punc"
    ref_text = "ပြည်နယ်အစိုးရအဖွဲ့ ဆိုသည်မှာ တပြိုင်နက် ဆောင်ရွက်ရာတွင် အတည်ဖြစ်သည်။"
    issues = audit_line(valid_pos, 1, mode="pos", ref_line=ref_text)
    assert not issues, f"Expected 0 issues on valid POS line, got: {issues}"

    # Test 2: Bracket compound reconstruction
    bracket_line = "[မြန်မာ/n | နိုင်ငံတော်/n]/n တွင်/ppm တဖက်သတ်/adv မ/part ပြုလုပ်/v ရ/part ။/punc"
    ref_bracket = "မြန်မာနိုင်ငံတော်တွင် တဖက်သတ် မပြုလုပ်ရ။"
    issues_b = audit_line(bracket_line, 2, mode="bracket", ref_line=ref_bracket)
    assert not issues_b, f"Expected 0 issues on valid bracket line, got: {issues_b}"

    # Test 3: Detect invalid tag, broken dependent sign, wrong fixed tag, ဆိုသည်မှာ violation, post-verbal ရာ/v violation, unsplit title, split name prefix, split paung myarswar, and split noun paung numeral
    bad_line = "တပြိုင်နက်/adj ခ/n ံ/n မြန်မာနိုင်ငံ/n ဆို/v သည်/ppm မှာ/part ဆောင်ရွက်/v ရာ/v တွင်/ppm သည်/DET ဗိုလ်ချုပ်အောင်ဆန်း/n ဦး/part မင်းအောင်လှိုင်/n သန်းပေါင်း/n များစွာ/adv တိုက်ပွဲ/n ပေါင်း/part ၁၀၀/num"
    issues_bad = audit_line(bad_line, 3, mode="pos")
    issue_types = {i["type"] for i in issues_bad}
    assert "owner_fixed_tag_violation" in issue_types, "Missed owner_fixed_tag_violation"
    assert "illegal_word_start_dependent_sign" in issue_types, "Missed illegal dependent sign"
    assert "unsplit_component_standard" in issue_types, "Missed unsplit component standard"
    assert "so_thi_pos_violation" in issue_types, "Missed so_thi_pos_violation"
    assert "so_thi_hma_pos_violation" in issue_types, "Missed so_thi_hma_pos_violation"
    assert "post_verbal_yar_pos_violation" in issue_types, "Missed post_verbal_yar_pos_violation"
    assert "invalid_pos_tag" in issue_types, "Missed invalid_pos_tag (DET)"
    assert "unsplit_title_name" in issue_types, "Missed unsplit_title_name"
    assert "split_name_prefix_violation" in issue_types, "Missed split_name_prefix_violation"
    assert "split_paung_myarswar_violation" in issue_types, "Missed split_paung_myarswar_violation"
    assert "split_noun_paung_numeral_violation" in issue_types, "Missed split_noun_paung_numeral_violation"

    # Test 4: NER TSV validation (valid and defective sequences)
    valid_ner_tsv = [
        "line_number\ttoken_id\ttoken\tpos\tner_bio",
        "1\t1\tဗိုလ်ချုပ်\tn\tO",
        "1\t2\tအောင်ဆန်း\tn\tB-PER",
        "1\t3\tသည်\tppm\tO",
        "1\t4\tရန်ကုန်\tn\tB-GPE",
        "1\t5\tမြို့\tn\tI-GPE",
        "1\t6\tသို့\tppm\tO",
    ]
    ner_ok = audit_ner_tsv(valid_ner_tsv)
    assert not ner_ok, f"Expected 0 issues on valid NER TSV, got: {ner_ok}"

    bad_ner_tsv = [
        "line_number\ttoken_id\ttoken\tpos\tner_bio",
        "1\t1\tဗိုလ်ချုပ်\tn\tB-PER",             # title_in_per_span
        "1\t2\tသည်\tppm\tB-GPE",               # clitic_bleed_ppm_tagged
        "1\t3\tရန်ကုန်\tn\tI-GPE",              # invalid_bio_transition (follows B-GPE on clitic)
        "1\t4\tမြို့\tn\tB-INVALID_CLASS",     # invalid_ner_class
        "2\t1\tစစ်ကိုင်း\tn\tI-LOC",            # orphan_i_tag_across_sentence
    ]
    bad_ner_issues = audit_ner_tsv(bad_ner_tsv)
    bad_ner_types = {i["type"] for i in bad_ner_issues}
    assert "title_in_per_span" in bad_ner_types, "Missed title_in_per_span"
    assert "clitic_bleed_ppm_tagged" in bad_ner_types, "Missed clitic_bleed_ppm_tagged"
    assert "invalid_ner_class" in bad_ner_types, "Missed invalid_ner_class"
    assert "orphan_i_tag_across_sentence" in bad_ner_types, "Missed orphan_i_tag_across_sentence"

    print("SELF-TEST PASSED: All orthographic, 15-tag, fixed-form, component, title-split, prefix-preservation, -ပေါင်းများစွာ, [Noun]ပေါင်း numeral, ဆိုသည်မှာ, ရာ/part, bracket, and 15-class BIO NER checks verified.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Myanmar WS/POS/Bracket/NER NLP files.")
    parser.add_argument("--input", type=Path, help="Input file to validate")
    parser.add_argument("--reference", type=Path, help="Optional raw/reference file for character conservation check")
    parser.add_argument("--mode", choices=["ws", "pos", "bracket", "consistency", "ner"], default="ws", help="Validation mode (consistency=token scan, ner=BIO NER TSV audit)")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--self-test", action="store_true", help="Run built-in unit self-tests")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if not args.input or not args.input.is_file():
        parser.error("--input file is required unless --self-test is specified.")

    input_lines = args.input.read_text(encoding="utf-8").splitlines()
    ref_lines: list[str] | None = None
    if args.reference:
        ref_lines = args.reference.read_text(encoding="utf-8").splitlines()
        if len(ref_lines) != len(input_lines):
            print(
                f"ERROR: Line count mismatch: input={len(input_lines)} vs reference={len(ref_lines)}",
                file=sys.stderr,
            )
            return 1

    # NER Mode: audit token-level POS & BIO NER TSV dataset
    if args.mode == "ner":
        ner_issues = audit_ner_tsv(input_lines)
        report = {
            "file": str(args.input),
            "mode": "ner",
            "token_rows_checked": max(0, len(input_lines) - 1),
            "issue_count": len(ner_issues),
            "status": "pass" if not ner_issues else "fail",
            "issues": ner_issues[:200],
        }
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"Checked {len(input_lines)-1} token rows in '{args.input}' (mode=ner): {report['status'].upper()} ({len(ner_issues)} issues)")
            for issue in ner_issues[:25]:
                print(f"  Row {issue['line']} [{issue['type']}]: {issue['message']}")
        return 0 if not ner_issues else 1

    if args.self_test:
        return run_self_test()

    if not args.input or not args.input.is_file():
        parser.error("--input file is required unless --self-test is specified.")

    input_lines = args.input.read_text(encoding="utf-8").splitlines()
    ref_lines: list[str] | None = None
    if args.reference:
        ref_lines = args.reference.read_text(encoding="utf-8").splitlines()
        if len(ref_lines) != len(input_lines):
            print(
                f"ERROR: Line count mismatch: input={len(input_lines)} vs reference={len(ref_lines)}",
                file=sys.stderr,
            )
            return 1

    # Consistency mode: scan entire file for intra-corpus segmentation mismatches
    if args.mode == "consistency":
        consistency_issues = scan_token_consistency(input_lines, mode="ws")
        report = {
            "file": str(args.input),
            "mode": "consistency",
            "lines_checked": len(input_lines),
            "issue_count": len(consistency_issues),
            "status": "pass" if not consistency_issues else "fail",
            "issues": consistency_issues[:200],
        }
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"Consistency scan '{args.input}': {report['status'].upper()} ({len(consistency_issues)} inconsistent token types)")
            for issue in consistency_issues[:25]:
                print(f"  [{issue['type']}]: {issue['message']}")
        return 0 if not consistency_issues else 1

    all_issues: list[dict[str, Any]] = []
    audit_mode = args.mode  # ws / pos / bracket
    for idx, line in enumerate(input_lines, start=1):
        ref_l = ref_lines[idx - 1] if ref_lines is not None else None
        all_issues.extend(audit_line(line, idx, mode=audit_mode, ref_line=ref_l))

    report = {
        "file": str(args.input),
        "mode": audit_mode,
        "lines_checked": len(input_lines),
        "issue_count": len(all_issues),
        "status": "pass" if not all_issues else "fail",
        "issues": all_issues[:200],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Checked {len(input_lines)} lines in '{args.input}' (mode={audit_mode}): {report['status'].upper()} ({len(all_issues)} issues)")
        for issue in all_issues[:25]:
            print(f"  Line {issue['line']} [{issue['type']}]: {issue['message']}")

    return 0 if not all_issues else 1


if __name__ == "__main__":
    sys.exit(main())
