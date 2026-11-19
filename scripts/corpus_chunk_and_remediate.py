#!/usr/bin/env python3
"""
Myanmar Large-Corpus Chunking, Line-by-Line Streaming & Staged Regex Remediation Engine
(corpus_chunk_and_remediate.py)

Capabilities:
  1. `chunk`: Deterministic splitting of large WS/POS corpus files into line-range chunks
     and human/LLM review sub-chunks with SHA-256 manifest generation.
  2. `merge`: Lossless reassembly of chunks back into unified WS/POS/TSV files with
     strict line-range continuity and non-whitespace character conservation checks.
  3. `remediate`: Constant-memory O(1) line-by-line streaming inspection and 6-stage
     token-bounded regex & contextual POS remediation with automatic rollback on
     character drift, TSV change ledger, and RECORD_ONLY_NOT_APPLIED typo lead logging.
  4. `--self-test`: Built-in end-to-end verification suite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from .common_standards import (
        ALLOWED_15_TAGS,
        CLASSIFIERS as STANDARD_CLASSIFIERS,
        OWNER_COMPONENT_STANDARDS,
        OWNER_COMPONENT_STANDARDS_ORDERED,
        OWNER_FIXED_TAG_SURFACES,
        PROFILES,
        RECORD_ONLY_LEADS,
        normalize_profile,
        parse_pos_token,
        strip_ws,
    )
except ImportError:
    _scripts_dir = str(Path(__file__).resolve().parent)
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)
    from common_standards import (
        ALLOWED_15_TAGS,
        CLASSIFIERS as STANDARD_CLASSIFIERS,
        OWNER_COMPONENT_STANDARDS,
        OWNER_COMPONENT_STANDARDS_ORDERED,
        OWNER_FIXED_TAG_SURFACES,
        PROFILES,
        RECORD_ONLY_LEADS,
        normalize_profile,
        parse_pos_token,
        strip_ws,
    )

# Stage 1..5 WS Regex Cascade (compiled once for streaming performance)
WS_STAGE_RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    # Stage 1: Structural & Orthographic Recovery
    ("Stage1", "S1_KINZI_JOIN", re.compile(r"(\u1004\u103a\u1039)\s+"), r"\1"),
    ("Stage1", "S1_VIRAMA_JOIN", re.compile(r"(\u1039)\s+"), r"\1"),
    ("Stage1", "S1_DEP_SIGN_JOIN", re.compile(r"(?<=\S)\s+([\u102b-\u103e\u1056-\u1059]+)"), r"\1"),
    ("Stage1", "S1_SHATTERED_1", re.compile(r"(?<!\S)ဦး\s+စီ\s+ချုပ်(?!\S)"), "ဦးစီချုပ်"),
    ("Stage1", "S1_SHATTERED_2", re.compile(r"(?<!\S)ပြည်\s+တောင်\s+စု(?!\S)"), "ပြည်တောင်စု"),
    ("Stage1", "S1_SHATTERED_3", re.compile(r"(?<!\S)အ\s+ထင်း\s+အ\s+ရှား(?!\S)"), "အထင်းအရှား"),
    ("Stage1", "S1_SHATTERED_4", re.compile(r"(?<!\S)သံ\s+တ\s+မန်\s+အ\s+ဆက်\s+အ\s+သွယ်(?!\S)"), "သံတမန် အဆက်အသွယ်"),
    # Stage 2: Protected Lexemes & [တ/တစ် + X + တ/တစ် + Y] Idioms
    ("Stage2", "S2_TA_IDIOM_JOIN", re.compile(r"(?<!\S)(တ(?:စ်)?)\s+စုံ\s+(တ(?:စ်)?)\s+(ရာ|ဦး|ယောက်|ခု)(?!\S)"), r"\1စုံ\2\3"),
    ("Stage2", "S2_TA_SHIFT_1", re.compile(r"(?<!\S)ကိစ္စ(တ(?:စ်)?စုံ)\s+(တ(?:စ်)?ရာ)(?!\S)"), r"ကိစ္စ \1\2"),
    ("Stage2", "S2_TA_SHIFT_2", re.compile(r"(?<!\S)(တ(?:စ်)?စုံ)\s+(တ(?:စ်)?ရာ)(သော|သည်|ကို|က)(?!\S)"), r"\1\2 \3"),
    ("Stage2", "S2_TA_PYAING_NAK", re.compile(r"(?<!\S)(တ(?:စ်)?)\s+ပြိုင်\s*နက်(?!\S)"), r"\1ပြိုင်နက်"),
    ("Stage2", "S2_TA_PHAK_THAT", re.compile(r"(?<!\S)(တ(?:စ်)?)\s+ဖက်\s*သတ်(?!\S)"), r"\1ဖက်သတ်"),
    ("Stage2", "S2_TA_KHA_TA_YAN", re.compile(r"(?<!\S)(တ(?:စ်)?)\s+ခါ\s+(တ(?:စ်)?)\s+ရံ(?!\S)"), r"\1ခါ\2ရံ"),
    ("Stage2", "S2_TAKYUN_PENALTY", re.compile(r"(?<!\S)(တ(?:စ်)?ကျွန်း)\s+ပို့\s+ဒဏ်\s*ခံ(?!\S)"), r"\1ပို့ဒဏ် ခံ"),
    ("Stage2", "S2_IDIOM_SAPAY", re.compile(r"(?<!\S)စာ\s+ပေး\s*စာ\s+ယူ(?!\S)"), "စာပေးစာယူ"),
    ("Stage2", "S2_IDIOM_THAKTHAK", re.compile(r"(?<!\S)သက်\s+သက်\s+သာ\s+သာ(?!\S)"), "သက်သက်သာသာ"),
    ("Stage2", "S2_PROT_THAPHYINT", re.compile(r"(?<!\S)သ\s+ဖြင့်(?!\S)"), "သဖြင့်"),
    ("Stage2", "S2_PROT_HNALONETHAR", re.compile(r"(?<!\S)နှ\s*လုံး\s+သား(?!\S)"), "နှလုံးသား"),
    ("Stage2", "S2_PROT_THUTHAN", re.compile(r"(?<!\S)သု\s+သာန်(?!\S)"), "သုသာန်"),
    ("Stage2", "S2_NAME_PREFIX_JOIN", re.compile(r"(?<!\S)(ဦး|ဒေါ်|စဝ်|စော|နော်|ဆလိုင်း|စလိုင်း)\s+(မင်းအောင်လှိုင်|အောင်ဆန်းစုကြည်|ကျော်မိုးထွန်း|စံထွန်း|မုတ်သုန်)(?!\S)"), r"\1\2"),
    ("Stage2", "S2_PAUNG_MYARSWAR_JOIN_1", re.compile(r"(?<!\S)([A-Za-z\u1000-\u109F]+ပေါင်း)\s+များစွာ(?!\S)"), r"\1များစွာ"),
    ("Stage2", "S2_PAUNG_MYARSWAR_JOIN_2", re.compile(r"(?<!\S)([A-Za-z\u1000-\u109F]+ပေါင်း)\s+များ\s+စွာ(?!\S)"), r"\1များစွာ"),
    ("Stage2", "S2_NOUN_PAUNG_NUMERAL_JOIN", re.compile(r"(?<!\S)(တိုက်ပွဲ|အဖွဲ့အစည်း|ရက်|နိုင်ငံ|ပစ်မှတ်|အမှု|လူ)\s+ပေါင်း(?=\s+(?:\d+|[၀-၉]+))(?!\S)"), r"\1ပေါင်း"),
    # Stage 3: Title/Rank Splits
    ("Stage3", "S3_TITLE_BOGYOKE", re.compile(r"(?<!\S)ဗိုလ်ချုပ်အောင်ဆန်း(?!\S)"), "ဗိုလ်ချုပ် အောင်ဆန်း"),
    ("Stage3", "S3_TITLE_BOGYI", re.compile(r"(?<!\S)ဗိုလ်ကြီးဇင်ယော်(?!\S)"), "ဗိုလ်ကြီး ဇင်ယော်"),
    ("Stage3", "S3_TITLE_BOHMU", re.compile(r"(?<!\S)ဗိုလ်မှူးစောမုတ်သုန်(?!\S)"), "ဗိုလ်မှူး စောမုတ်သုန်"),
    ("Stage3", "S3_TITLE_SAWBWA", re.compile(r"(?<!\S)စော်ဘွားကြီးစဝ်စံထွန်း(?!\S)"), "စော်ဘွားကြီး စဝ်စံထွန်း"),
    # Stage 4: Morphosyntactic Chain Rules
    ("Stage4", "S4_YAY_CHAIN_1", re.compile(r"(?<!\S)(လာ|နိုင်|ပေး|ဖြစ်)စေရေး(?!\S)"), r"\1 စေရေး"),
    ("Stage4", "S4_YAY_CHAIN_2", re.compile(r"(?<!\S)ပေးနိုင်ရေး(?!\S)"), "ပေး နိုင်ရေး"),
    ("Stage4", "S4_CHAK_AUX", re.compile(r"(?<!\S)(သတ်မှတ်|ဖော်ပြ|ပြဋ္ဌာန်း)\s*(ထား|ပါ)ချက်(?!\S)"), r"\1 \2 ချက်"),
    ("Stage4", "S4_PROD_SU", re.compile(r"(?<!\S)(လျှောက်ထား|ကြီးကြပ်|ကျူးလွန်|ပိုင်ဆိုင်|ရင်းနှီးမြှုပ်နှံ)သူ(?!\S)"), r"\1 သူ"),
    ("Stage4", "S4_MARKER_AA", re.compile(r"(?<!\S)(သမ္မတ|တရားခံ|တရားလို|တဦး|တစ်ဦး|၎င်း)အား(?!\S)"), r"\1 အား"),
    ("Stage4", "S4_REDUP_CLF", re.compile(r"(?<!\S)(တ(?:စ်)?)\s+(ဦး|ခု|ရပ်|ယောက်|မျိုး)\s+\2(?!ဆောင်|\S)"), r"\1 \2\2"),
    # Stage 5: Boundary-Shift Trap Remediation
    ("Stage5", "S5_TRAP_LAYSAR", re.compile(r"(?<!\S)အများ\s+ကလေး\s+စား\s+ထိုက်(?!\S)"), "အများ က လေးစား ထိုက်"),
    ("Stage5", "S5_TRAP_THUMA", re.compile(r"(?<!\S)ခံ\s+ရ\s+သူမ\s+ဟုတ်\s+ဘဲ(?!\S)"), "ခံ ရ သူ မ ဟုတ် ဘဲ"),
    ("Stage5", "S5_TRAP_AYATHA", re.compile(r"(?<!\S)ဥပဒေ\s+အရသာ(?!\S)"), "ဥပဒေ အရ သာ"),
    ("Stage5", "S5_TRAP_KHANMA", re.compile(r"(?<!\S)အစည်းအဝေးခန်း\s+မ(?!\S)"), "အစည်းအဝေး ခန်းမ"),
    ("Stage5", "S5_TRAP_THATHANA", re.compile(r"(?<!\S)ဗုဒ္ဓ\s+ဘာသာသာ\s*သ\s*နာ(?!\S)"), "ဗုဒ္ဓ ဘာသာ သာသနာ"),
    ("Stage5", "S5_TRAP_MEE", re.compile(r"(?<!\S)မီးငြှိမ်း\s+သတ်\s*ရေး(?!\S)"), "မီး ငြှိမ်းသတ်ရေး"),
    ("Stage5", "S5_TRAP_SIYINCHAK", re.compile(r"(?<!\S)စီရင်ချက်ချ\s+မှတ်(?!\S)"), "စီရင်ချက် ချမှတ်"),
    ("Stage5", "S5_TRAP_THATI", re.compile(r"(?<!\S)သတိမထား\s+ရှိ\s+ဘဲ(?!\S)"), "သတိ မ ထားရှိ ဘဲ"),
    ("Stage5", "S5_TRAP_OOYAY", re.compile(r"(?<!\S)ဦး\s+ရေအနက်(?!\S)"), "ဦးရေ အနက်"),
    ("Stage5", "S5_TRAP_TAWANYU", re.compile(r"(?<!\S)တာဝန်\s+ယူဆောင်\s+ရွက်(?!\S)"), "တာဝန် ယူ ဆောင်ရွက်"),
    ("Stage5", "S5_TRAP_KHETTA", re.compile(r"(?<!\S)ခေတ္တရပ်\s+စောင့်(?!\S)"), "ခေတ္တ ရပ် စောင့်"),
    ("Stage5", "S5_TRAP_KINPHIA", re.compile(r"(?<!\S)အန္တရာယ်\s+ကင်းဖိအား(?!\S)"), "အန္တရာယ် ကင်း ဖိအား"),
    ("Stage5", "S5_TRAP_KASAR", re.compile(r"(?<!\S)ကစား\s+ပြိုင်ပွဲ\s+ကွင်းကြီး(?!\S)"), "ကစားပြိုင်ပွဲကွင်း ကြီး"),
]


def sha256_text(text: str) -> str:
    """Return hex SHA-256 of UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_parse_pos_token(tok: str) -> tuple[str, str]:
    """Parse word/tag using shared parse_pos_token with safe fallback."""
    p = parse_pos_token(tok)
    return p if p is not None else (tok.split("/")[0] if "/" in tok else tok, "unk")


def extract_surface_from_line(line: str, mode: str) -> str:
    """Return the concatenated non-whitespace surface characters of a WS or POS line."""
    if mode == "pos":
        words = [_safe_parse_pos_token(t)[0] for t in line.split()]
        return strip_ws("".join(words))
    return strip_ws(line)


def remediate_single_line(
    line: str,
    line_no: int,
    mode: str = "ws",
    profile: str = "general",
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Apply the 6-stage regex & contextual POS remediation cascade to a single line.
    Guarantees non-whitespace character conservation (rolls back if violated).
    """
    profile = normalize_profile(profile, default="general")
    orig_line = line.rstrip("\r\n")
    orig_chars = extract_surface_from_line(orig_line, mode)
    changes: list[dict[str, Any]] = []
    record_only_hits: list[dict[str, Any]] = []

    # Scan for Stage 6 Owner Record-Only Typo Leads first (never modified)
    for lead_id, pattern, proposed in RECORD_ONLY_LEADS:
        for m in pattern.finditer(orig_line):
            record_only_hits.append(
                {
                    "line_number": line_no,
                    "lead_id": lead_id,
                    "observed_surface": m.group(0),
                    "proposed_reading": proposed,
                    "status": "RECORD_ONLY_NOT_APPLIED",
                }
            )

    working = orig_line

    if mode == "ws":
        # Apply Stage 1, 2, 4, 5 WS regex rules
        for stage, rule_id, regex, repl in WS_STAGE_RULES:
            new_working = regex.sub(repl, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": stage,
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Apply Stage 3: 10-Row Component Split Standards (complete token match)
        for rule_id, surface, comp_list in OWNER_COMPONENT_STANDARDS_ORDERED:
            comp_ws = " ".join(w for w, _ in comp_list)
            pat = re.compile(rf"(?<!\S){re.escape(surface)}(?!\S)")
            new_working = pat.sub(comp_ws, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": "Stage3",
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Split fused ၍ in WS mode (except ဟူ၍, အကယ်၍)
        ws_toks = working.split()
        new_ws_toks: list[str] = []
        ywe_changed = False
        for t in ws_toks:
            if t.endswith("၍") and len(t) > 1 and t not in ("ဟူ၍", "အကယ်၍"):
                new_ws_toks.extend([t[:-1], "၍"])
                ywe_changed = True
            else:
                new_ws_toks.append(t)
        if ywe_changed:
            after_ywe = " ".join(new_ws_toks)
            changes.append(
                {
                    "line_number": line_no,
                    "stage": "Stage4",
                    "rule_id": "S4_SPLIT_YWE",
                    "before": working,
                    "after": after_ywe,
                }
            )
            working = after_ywe

    elif mode == "pos":
        # Stage 1: Structural & Orthographic Recovery in POS
        pos_stage1_rules = [
            ("Stage1", "S1_POS_KINZI_JOIN", re.compile(r"(\u1004\u103a\u1039)(?:/[a-z]+)?\s+([A-Za-z\u1000-\u109F]+)/([a-z]+)"), r"\1\2/\3"),
            ("Stage1", "S1_POS_VIRAMA_JOIN", re.compile(r"(\u1039)(?:/[a-z]+)?\s+([A-Za-z\u1000-\u109F]+)/([a-z]+)"), r"\1\2/\3"),
            ("Stage1", "S1_POS_DEP_SIGN_JOIN", re.compile(r"([A-Za-z\u1000-\u109F]+)/([a-z]+)\s+([\u102b-\u103e\u1056-\u1059]+)(?:/[a-z]+)?(?!\S)"), r"\1\3/\2"),
            ("Stage1", "S1_POS_SHATTERED_1", re.compile(r"(?<!\S)ဦး/[a-z]+\s+စီ/[a-z]+\s+ချုပ်/[a-z]+(?!\S)"), "ဦးစီချုပ်/n"),
            ("Stage1", "S1_POS_SHATTERED_2", re.compile(r"(?<!\S)ပြည်/[a-z]+\s+တောင်/[a-z]+\s+စု/[a-z]+(?!\S)"), "ပြည်တောင်စု/n"),
            ("Stage1", "S1_POS_SHATTERED_3", re.compile(r"(?<!\S)အ/[a-z]+\s+ထင်း/[a-z]+\s+အ/[a-z]+\s+ရှား/[a-z]+(?!\S)"), "အထင်းအရှား/adv"),
            ("Stage1", "S1_POS_SHATTERED_4", re.compile(r"(?<!\S)သံ/[a-z]+\s+တ/[a-z]+\s+မန်/[a-z]+\s+အ/[a-z]+\s+ဆက်/[a-z]+\s+အ/[a-z]+\s+သွယ်/[a-z]+(?!\S)"), "သံတမန်/n အဆက်အသွယ်/n"),
        ]
        for stage, rule_id, regex, repl in pos_stage1_rules:
            new_working = regex.sub(repl, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": stage,
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Stage 2: Protected Lexemes & [တ/တစ် + X + တ/တစ် + Y] Idioms in POS
        pos_stage2_rules = [
            ("Stage2", "S2_POS_TA_IDIOM_JOIN", re.compile(r"(?<!\S)(တ(?:စ်)?)/[a-z]+\s+စုံ/[a-z]+\s+(တ(?:စ်)?)/[a-z]+\s+(ရာ|ဦး|ယောက်|ခု)/[a-z]+(?!\S)"), r"\1စုံ\2\3/pron"),
            ("Stage2", "S2_POS_TA_SHIFT_1", re.compile(r"(?<!\S)ကိစ္စ(တ(?:စ်)?စုံ)/[a-z]+\s+(တ(?:စ်)?(?:ရာ|ဦး|ယောက်|ခု))/[a-z]+(?!\S)"), r"ကိစ္စ/n \1\2/adj"),
            ("Stage2", "S2_POS_TAPYAINGNAK", re.compile(r"(?<!\S)(တ(?:စ်)?)/[a-z]+\s+ပြိုင်\s*နက်/[a-z]+(?!\S)"), r"\1ပြိုင်နက်/adv"),
            ("Stage2", "S2_POS_TAPHAKTHAT", re.compile(r"(?<!\S)(တ(?:စ်)?)/[a-z]+\s+ဖက်\s*သတ်/[a-z]+(?!\S)"), r"\1ဖက်သတ်/adv"),
            ("Stage2", "S2_POS_TA_KHA_TA_YAN", re.compile(r"(?<!\S)(တ(?:စ်)?)/[a-z]+\s+ခါ/[a-z]+\s+(တ(?:စ်)?)/[a-z]+\s+ရံ/[a-z]+(?!\S)"), r"\1ခါ\2ရံ/adv"),
            ("Stage2", "S2_POS_TAKYUN_PENALTY", re.compile(r"(?<!\S)(တ(?:စ်)?ကျွန်း)/[a-z]+\s+ပို့/[a-z]+\s+ဒဏ်/[a-z]+\s*ခံ/[a-z]+(?!\S)"), r"\1ပို့ဒဏ်/n ခံ/v"),
            ("Stage2", "S2_POS_IDIOM_SAPAY", re.compile(r"(?<!\S)စာ/[a-z]+\s+ပေး/[a-z]+\s*စာ/[a-z]+\s+ယူ/[a-z]+(?!\S)"), "စာပေးစာယူ/n"),
            ("Stage2", "S2_POS_IDIOM_THAKTHAK", re.compile(r"(?<!\S)သက်/[a-z]+\s+သက်/[a-z]+\s+သာ/[a-z]+\s+သာ/[a-z]+(?!\S)"), "သက်သက်သာသာ/adv"),
            ("Stage2", "S2_POS_PROT_THAPHYINT", re.compile(r"(?<!\S)သ/[a-z]+\s+ဖြင့်/[a-z]+(?!\S)"), "သဖြင့်/conj"),
            ("Stage2", "S2_POS_PROT_HNALONETHAR", re.compile(r"(?<!\S)နှ/[a-z]+\s*လုံး/[a-z]+\s+သား/[a-z]+(?!\S)"), "နှလုံးသား/n"),
            ("Stage2", "S2_POS_PROT_THUTHAN", re.compile(r"(?<!\S)သု/[a-z]+\s+သာန်/[a-z]+(?!\S)"), "သုသာန်/n"),
            ("Stage2", "S2_POS_NAME_PREFIX_JOIN", re.compile(r"(?<!\S)(ဦး|ဒေါ်|စဝ်|စော|နော်|ဆလိုင်း|စလိုင်း)/[a-z]+\s+(မင်းအောင်လှိုင်|အောင်ဆန်းစုကြည်|ကျော်မိုးထွန်း|စံထွန်း|မုတ်သုန်)/[a-z]+(?!\S)"), r"\1\2/n"),
            ("Stage2", "S2_POS_PAUNG_MYARSWAR_JOIN_1", re.compile(r"(?<!\S)([A-Za-z\u1000-\u109F]+ပေါင်း)/[a-z]+\s+များစွာ/[a-z]+(?!\S)"), r"\1များစွာ/adj"),
            ("Stage2", "S2_POS_PAUNG_MYARSWAR_JOIN_2", re.compile(r"(?<!\S)([A-Za-z\u1000-\u109F]+ပေါင်း)/[a-z]+\s+များ/[a-z]+\s+စွာ/[a-z]+(?!\S)"), r"\1များစွာ/adj"),
            ("Stage2", "S2_POS_NOUN_PAUNG_NUMERAL_JOIN", re.compile(r"(?<!\S)(တိုက်ပွဲ|အဖွဲ့အစည်း|ရက်|နိုင်ငံ|ပစ်မှတ်|အမှု|လူ)/[a-z]+\s+ပေါင်း/[a-z]+(?=\s+(?:\d+|[၀-၉]+)/num)"), r"\1ပေါင်း/n"),
            ("Stage2", "S2_POS_PAUNG_MYARSWAR_ADV", re.compile(r"(?<!\S)(နှစ်ပေါင်းများစွာ|လပေါင်းများစွာ|ရာစုနှစ်ပေါင်းများစွာ)/adj(?!\S)"), r"\1/adv"),
        ]
        for stage, rule_id, regex, repl in pos_stage2_rules:
            new_working = regex.sub(repl, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": stage,
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Stage 3: Title/Rank Splits on POS tokens
        pos_title_split_rules = [
            ("Stage3", "S3_POS_TITLE_BOGYOKE", re.compile(r"(?<!\S)ဗိုလ်ချုပ်အောင်ဆန်း/n(?!\S)"), "ဗိုလ်ချုပ်/n အောင်ဆန်း/n"),
            ("Stage3", "S3_POS_TITLE_BOGYI", re.compile(r"(?<!\S)ဗိုလ်ကြီးဇင်ယော်/n(?!\S)"), "ဗိုလ်ကြီး/n ဇင်ယော်/n"),
            ("Stage3", "S3_POS_TITLE_BOHMU", re.compile(r"(?<!\S)ဗိုလ်မှူးစောမုတ်သုန်/n(?!\S)"), "ဗိုလ်မှူး/n စောမုတ်သုန်/n"),
            ("Stage3", "S3_POS_TITLE_SAWBWA", re.compile(r"(?<!\S)စော်ဘွားကြီးစဝ်စံထွန်း/n(?!\S)"), "စော်ဘွားကြီး/n စဝ်စံထွန်း/n"),
        ]
        for stage, rule_id, regex, repl in pos_title_split_rules:
            new_working = regex.sub(repl, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": stage,
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Stage 3: 10-Row Component Split Standards on POS tokens
        for rule_id, surface, comp_list in OWNER_COMPONENT_STANDARDS_ORDERED:
            comp_pos = " ".join(f"{w}/{p}" for w, p in comp_list)
            pat = re.compile(rf"(?<!\S){re.escape(surface)}/[a-z]+(?!\S)")
            new_working = pat.sub(comp_pos, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": "Stage3",
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Stage 4: Morphosyntactic Chain Rules in POS
        pos_stage4_rules = [
            ("Stage4", "S4_POS_YAY_CHAIN_1", re.compile(r"(?<!\S)(လာ|နိုင်|ပေး|ဖြစ်)စေရေး/[a-z]+(?!\S)"), r"\1/v စေရေး/n"),
            ("Stage4", "S4_POS_YAY_CHAIN_2", re.compile(r"(?<!\S)ပေးနိုင်ရေး/[a-z]+(?!\S)"), "ပေး/v နိုင်ရေး/n"),
            ("Stage4", "S4_POS_CHAK_AUX", re.compile(r"(?<!\S)(သတ်မှတ်|ဖော်ပြ|ပြဋ္ဌာန်း)(?:/[a-z]+)?\s*(ထား|ပါ)ချက်/[a-z]+(?!\S)"), r"\1/v \2/part ချက်/n"),
            ("Stage4", "S4_POS_PROD_SU", re.compile(r"(?<!\S)(လျှောက်ထား|ကြီးကြပ်|ကျူးလွန်|ပိုင်ဆိုင်|ရင်းနှီးမြှုပ်နှံ)သူ/[a-z]+(?!\S)"), r"\1/v သူ/part"),
            ("Stage4", "S4_POS_MARKER_AA", re.compile(r"(?<!\S)(သမ္မတ|တရားခံ|တရားလို|တဦး|တစ်ဦး|၎င်း)အား/[a-z]+(?!\S)"), r"\1/n အား/ppm"),
            ("Stage4", "S4_POS_REDUP_CLF", re.compile(r"(?<!\S)(တ(?:စ်)?)/[a-z]+\s+(ဦး|ခု|ရပ်|ယောက်|မျိုး)/[a-z]+\s+\2/[a-z]+(?!ဆောင်|\S)"), r"\1/tn \2\2/part"),
        ]
        for stage, rule_id, regex, repl in pos_stage4_rules:
            new_working = regex.sub(repl, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": stage,
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Stage 4B: Universal splitting of fused '၍' on POS tokens
        raw_toks = working.split()
        ywe_toks: list[str] = []
        ywe_split = False
        for t in raw_toks:
            w, pos = _safe_parse_pos_token(t)
            if w.endswith("၍") and len(w) > 1 and w not in ("ဟူ၍", "အကယ်၍"):
                stem = w[:-1]
                ywe_split = True
                if stem in ("ပို", "ဆက်လက်"):
                    ywe_toks.append(f"{stem}/adv")
                    ywe_toks.append("၍/part")
                else:
                    stem_pos = pos if pos in ("v", "adj", "adv") else "v"
                    ywe_toks.append(f"{stem}/{stem_pos}")
                    ywe_toks.append("၍/conj")
            else:
                ywe_toks.append(t)
        if ywe_split:
            after_ywe = " ".join(ywe_toks)
            changes.append(
                {
                    "line_number": line_no,
                    "stage": "Stage4",
                    "rule_id": "S4_SPLIT_YWE_POS",
                    "before": working,
                    "after": after_ywe,
                }
            )
            working = after_ywe

        # Stage 5: Boundary-Shift Trap Remediation on POS
        pos_trap_rules = [
            ("Stage5", "S5_POS_TRAP_LAYSAR", re.compile(r"(?<!\S)အများ/[a-z]+\s+ကလေး/[a-z]+\s+စား/[a-z]+\s+ထိုက်/[a-z]+(?!\S)"), "အများ/n က/ppm လေးစား/v ထိုက်/part"),
            ("Stage5", "S5_POS_TRAP_THUMA", re.compile(r"(?<!\S)ခံ/[a-z]+\s+ရ/[a-z]+\s+သူမ/[a-z]+\s+ဟုတ်/[a-z]+\s+ဘဲ/[a-z]+(?!\S)"), "ခံ/v ရ/part သူ/n မ/part ဟုတ်/v ဘဲ/part"),
            ("Stage5", "S5_POS_TRAP_AYATHA", re.compile(r"(?<!\S)ဥပဒေ/[a-z]+\s+အရသာ/[a-z]+(?!\S)"), "ဥပဒေ/n အရ/ppm သာ/part"),
            ("Stage5", "S5_POS_TRAP_KHANMA", re.compile(r"(?<!\S)အစည်းအဝေးခန်း/[a-z]+\s+မ/[a-z]+(?!\S)"), "အစည်းအဝေး/n ခန်းမ/n"),
            ("Stage5", "S5_POS_TRAP_THATHANA", re.compile(r"(?<!\S)ဗုဒ္ဓ/[a-z]+\s+ဘာသာသာ/[a-z]+\s*သ/[a-z]+\s*နာ/[a-z]+(?!\S)"), "ဗုဒ္ဓ/n ဘာသာ/n သာသနာ/n"),
            ("Stage5", "S5_POS_TRAP_MEE", re.compile(r"(?<!\S)မီးငြှိမ်း/[a-z]+\s+သတ်/[a-z]+\s*ရေး/[a-z]+(?!\S)"), "မီး/n ငြှိမ်းသတ်ရေး/n"),
            ("Stage5", "S5_POS_TRAP_SIYINCHAK", re.compile(r"(?<!\S)စီရင်ချက်ချ/[a-z]+\s+မှတ်/[a-z]+(?!\S)"), "စီရင်ချက်/n ချမှတ်/v"),
            ("Stage5", "S5_POS_TRAP_THATI", re.compile(r"(?<!\S)သတိမထား/[a-z]+\s+ရှိ/[a-z]+\s+ဘဲ/[a-z]+(?!\S)"), "သတိ/n မ/part ထားရှိ/v ဘဲ/part"),
            ("Stage5", "S5_POS_TRAP_OOYAY", re.compile(r"(?<!\S)ဦး/[a-z]+\s+ရေအနက်/[a-z]+(?!\S)"), "ဦးရေ/n အနက်/ppm"),
            ("Stage5", "S5_POS_TRAP_TAWANYU", re.compile(r"(?<!\S)တာဝန်/[a-z]+\s+ယူဆောင်/[a-z]+\s+ရွက်/[a-z]+(?!\S)"), "တာဝန်/n ယူ/v ဆောင်ရွက်/v"),
            ("Stage5", "S5_POS_TRAP_KHETTA", re.compile(r"(?<!\S)ခေတ္တရပ်/[a-z]+\s+စောင့်/[a-z]+(?!\S)"), "ခေတ္တ/adv ရပ်/v စောင့်/v"),
            ("Stage5", "S5_POS_TRAP_KINPHIA", re.compile(r"(?<!\S)အန္တရာယ်/[a-z]+\s+ကင်းဖိအား/[a-z]+(?!\S)"), "အန္တရာယ်/n ကင်း/adj ဖိအား/n"),
            ("Stage5", "S5_POS_TRAP_KASAR", re.compile(r"(?<!\S)ကစား/[a-z]+\s+ပြိုင်ပွဲ/[a-z]+\s+ကွင်းကြီး/[a-z]+(?!\S)"), "ကစားပြိုင်ပွဲကွင်း/n ကြီး/adj"),
        ]
        for stage, rule_id, regex, repl in pos_trap_rules:
            new_working = regex.sub(repl, working)
            if new_working != working:
                changes.append(
                    {
                        "line_number": line_no,
                        "stage": stage,
                        "rule_id": rule_id,
                        "before": working,
                        "after": new_working,
                    }
                )
                working = new_working

        # Stage 5B: Token-level Contextual POS Refinements & Verbal Chains
        cur_toks = working.split()
        final_toks: list[str] = []
        n_toks = len(cur_toks)
        pos_refined = False

        classifiers = set(STANDARD_CLASSIFIERS)
        aspect_aux = {
            "ခဲ့", "ပြီး", "နိုင်", "ရ", "စေ", "သင့်", "လိုက်", "နေ", "ပေး", "ထား",
            "သွား", "လာ", "ပါ", "ကြ", "မိ", "ချင်", "တတ်", "ထိုက်", "အပ်", "ပိုင်",
            "ဖူး", "ပြန်", "ဦး", "လိမ့်", "တော့"
        }
        quotatives = {"ဟု", "ဟူ၍", "ဟူသော", "ဟူသည်"}
        post_verb_rel_markers = {
            "ကို", "အား", "မှာ", "တွင်", "၌", "မှ", "သို့", "၏", "ရဲ့", "က",
            "နှင့်", "ဟု", "ဟူ၍", "ဟူသော", "သော", "သည့်", "ခါ", "အခါ", "တိုင်း",
            "လျှင်", "သော်လည်း", "သော်"
        }

        for i, tok in enumerate(cur_toks):
            w, pos = _safe_parse_pos_token(tok)
            new_pos = pos
            # Read prev_w and prev_pos from final_toks if available so verbal chain propagates!
            prev_w, prev_pos = _safe_parse_pos_token(final_toks[i - 1]) if i > 0 else ("", "")
            next_w, next_pos = _safe_parse_pos_token(cur_toks[i + 1]) if i + 1 < n_toks else ("", "")
            p2 = _safe_parse_pos_token(cur_toks[i - 2]) if i >= 2 else None

            # 1. Owner 11 Fixed-Tag Exact Surfaces (Highest Precedence)
            if w in OWNER_FIXED_TAG_SURFACES:
                new_pos = OWNER_FIXED_TAG_SURFACES[w]

            # 2. Archaic idioms: တစုံတဦး / တစုံတယောက် / တစုံတခု / တစုံတရာ
            elif w in ("တစုံတရာ", "တစုံတဦး", "တစုံတယောက်", "တစုံတခု", "တစ်စုံတစ်ရာ", "တစ်စုံတစ်ဦး", "တစ်စုံတစ်ယောက်", "တစ်စုံတစ်ခု"):
                if prev_pos == "n" or next_w == "သော":
                    new_pos = "adj"
                elif next_pos in ("ppm", "conj") or next_w in ("ကို", "က", "သည်", "၏", "မှ", "အား"):
                    new_pos = "pron"
                else:
                    new_pos = "pron"

            # 3. Pre-verbal negation မ -> /part (preserving ကျား - မ/n ဘာဝ/n)
            elif w == "မ" and i + 1 < n_toks:
                if prev_w in ("-", "—") and p2 and p2[0] == "ကျား":
                    new_pos = "n"
                elif next_pos in ("v", "adj", "part"):
                    new_pos = "part"

            # 4. Quotative & complementizer particles -> /part
            elif w in quotatives:
                new_pos = "part"

            # 5. ဆိုသည်မှာ pattern: ဆို/v သည်/part မှာ/ppm
            elif w == "သည်" and prev_w == "ဆို" and prev_pos == "v":
                new_pos = "part"
            elif w == "မှာ" and prev_w == "သည်" and p2 and p2[0] == "ဆို":
                new_pos = "ppm"

            # 6. Medial and final သည်/မည်
            elif w == "သည်" and prev_pos in ("v", "part", "adj"):
                if i == n_toks - 1 or next_w == "။":
                    # Sentence-final
                    if profile != "legacy_mypos_alt":
                        new_pos = "part"
                    else:
                        new_pos = "ppm"
                elif next_pos in ("ppm", "conj") or next_w in post_verb_rel_markers:
                    new_pos = "part"

            elif w == "မည်" and (i == n_toks - 1 or next_w == "။"):
                if prev_pos in ("v", "part", "adj"):
                    new_pos = "part"

            # 7. Post-verbal ရာ -> /part
            elif w == "ရာ" and pos != "tn":
                if prev_pos in ("v", "part"):
                    new_pos = "part"

            # 8. Nominalizers ခြင်း, မှု, ခွင့် after verb OR particle -> /part
            elif w in ("ခြင်း", "မှု", "ခွင့်") and prev_pos in ("v", "part"):
                new_pos = "part"

            # 9. Aspect/auxiliary particles in verbal chains after v or part -> /part (excluding immediate post-negation main verb)
            elif w in aspect_aux and prev_pos in ("v", "part") and prev_w != "မ":
                new_pos = "part"

            # 10. Spelled numerals တ, တစ် before classifier -> /tn
            elif w in ("တ", "တစ်") and next_w in classifiers:
                new_pos = "tn"

            # 11. Decimal point ဒသမ between numerals -> /n
            elif w == "ဒသမ" and prev_pos in ("tn", "num") and next_pos in ("tn", "num"):
                new_pos = "n"

            # 12. မြေပေါ် in Row 10 context -> /n
            elif w == "မြေပေါ်" and pos == "adj":
                new_pos = "n"

            if new_pos != pos:
                pos_refined = True
            final_toks.append(f"{w}/{new_pos}")

        if pos_refined:
            after_pos = " ".join(final_toks)
            changes.append(
                {
                    "line_number": line_no,
                    "stage": "Stage5",
                    "rule_id": "S5_CONTEXTUAL_POS_REFINE",
                    "before": working,
                    "after": after_pos,
                }
            )
            working = after_pos

    # Stage 6: Non-Whitespace Character Conservation Gate
    new_chars = extract_surface_from_line(working, mode)
    if new_chars != orig_chars:
        changes.append(
            {
                "line_number": line_no,
                "stage": "Stage6_Gate",
                "rule_id": "CHAR_CONSERVATION_ROLLBACK",
                "before": working,
                "after": orig_line,
            }
        )
        return orig_line, changes, record_only_hits

    return working, changes, record_only_hits


def chunk_corpus_file(
    input_path: Path,
    outdir: Path,
    chunk_size: int = 1000,
    subchunk_size: int | None = None,
) -> dict[str, Any]:
    """
    Split a large corpus file into deterministic line-range chunks (and optional sub-chunks)
    using line-by-line streaming, preserving 1-based global line numbers and SHA-256 hashes.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    raw_bytes = input_path.read_bytes()
    source_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    lines = raw_bytes.decode("utf-8").splitlines()
    total_lines = len(lines)

    chunks_meta: list[dict[str, Any]] = []

    for start_idx in range(0, total_lines, chunk_size):
        end_idx = min(start_idx + chunk_size, total_lines)
        start_line = start_idx + 1
        end_line = end_idx
        chunk_num = (start_idx // chunk_size) + 1
        chunk_lines = lines[start_idx:end_idx]

        txt_name = f"chunk_{chunk_num:04d}_lines_{start_line:06d}_{end_line:06d}.txt"
        json_name = f"chunk_{chunk_num:04d}_lines_{start_line:06d}_{end_line:06d}.json"
        txt_path = outdir / txt_name
        json_path = outdir / json_name

        txt_content = "\n".join(chunk_lines) + "\n"
        txt_path.write_text(txt_content, encoding="utf-8")

        records = [
            {"line_number": start_line + i, "text": l}
            for i, l in enumerate(chunk_lines)
        ]
        payload: dict[str, Any] = {
            "chunk_id": chunk_num,
            "line_range": {"start_line": start_line, "end_line": end_line},
            "total_lines": len(records),
            "sha256": sha256_text(txt_content),
            "records": records,
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        subchunks_info: list[dict[str, Any]] = []
        if subchunk_size and subchunk_size > 0:
            sub_dir = outdir / f"subchunks_{chunk_num:04d}"
            sub_dir.mkdir(parents=True, exist_ok=True)
            for s_idx in range(0, len(records), subchunk_size):
                sub_recs = records[s_idx : s_idx + subchunk_size]
                s_start = sub_recs[0]["line_number"]
                s_end = sub_recs[-1]["line_number"]
                sub_name = f"subchunk_lines_{s_start:06d}_{s_end:06d}.txt"
                sub_path = sub_dir / sub_name
                sub_content = "\n".join(
                    f"Line {r['line_number']}:\t{r['text']}" for r in sub_recs
                ) + "\n"
                sub_path.write_text(sub_content, encoding="utf-8")
                subchunks_info.append(
                    {
                        "file": str(sub_path.relative_to(outdir)),
                        "start_line": s_start,
                        "end_line": s_end,
                        "line_count": len(sub_recs),
                    }
                )

        chunks_meta.append(
            {
                "chunk_id": chunk_num,
                "txt_file": txt_name,
                "json_file": json_name,
                "start_line": start_line,
                "end_line": end_line,
                "line_count": len(chunk_lines),
                "sha256": sha256_text(txt_content),
                "subchunks": subchunks_info,
            }
        )

    manifest = {
        "source_file": input_path.name,
        "source_sha256": source_sha256,
        "total_lines": total_lines,
        "chunk_size": chunk_size,
        "subchunk_size": subchunk_size,
        "total_chunks": len(chunks_meta),
        "chunks": chunks_meta,
    }
    manifest_path = outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def merge_chunks(
    manifest_path: Path,
    output_path: Path,
    reference_path: Path | None = None,
) -> dict[str, Any]:
    """
    Reassemble chunk files into a single corpus file and verify 1-based line continuity
    and non-whitespace character conservation against the original reference file.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_dir = manifest_path.parent
    merged_lines: list[str] = []
    expected_next_line = 1

    for chunk in sorted(manifest["chunks"], key=lambda c: c["chunk_id"]):
        if chunk["start_line"] != expected_next_line:
            raise ValueError(
                f"Line continuity gap at chunk {chunk['chunk_id']}: "
                f"expected start_line {expected_next_line}, got {chunk['start_line']}"
            )
        txt_path = base_dir / chunk["txt_file"]
        c_lines = txt_path.read_text(encoding="utf-8").splitlines()
        if len(c_lines) != chunk["line_count"]:
            raise ValueError(
                f"Chunk {chunk['chunk_id']} line count mismatch: "
                f"expected {chunk['line_count']}, got {len(c_lines)}"
            )
        merged_lines.extend(c_lines)
        expected_next_line = chunk["end_line"] + 1

    if len(merged_lines) != manifest["total_lines"]:
        raise ValueError(
            f"Total merged lines ({len(merged_lines)}) != manifest total_lines ({manifest['total_lines']})"
        )

    if reference_path and reference_path.is_file():
        ref_lines = reference_path.read_text(encoding="utf-8").splitlines()
        if len(ref_lines) != len(merged_lines):
            raise ValueError("Reference file line count does not match merged output.")
        for idx, (m_line, r_line) in enumerate(zip(merged_lines, ref_lines), start=1):
            if strip_ws(m_line) != strip_ws(r_line):
                raise ValueError(f"Character conservation mismatch at merged line {idx}")

    output_content = "\n".join(merged_lines) + "\n"
    output_path.write_text(output_content, encoding="utf-8")
    return {
        "output_file": str(output_path),
        "total_lines": len(merged_lines),
        "output_sha256": sha256_text(output_content),
        "status": "merged_verified",
    }


def stream_remediate_file(
    input_path: Path,
    output_path: Path | None,
    mode: str = "ws",
    profile: str = "general",
    dry_run: bool = False,
    ledger_path: Path | None = None,
    record_only_path: Path | None = None,
    sync_ws_path: Path | None = None,
) -> dict[str, Any]:
    """
    Stream a corpus file line-by-line (O(1) RAM per line), applying the 6-stage
    regex and contextual POS remediation cascade with character-conservation guard.
    """
    profile = normalize_profile(profile, default="general")
    total_lines = 0
    modified_lines = 0
    all_changes: list[dict[str, Any]] = []
    all_record_only: list[dict[str, Any]] = []

    out_fh = None
    if output_path and not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_fh = output_path.open("w", encoding="utf-8")

    sync_ws_fh = None
    if sync_ws_path and not dry_run:
        sync_ws_path.parent.mkdir(parents=True, exist_ok=True)
        sync_ws_fh = sync_ws_path.open("w", encoding="utf-8")

    try:
        with input_path.open("r", encoding="utf-8") as in_fh:
            for line_no, raw_line in enumerate(in_fh, start=1):
                total_lines += 1
                remediated, changes, record_hits = remediate_single_line(
                    raw_line, line_no, mode=mode, profile=profile
                )
                if changes:
                    modified_lines += 1
                    all_changes.extend(changes)
                if record_hits:
                    all_record_only.extend(record_hits)
                if out_fh is not None:
                    out_fh.write(remediated + "\n")
                if sync_ws_fh is not None:
                    if mode == "pos":
                        ws_toks = [_safe_parse_pos_token(t)[0] for t in remediated.split()]
                        sync_ws_fh.write(" ".join(ws_toks) + "\n")
                    else:
                        sync_ws_fh.write(remediated + "\n")
    finally:
        if out_fh is not None:
            out_fh.close()
        if sync_ws_fh is not None:
            sync_ws_fh.close()

    if ledger_path and not dry_run:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with ledger_path.open("w", encoding="utf-8") as l_fh:
            l_fh.write("line_number\tstage\trule_id\tbefore\tafter\n")
            for ch in all_changes:
                l_fh.write(
                    f"{ch['line_number']}\t{ch['stage']}\t{ch['rule_id']}\t{ch['before']}\t{ch['after']}\n"
                )

    if record_only_path and not dry_run:
        record_only_path.parent.mkdir(parents=True, exist_ok=True)
        with record_only_path.open("w", encoding="utf-8") as r_fh:
            for hit in all_record_only:
                r_fh.write(json.dumps(hit, ensure_ascii=False) + "\n")

    return {
        "input_file": str(input_path),
        "output_file": str(output_path) if output_path and not dry_run else None,
        "mode": mode,
        "profile": profile,
        "dry_run": dry_run,
        "total_lines": total_lines,
        "modified_lines": modified_lines,
        "total_stage_edits": len(all_changes),
        "record_only_typo_hits": len(all_record_only),
    }


def run_self_test() -> int:
    """Verify chunking, merging, line-by-line streaming, WS↔POS parity, and all 6 regex stages."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # 1. Test WS 6-stage remediation
        sample_ws_lines = [
            "ဦး စီ ချုပ် က ကိစ္စတစုံ တရာ ကို တ ပြိုင် နက် ဆောင်ရွက် သည် ။",
            "ပြည်နယ်အစိုးရအဖွဲ့ သည် အများ ကလေး စား ထိုက် သူမ ဟုတ် ဘဲ ဖွံ့ဖြိုး တိုးတက် လာစေရေး ဆောင်ရွက်၍ နေ သည် ။",
            "တကျွန်း ပို့ ဒဏ်ခံ နေ ရ သော်လည်း တကျွန်း အပို့ ခံ ရ သူ နှင့် ပြည်သူ့ ကော်စီ စည်းမျည်း ကို စစ်ဆေး သည် ။",
            "အန္တရာယ် ကင်းဖိအား ထိန်း နှင့် ကစား ပြိုင်ပွဲ ကွင်းကြီး တွင် တစ် ဦး ဦး က လျှောက်ထားသူ ဖြစ် သည် ။",
        ]
        ws_in = tmpdir / "sample_ws.txt"
        ws_out = tmpdir / "sample_ws_remediated.txt"
        ws_ledger = tmpdir / "ws_ledger.tsv"
        ws_leads = tmpdir / "ws_leads.jsonl"
        ws_in.write_text("\n".join(sample_ws_lines) + "\n", encoding="utf-8")

        summary = stream_remediate_file(
            ws_in, ws_out, mode="ws", dry_run=False, ledger_path=ws_ledger, record_only_path=ws_leads
        )
        assert summary["total_lines"] == 4
        assert summary["modified_lines"] == 4
        assert summary["record_only_typo_hits"] >= 1

        out_lines = ws_out.read_text(encoding="utf-8").splitlines()
        assert "ဦးစီချုပ် က ကိစ္စ တစုံတရာ ကို တပြိုင်နက် ဆောင်ရွက် သည် ။" == out_lines[0], out_lines[0]
        assert "ပြည်နယ် အစိုးရ အဖွဲ့" in out_lines[1], out_lines[1]
        assert "အများ က လေးစား ထိုက်" in out_lines[1], out_lines[1]
        assert "လာ စေရေး" in out_lines[1], out_lines[1]
        assert "ဆောင်ရွက် ၍" in out_lines[1], out_lines[1]
        assert "တကျွန်းပို့ဒဏ် ခံ" in out_lines[2] and "တကျွန်း အပို့ ခံ" in out_lines[2], out_lines[2]
        assert "အန္တရာယ် ကင်း ဖိအား" in out_lines[3] and "ကစားပြိုင်ပွဲကွင်း ကြီး" in out_lines[3], out_lines[3]
        assert "တစ် ဦးဦး" in out_lines[3] and "လျှောက်ထား သူ" in out_lines[3], out_lines[3]

        # 2. Test POS mode 6-stage remediation & verbal chains / nominalizers / alignment
        sample_pos = "မြန်မာနိုင်ငံတော်/n တွင်/ppm တမျိုးတည်း/adv မ/n သွား/v ခဲ့/v ခြင်း/n လက်ခံ၍/v ဟု/conj ဆို/v သည်/ppm ။/punc"
        remediated_pos, pos_changes, _ = remediate_single_line(sample_pos, 1, mode="pos")
        assert "မြန်မာ/n နိုင်ငံတော်/n" in remediated_pos, remediated_pos
        assert "တမျိုးတည်း/adj" in remediated_pos, remediated_pos
        assert "မ/part သွား/v ခဲ့/part ခြင်း/part" in remediated_pos, remediated_pos
        assert "လက်ခံ/v ၍/conj ဟု/part" in remediated_pos, remediated_pos
        assert len(pos_changes) >= 2

        # 2b. Test POS alignment with Stage 1, 2, 4, 5 and verbal chains / medial သည်
        pos_align_test = (
            "ဦး/n စီ/n ချုပ်/n က/ppm တ/tn စုံ/n တ/tn ယောက်/n အား/n ပေးနိုင်ရေး/n "
            "အတွက်/ppm လျှောက်ထားသူ/n ကို/ppm အများ/n ကလေး/n စား/n ထိုက်/v စေ/v ရန်/conj "
            "သွား/v ခဲ့/v နိုင်/v ခြင်း/n သည်/ppm ကို/ppm သိ/v သည်/ppm ။/punc"
        )
        rem_pos, _, _ = remediate_single_line(pos_align_test, 2, mode="pos", profile="general")
        assert "ဦးစီချုပ်/n" in rem_pos, f"Stage 1 shattered failed in POS: {rem_pos}"
        assert "တစုံတယောက်/pron" in rem_pos, f"Stage 2 ta idiom failed in POS: {rem_pos}"
        assert "ပေး/v နိုင်ရေး/n" in rem_pos, f"Stage 4 morphosyntactic split failed: {rem_pos}"
        assert "လျှောက်ထား/v သူ/part" in rem_pos, f"Stage 4 su split failed: {rem_pos}"
        assert "အများ/n က/ppm လေးစား/v ထိုက်/part" in rem_pos, f"Stage 5 trap failed: {rem_pos}"
        assert "သွား/v ခဲ့/part နိုင်/part ခြင်း/part" in rem_pos, f"Verbal chain propagation failed: {rem_pos}"
        assert "သည်/part ကို/ppm" in rem_pos, f"Medial သည် conversion failed: {rem_pos}"
        assert "သိ/v သည်/part ။/punc" in rem_pos, f"Sentence-final သည် general profile failed: {rem_pos}"

        # 2c. Profile-aware sentence-final သည် under legacy_mypos_alt
        rem_legacy, _, _ = remediate_single_line("သွား/v သည်/ppm ။/punc", 3, mode="pos", profile="legacy_mypos_alt")
        assert "သွား/v သည်/ppm ။/punc" in rem_legacy, f"Legacy profile final ppm corrupted: {rem_legacy}"

        # 2d. Test --sync-ws-out streaming option
        pos_file = tmpdir / "test_corpus_pos.txt"
        pos_file.write_text(pos_align_test + "\n", encoding="utf-8")
        pos_rem_file = tmpdir / "test_corpus_pos_rem.txt"
        sync_ws_file = tmpdir / "test_corpus_ws_synced.txt"
        stream_remediate_file(
            pos_file,
            pos_rem_file,
            mode="pos",
            profile="general",
            sync_ws_path=sync_ws_file,
        )
        assert sync_ws_file.is_file(), "sync_ws_file not created"
        synced_ws_line = sync_ws_file.read_text(encoding="utf-8").strip()
        rem_pos_line = pos_rem_file.read_text(encoding="utf-8").strip()
        pos_surfaces = [_safe_parse_pos_token(t)[0] for t in rem_pos_line.split()]
        assert synced_ws_line == " ".join(pos_surfaces), "sync-ws-out token parity mismatch"

        # 3. Test deterministic chunking and lossless merge
        chunk_dir = tmpdir / "chunks"
        manifest = chunk_corpus_file(ws_out, chunk_dir, chunk_size=2, subchunk_size=1)
        assert manifest["total_chunks"] == 2
        merged_out = tmpdir / "merged_ws.txt"
        merge_report = merge_chunks(chunk_dir / "manifest.json", merged_out, reference_path=ws_in)
        assert merge_report["status"] == "merged_verified"
        assert merged_out.read_text(encoding="utf-8") == ws_out.read_text(encoding="utf-8")

    print(
        "SELF-TEST PASSED: Deterministic chunking, lossless merge, line-by-line streaming, "
        "WS↔POS parity, verbal chains, and all 6 regex/POS remediation stages verified."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Large-Corpus Chunking, Line-by-Line Streaming & Staged Regex Remediation CLI"
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-test suite")
    subparsers = parser.add_subparsers(dest="command")

    # chunk subcommand
    p_chunk = subparsers.add_parser("chunk", help="Split a large corpus file into line-range chunks")
    p_chunk.add_argument("--input", type=Path, required=True, help="Input corpus file")
    p_chunk.add_argument("--outdir", type=Path, required=True, help="Output directory for chunks")
    p_chunk.add_argument("--chunk-size", type=int, default=1000, help="Lines per primary chunk (default: 1000)")
    p_chunk.add_argument("--subchunk-size", type=int, default=100, help="Lines per review sub-chunk (default: 100)")

    # merge subcommand
    p_merge = subparsers.add_parser("merge", help="Merge chunks back into a unified corpus file")
    p_merge.add_argument("--manifest", type=Path, required=True, help="Path to manifest.json")
    p_merge.add_argument("--output", type=Path, required=True, help="Output merged file path")
    p_merge.add_argument("--reference", type=Path, help="Optional original file for character conservation check")

    # remediate subcommand
    p_rem = subparsers.add_parser("remediate", help="Run line-by-line streaming 6-stage remediation")
    p_rem.add_argument("--input", type=Path, required=True, help="Input WS or POS file")
    p_rem.add_argument("--output", type=Path, help="Output remediated file")
    p_rem.add_argument("--mode", choices=["ws", "pos"], default="ws", help="Stream mode: ws or pos")
    p_rem.add_argument(
        "--profile",
        choices=PROFILES,
        default="general",
        help="Workflow profile: general, legal70k, news_unified, legacy_mypos_alt (default: general)",
    )
    p_rem.add_argument("--dry-run", action="store_true", help="Preview counts without writing files")
    p_rem.add_argument("--ledger", type=Path, help="Optional TSV path to record every line/stage edit")
    p_rem.add_argument("--record-only-log", type=Path, help="Optional JSONL path for record-only typo leads")
    p_rem.add_argument("--sync-ws-out", type=Path, help="Optional path to export synchronized word-segmented text")

    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if args.command == "chunk":
        res = chunk_corpus_file(args.input, args.outdir, args.chunk_size, args.subchunk_size)
        print(json.dumps({k: v for k, v in res.items() if k != "chunks"}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "merge":
        res = merge_chunks(args.manifest, args.output, args.reference)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    if args.command == "remediate":
        res = stream_remediate_file(
            args.input,
            args.output,
            mode=args.mode,
            profile=args.profile,
            dry_run=args.dry_run,
            ledger_path=args.ledger,
            record_only_path=args.record_only_log,
            sync_ws_path=args.sync_ws_out,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
