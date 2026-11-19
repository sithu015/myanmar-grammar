#!/usr/bin/env python3
"""
myPOS-HD (Hierarchical Dual-Layer v4.1) Additive Projector & UPOS Bridge

Losslessly projects canonical 15-tag Myanmar POS sequences into:
  - mypos15: Canonical lowercase 15-tag (base = collapse_to_mypos15(mypos_hd))
  - mypos_hd: Hierarchical `base:sub` annotation resolving functional collisions
  - mypos_core: Expanded flat syntactic tagset (`propn`, `aux`, `clf`, `neg`, `nom`, `rel`, `sfp`, `cconj`, `sconj`, `det`)
  - upos / feats: Universal Dependencies v2 mapping across all 15 base tags

Supports both corpus profiles observed in 9.64M-token cross-corpus audits:
  - `unified_modern`: News 70k, Shan Yoma v2.15+, Legal L3k+ (verb-final = `part`)
  - `legacy_mypos_alt`: myPOS+myALT+myMediCon, Legal L1-2k (verb-final `သည်/တယ်/မည်/မယ်/၏` = `ppm`)

Usage:
  python3 scripts/project_mypos_hd.py --self-test
  python3 scripts/project_mypos_hd.py --input corpus_pos.txt --mode pos --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

try:
    from .common_standards import (
        ALLOWED_15_TAGS,
        CLASSIFIERS,
        PERSON_PREFIXES,
        PROFILES,
        STRICT_TITLE_PREFIXES,
        TITLES_AND_RANKS,
        normalize_profile,
        parse_pos_token,
    )
except ImportError:
    _scripts_dir = str(Path(__file__).resolve().parent)
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)
    from common_standards import (
        ALLOWED_15_TAGS,
        CLASSIFIERS,
        PERSON_PREFIXES,
        PROFILES,
        STRICT_TITLE_PREFIXES,
        TITLES_AND_RANKS,
        normalize_profile,
        parse_pos_token,
    )

ALLOWED_HD_TAGS: frozenset[str] = frozenset(
    {
        "n",
        "n:prop",
        "n:gen",
        "n:rel",
        "pron",
        "pron:dem",
        "pron:gen",
        "v",
        "v:stat",
        "adj",
        "adj:det",
        "adj:ord",
        "adv",
        "ppm",
        "ppm:subj",
        "ppm:obj",
        "ppm:obl",
        "ppm:gen",
        "ppm:fin",
        "part",
        "part:neg",
        "part:aux",
        "part:clf",
        "part:ord",
        "part:nom",
        "part:rel",
        "part:sfp",
        "part:quot",
        "part:pl",
        "part:approx",
        "part:quant",
        "part:foc",
        "conj",
        "conj:coord",
        "conj:sub",
        "conj:purp",
        "conj:disc",
        "num",
        "num:latn",
        "tn",
        "abb",
        "fw",
        "int",
        "punc",
        "sb",
        "sb:enum",
    }
)

# Complete Base-15 -> Universal Dependencies v2 (UPOS, default FEATS)
BASE15_TO_UPOS: dict[str, tuple[str, str]] = {
    "n": ("NOUN", "_"),
    "pron": ("PRON", "_"),
    "v": ("VERB", "_"),
    "adj": ("ADJ", "_"),
    "adv": ("ADV", "_"),
    "ppm": ("ADP", "_"),
    "part": ("PART", "_"),
    "conj": ("CCONJ", "_"),
    "num": ("NUM", "NumType=Card"),
    "tn": ("NUM", "NumType=Card"),
    "int": ("INTJ", "_"),
    "punc": ("PUNCT", "_"),
    "abb": ("NOUN", "Abbr=Yes"),
    "fw": ("X", "Foreign=Yes"),
    "sb": ("SYM", "_"),
}

AUX_SET = {
    "နိုင်", "ရ", "စေ", "သင့်", "ထိုက်", "အပ်", "ပိုင်", "တတ်", "ခဲ့", "နေ", "ထား",
    "ပြီး", "ပေး", "သွား", "လာ", "လိုက်", "မိ", "ချင်", "တော်မူ", "ဘိ", "လေ",
    "ချေ", "ပြန်", "ဦး", "အံ့", "ဖူး", "လင့်",
}
CLF_SET = set(CLASSIFIERS)
ORD_PRECEDING_SET = {
    "ကြိမ်", "အကြိမ်", "ခု", "နှစ်", "ဆင့်", "အဆင့်", "ယောက်", "ဦး", "ရက်", "လ", "ပတ်", "ထပ်",
}
NEG_POST_SET = {"ဘူး", "ချေ", "ဘဲ", "ပဲ", "နဲ့", "လင့်"}
NOM_SET = {"ခြင်း", "မှု", "ခွင့်", "ရာ", "ချက်"}
REL_SET = {"သော", "သည့်", "မည့်", "တဲ့", "မယ့်"}
SFP_SET = {
    "သည်", "မည်", "၏", "ပြီ", "လိမ့်မည်", "သတည်း", "တည်း", "လေ", "ချေ",
    "တကား", "တုံ", "အံ့", "တယ်", "မယ်", "ပါ", "စို့", "သနည်း", "ပေါ့",
}
FIN_PPM_COPULA_SET = {"သည်", "မည်", "တယ်", "မယ်", "၏", "ပြီ", "စို့", "သနည်း"}
QUOT_SET = {"ဟု", "ဟူ၍", "ဟူသော", "ဟူသည်", "ဟူသမျှ"}
PLURAL_SET = {"များ", "တို့"}
APPROX_SET = {"ခန့်", "လောက်", "နီးပါး", "ကျော်"}
QUANT_SET = {"တိုင်း", "စီ", "လုံး", "စလုံး"}
FOCUS_PART_SET = {"သာ", "လည်း", "ပင်", "မျှ", "တော့", "ကား", "မူ", "တည်းဟူသော", "ပဲ", "တည်း", "ထည်း", "တည်"}

PPM_SUBJ = {"သည်", "က", "မှာ", "ဟာ"}
PPM_OBJ = {"ကို", "အား"}
PPM_GEN = {"၏", "ရဲ့"}
PPM_OBL = {"တွင်", "၌", "မှ", "သို့", "ဖြင့်", "နှင့်", "နဲ့", "ကြောင့်", "အတွက်", "အရ", "ထက်", "ထံ", "မို့"}

SCONJ_SET = {
    "၍", "သဖြင့်", "သောကြောင့်", "သော်လည်း", "သော်", "လျှင်", "ပါက", "က",
    "စေကာမူ", "ပြီးနောက်", "ပြီးလျှင်", "တုန်းက", "သောအခါ", "သည့်အခါ",
    "သည့်တိုင်အောင်", "သရွေ့", "သမျှ", "မတိုင်မီ", "သကဲ့သို့", "ကာ", "ပေမယ့်", "ရင်",
}
PURP_SET = {"ရန်", "အောင်"}
CCONJ_SET = {
    "နှင့်", "နဲ့", "သို့မဟုတ်", "သို့တည်းမဟုတ်", "သော်လည်းကောင်း", "သော်၎င်း",
    "လည်းကောင်း", "ဖြစ်စေ", "ဝါ",
}
DISC_CONJ_SET = {
    "ထို့ကြောင့်", "သို့ဖြစ်၍", "သို့ဖြစ်ပါ၍", "သို့ရာတွင်", "သို့သော်",
    "ထို့ပြင်", "ထို့အပြင်", "ထို့နောက်", "သို့မဟုတ်ပါက", "သို့နှင့်",
    "ဒါပေမယ့်", "ဒါပေမဲ့", "သို့ပေမယ့်", "သို့ပေမဲ့",
}

DET_SET = {"ဤ", "ထို", "ယင်း", "အဆိုပါ", "၎င်း", "ဒီ", "အဲဒီ", "မည်သည့်", "ဟို", "ဘယ်"}
PALI_ORD_SET = {
    "ပထမ", "ပဌမ", "ဒုတိယ", "တတိယ", "စတုတ္ထ", "ပဉ္စမ", "ဆဋ္ဌမ", "သတ္တမ", "အဋ္ဌမ",
    "နဝမ", "ဒသမ", "ဧကဒသမ", "ဧကာဒသမ", "ဒွါဒသမ", "တေရသမ", "စုဒ္ဒသမ", "ပန္နရသမ",
    "ပဉ္စဒသမ", "သောဠသမ", "သတ္တရသမ", "အဋ္ဌာရသမ", "ဧကူနဝီသတိမ", "ဝီသတိမ", "ပထမဆုံး",
}
STATIVE_SET = {
    "လွယ်ကူ", "ခက်ခဲ", "ကြီးမား", "ကောင်းမွန်", "လွတ်လပ်", "တရားမျှတ",
    "ညီမျှ", "ခိုင်မြဲ", "ငြိမ်းချမ်း", "လှပ", "မြင့်မား", "ရှင်းလင်း", "ရဲရင့်",
}
RELATIONAL_N_SET = {"အတွင်း", "အပေါ်", "အောက်", "အကြား", "အနက်", "အနီး", "အထဲ", "ထံ", "အတိုင်း"}

# Strictly valid Burmese creaky-tone (\u1037) inflected genitive/oblique whitelists.
# Never includes words with native heavy-tone \u1038 + \u1037 (e.g., no မင်း့/အမျိုးသမီး့)
# and never uses a naive \u1037$ regex (which wrongly captures lexical မြို့/နေ့/ဘွဲ့/တို့).
CREAKY_GEN_NOUN_SET = {
    "မြန်မာ့", "နိုင်ငံ့", "ပြည်သူ့", "သာသနာ့", "စေတနာ့", "ကမ္ဘာ့",
    "ဘုရင့်", "မင့်", "အဖေ့", "အမေ့", "မိခင့်", "ဖခင့်", "အရှင့်", "ပညာ့", "ဘုရာ့",
}
CREAKY_GEN_PRON_SET = {"သူ့", "ငါ့", "မည်သူ့", "ကျွန်တော့်", "ကိုယ့်"}

NON_PERSON_LEXICAL = {
    "ဦးရေ", "ဦးစီး", "ဦးဆောင်", "ဦးထုပ်", "ဦးတည်", "ဦးနှောက်", "ဦးခေါင်း", "ဦးစွာ", "ဦးပိုင်", "ဦးချို",
    "ဦးလေး", "ဦးလေးကြီး", "ဦးပဉ္စင်းကြီး", "ဦးစေတီကြီး", "ဦးစေတီတော်ကြီး", "ဦးလူကြီး",
    "ဒေါ်လာ", "ကိုယ်", "ကိုယ်တိုင်", "ကိုယ်စား", "ကိုယ်ပိုင်", "မိဘ", "မဟာ", "မင်း", "မင်းကြီး",
    "မောင်နှမ", "မောင်တော်", "စောင့်", "စောစော", "စောစီး", "စောဒက", "စောဒနာ",
    "စောဒနာဝင်", "စောဒနာလွှာ", "စောင်းတန်း", "နော်ဝေ", "ရှင်ဘုရင်", "ခွန်အား",
    "ကျူးကျော်သူ", "အခြေအနေမျိုး", "အနေမျိုး", "ဦးဆုံး", "ဦးနှုန်း", "ဒေါ်ဒေါ်",
    "မဟာသင်္ကြံ", "သင်္ကြံပွဲ",
}
NON_PERSON_STEM_PREFIXES = (
    "ဦးစီး", "ဦးဆောင်", "ဦးတည်", "ဦးနှောက်", "ဦးခေါင်း", "ဦးထုပ်", "ဦးရေ",
    "ဦးစား", "ဦးပိုင်", "ဦးချို", "ဦးလေး", "ဦးပဉ္စင်း", "ဦးစေတီ", "ဦးလူကြီး",
    "ဦးပေါင်း", "ဦးသျှောင်", "ဦးစာရင်း", "ဦးစွာ", "ဦးဦး",
    "ဒေါ်လာ", "မောင်နှမ", "မောင်နှံ", "မောင်တော်", "မောင်တော",
    "စောစော", "စောစီး", "စောင့်", "စောဒက", "စောဒနာ", "စောမုတ်သုန်",
    "နော်ဝေ",
    "ကျူးကျော်", "အခြေအနေ", "မဟာသင်္ကြံ", "ဦးဆုံး", "ဦးနှုန်း", "ဇွဲ",
    "ဦးမည်", "ဦးဖြစ်", "ဦးမည်ဖြစ်", "မောင်ဖြစ်", "နိုင်ရှာ", "နိုင်တော့",
)
NON_PERSON_SUFFIXES = (
    "တော်", "ချုပ်", "ဝန်", "မှူး", "ရေး", "မှု", "ခြင်း", "ခွင့်", "ချက်", "နိုင်ငံ",
    "ဌာန", "ရုံး", "အဖွဲ့", "ကော်မတီ", "ကော်မရှင်", "စျေး", "ဈေး", "စနစ်", "ပစ္စည်း",
    "များ", "တို့", "စွာ", "စီး", "ဥပဒေ", "ပုဒ်မ", "စာရင်း", "သတင်း", "တက္ကသိုလ်", "ဆေးရုံ",
    "သောကြောင့်", "တော့ဘဲ", "တော့ပဲ", "ပေ", "လေ", "သော်လည်း", "ပါသလား", "ခဲ့", "ပြီ", "ရှာ",
    "မည်", "ဖြစ်", "တော့", "ပါ", "သော", "ပုံ", "ဘွယ်", "လျက်", "ကာ",
)
ROYAL_TITLE_MARKERS = ("နေမျိုး", "သင်္ခယာ", "ကျော်ထင်", "ကျော်သူ", "သိင်္ခသူ", "တရဖျား", "နော်ရထာ", "သီဟသူ", "သင်္ကြံ")
MONARCH_SOBRIQUETS = {
    "မင်းတုန်းမင်း", "သီပေါမင်း", "ပုဂံမင်း", "သာယာဝတီမင်း", "ရွှေဘိုမင်း", "စစ်ကိုင်းမင်း",
    "ကနောင်မင်း", "တောင်ငူမင်း", "ပြည်မင်း", "စလင်းမင်း", "ရမည်းသင်းမင်း", "ပုခန်းမင်း",
    "မိုးမိတ်မင်း", "မင်းကြီးဖြူ", "မဟာသမ္မတမင်း", "အလောင်းမင်းတရားကြီး"
}
ASCII_NUM_RE = re.compile(r"^[0-9]+([.,:/-][0-9]+)*$")


def collapse_to_mypos15(hd_tag: str) -> str:
    """Losslessly recover the canonical Base-15 tag from any myPOS-HD tag."""
    if hd_tag == "num:latn":
        return "num"
    return hd_tag.split(":", 1)[0]


def _is_person_or_royal_propn(word: str, prop_set: set[str]) -> bool:
    if word in prop_set or word in MONARCH_SOBRIQUETS:
        return True
    if word in NON_PERSON_LEXICAL or word in TITLES_AND_RANKS:
        return False
    if word.startswith(("ကိုင်", "ကိုက်", "ကိုယ်", "ကိုယ့်", "ကိုင်း")):
        return False
    if word.startswith(("ကိုင်", "ကိုက်", "ကိုယ်", "ကိုယ့်", "ကိုင်း")):
        return False
    if word.startswith(NON_PERSON_STEM_PREFIXES):
        return False
    if word.endswith(NON_PERSON_SUFFIXES):
        return False
    if word.endswith(("သည်", "မှာ", "က", "ကို", "နှင့်", "နဲ့", "အား", "တွင်", "၌", "သို့", "ဖြင့်")):
        return False
    if word.startswith("နိုင်") and word not in prop_set:
        return False
    if word in prop_set:
        return True
    if any(m in word for m in ROYAL_TITLE_MARKERS):
        return True
    HD_PROP_PREFIXES = STRICT_TITLE_PREFIXES + ("စိုင်း", "ခွန်", "နန်း", "မိုင်း", "မန်း")
    for p in HD_PROP_PREFIXES:
        if word.startswith(p) and len(word) > len(p):
            rest = word[len(p):]
            # Must begin a new syllable (consonant/independent vowel), not a combining mark
            if not ("\u1000" <= rest[0] <= "\u102a"):
                continue
            if len(rest) > 1 and rest[1] == "\u103a":
                continue
            # Reject bare kinship/adverbial prefix+ကြီး (ဦးကြီး, ဒေါ်ကြီး, စောကြီး)
            if rest == "ကြီး":
                continue
            if len(rest) > 1 or word in {"ဦးစ", "ဦးဘ", "ဦးဩ", "ဒေါ်ဦး", "စောဘ"}:
                return True
    return False


def project_sentence_to_mypos_hd(
    tokens_with_pos: list[tuple[str, str]],
    proper_nouns: Iterable[str] = (),
    profile: str = "auto",
) -> list[dict[str, str]]:
    """Project (word, base15_tag) sequence into multi-tier myPOS-HD v4.1 dictionaries."""
    profile = normalize_profile(profile, default="auto", allow_auto=True)
    prop_set = set(proper_nouns)
    n_toks = len(tokens_with_pos)
    results: list[dict[str, str]] = []
    seen_neg_ma = False

    for i, (w, tag) in enumerate(tokens_with_pos):
        prev_w, prev_t = tokens_with_pos[i - 1] if i > 0 else ("", "")
        next_w, next_t = tokens_with_pos[i + 1] if i + 1 < n_toks else ("", "")

        if w in ("။", "၊", ",", ".") or tag == "conj":
            seen_neg_ma = False

        upos, feats = BASE15_TO_UPOS.get(tag, ("X", "_"))
        hd_tag = tag
        core_tag = tag

        if tag == "part":
            if w == "မ" and next_t in {"v", "adj", "part"}:
                seen_neg_ma = True
                hd_tag, core_tag, upos, feats = "part:neg", "neg", "PART", "Polarity=Neg|Position=Pre"
            elif w in NEG_POST_SET and prev_t in {"v", "part", "adj"} and (w in {"ဘဲ", "နဲ့", "လင့်"} or seen_neg_ma):
                hd_tag, core_tag, upos, feats = "part:neg", "neg", "PART", "Polarity=Neg|Position=Post"
            elif w in CLF_SET and prev_t in {"num", "tn"}:
                hd_tag, core_tag, upos, feats = "part:clf", "clf", "NOUN", "NounType=Clf"
            elif w == "မြောက်" and prev_w in ORD_PRECEDING_SET and prev_t in {"part", "n"}:
                hd_tag, core_tag, upos, feats = "part:ord", "part", "PART", "NumType=Ord"
            elif w == "သည်" and prev_t in {"v", "part"} and next_t == "ppm":
                hd_tag, core_tag, upos, feats = "part:nom", "nom", "SCONJ", "VerbForm=Vnoun"
            elif w in NOM_SET and prev_t in {"v", "part", "adj"}:
                hd_tag, core_tag, upos, feats = "part:nom", "nom", "PART", "VerbForm=Vnoun"
            elif w in REL_SET and prev_t in {"v", "part", "adj"}:
                hd_tag, core_tag, upos, feats = "part:rel", "rel", "SCONJ", "VerbForm=Part"
            elif w in QUOT_SET:
                hd_tag, core_tag, upos, feats = "part:quot", "part", "PART", "PartType=Quot"
            elif w == "သော်":
                hd_tag, core_tag, upos, feats = "conj:sub", "sconj", "SCONJ", "VerbForm=Conv"
            elif w in SFP_SET and (next_t in {"punc", ""} or next_w in QUOT_SET):
                hd_tag, core_tag, upos, feats = "part:sfp", "sfp", "PART", "Mood=Ind"
            elif w in AUX_SET and prev_t in {"v", "part"}:
                hd_tag, core_tag, upos, feats = "part:aux", "aux", "AUX", "VerbForm=Fin"
            elif w in PLURAL_SET:
                hd_tag, core_tag, upos, feats = "part:pl", "part", "PART", "Number=Plur"
            elif w in APPROX_SET:
                hd_tag, core_tag, upos, feats = "part:approx", "part", "PART", "NumType=Approx"
            elif w in QUANT_SET:
                hd_tag, core_tag, upos, feats = "part:quant", "part", "PART", "_"
            elif w in FOCUS_PART_SET:
                hd_tag, core_tag, upos, feats = "part:foc", "part", "PART", "_"
            elif w in PURP_SET and prev_t in {"v", "part"}:
                hd_tag, core_tag, upos, feats = "conj:purp", "sconj", "SCONJ", "_"

        elif tag == "ppm":
            # Support legacy myPOS+ALT / Legal L1-2k `pos_copula_ppm` profile transparently
            is_verbal_fin = (
                profile == "legacy_mypos_alt"
                or (profile == "auto" and prev_t in {"v", "part"} and (next_t in {"punc", ""} or next_w in QUOT_SET))
                or (w == "၏" and (next_t in {"punc", ""} or next_w in {"။", "၊"}))
            )
            if is_verbal_fin and w in FIN_PPM_COPULA_SET and (prev_t in {"v", "part"} or w == "၏"):
                hd_tag, core_tag, upos, feats = "ppm:fin", "sfp", "PART", "Mood=Ind"
            elif w == "မူ" and (prev_w in {"မ", "တော်မ", "လိုက်မ", "မဖြစ်"} or (prev_t in {"part", "v"} and next_w == "မီ")):
                hd_tag, core_tag, upos, feats = "part:aux", "part", "PART", "_"
            elif w in PPM_SUBJ:
                hd_tag, core_tag, upos, feats = "ppm:subj", "ppm", "ADP", "Case=Nom"
            elif w in PPM_OBJ:
                hd_tag, core_tag, upos, feats = "ppm:obj", "ppm", "ADP", "Case=Acc"
            elif w in PPM_GEN:
                hd_tag, core_tag, upos, feats = "ppm:gen", "ppm", "ADP", "Case=Gen"
            elif w in PPM_OBL:
                hd_tag, core_tag, upos, feats = "ppm:obl", "ppm", "ADP", "Case=Loc"

        elif tag == "n":
            if w in CREAKY_GEN_NOUN_SET and next_t in {"n", "ppm", "adj", "part", "v"}:
                hd_tag, core_tag, upos, feats = "n:gen", "n", "NOUN", "Case=Gen"
            elif _is_person_or_royal_propn(w, prop_set):
                hd_tag, core_tag, upos, feats = "n:prop", "propn", "PROPN", "_"
            elif w in RELATIONAL_N_SET:
                hd_tag, core_tag, upos, feats = "n:rel", "n", "NOUN", "NounType=Rel"

        elif tag == "pron":
            if w in CREAKY_GEN_PRON_SET and next_t in {"n", "ppm", "adj", "part", "v"}:
                hd_tag, core_tag, upos, feats = "pron:gen", "pron", "PRON", "Case=Gen"
            elif w in DET_SET or w in {"၎င်း", "ဒါ", "အဲဒါ"}:
                if next_t == "n":
                    hd_tag, core_tag, upos, feats = "adj:det", "det", "DET", "PronType=Dem"
                else:
                    hd_tag, core_tag, upos, feats = "pron:dem", "pron", "PRON", "PronType=Dem"

        elif tag == "v":
            if w in STATIVE_SET:
                hd_tag, core_tag, upos, feats = "v:stat", "v", "ADJ", "_"

        elif tag == "adj":
            if w in DET_SET:
                hd_tag, core_tag, upos, feats = "adj:det", "det", "DET", "PronType=Dem"
            elif w in PALI_ORD_SET:
                hd_tag, core_tag, upos, feats = "adj:ord", "adj", "ADJ", "NumType=Ord"

        elif tag == "conj":
            if w in DISC_CONJ_SET:
                hd_tag, core_tag, upos, feats = "conj:disc", "sconj", "ADV", "_"
            elif w in PURP_SET:
                hd_tag, core_tag, upos, feats = "conj:purp", "sconj", "SCONJ", "_"
            elif w in SCONJ_SET:
                hd_tag, core_tag, upos, feats = "conj:sub", "sconj", "SCONJ", "VerbForm=Conv"
            elif w in CCONJ_SET:
                hd_tag, core_tag, upos, feats = "conj:coord", "cconj", "CCONJ", "_"
            elif prev_t in {"v", "part"}:
                hd_tag, core_tag, upos, feats = "conj:sub", "sconj", "SCONJ", "_"
            else:
                hd_tag, core_tag, upos, feats = "conj:coord", "cconj", "CCONJ", "_"

        elif tag == "fw" and ASCII_NUM_RE.match(w):
            hd_tag, core_tag, upos, feats = "num:latn", "num", "NUM", "NumType=Card|Script=Latn"

        elif tag == "abb":
            if w in prop_set:
                hd_tag, core_tag, upos, feats = "abb", "abb", "PROPN", "Abbr=Yes"

        elif tag == "sb":
            if prev_w == "(" and next_w == ")":
                hd_tag, core_tag, upos, feats = "sb:enum", "sb", "SYM", "_"

        results.append(
            {
                "word": w,
                "mypos15": collapse_to_mypos15(hd_tag),
                "mypos_hd": hd_tag,
                "mypos_core": core_tag,
                "upos": upos,
                "feats": feats,
            }
        )

    return results


def _parse_pos_line(line: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for tok in line.split():
        parsed = parse_pos_token(tok)
        if parsed is not None:
            pairs.append(parsed)
    return pairs


def run_self_test() -> int:
    # 1. Unified modern sentence + proper name prefix + affirmative ပဲ vs negative မ...ပဲ
    s1 = _parse_pos_line("ဦးစ/n သည်/ppm ကောင်း/v တာ/part ပဲ/part ။/punc မ/part သွား/v ပဲ/part နေ/part ခဲ့/part သည်/part ။/punc")
    hd1 = project_sentence_to_mypos_hd(s1, proper_nouns={"ဦးစ"})
    assert hd1[0]["mypos_hd"] == "n:prop" and hd1[0]["upos"] == "PROPN"
    assert hd1[1]["mypos_hd"] == "ppm:subj" and hd1[1]["upos"] == "ADP"
    assert hd1[4]["mypos_hd"] == "part:foc" and hd1[4]["feats"] == "_"  # affirmative ပဲ MUST NOT be neg
    assert hd1[6]["mypos_hd"] == "part:neg"
    assert hd1[8]["mypos_hd"] == "part:neg"  # မ ... ပဲ inside same clause IS neg
    assert hd1[11]["mypos_hd"] == "part:sfp"

    # 2. Legacy mypos_alt profile (verb-final ppm) + creaky trap guard (မြို့ vs မြန်မာ့) + approx vs plur
    s2 = _parse_pos_line("မြို့/n တွင်/ppm မြန်မာ့/n လူ/n ၅/num နာရီ/n ခန့်/part များ/part ဖြစ်/v သည်/ppm ။/punc")
    hd2 = project_sentence_to_mypos_hd(s2, profile="legacy_mypos_alt")
    assert hd2[0]["mypos_hd"] == "n"  # မြို့ MUST NOT become n:gen
    assert hd2[2]["mypos_hd"] == "n:gen" and hd2[2]["feats"] == "Case=Gen"
    assert hd2[6]["mypos_hd"] == "part:approx" and hd2[6]["feats"] != "Number=Plur"
    assert hd2[7]["mypos_hd"] == "part:pl" and hd2[7]["feats"] == "Number=Plur"
    assert hd2[9]["mypos_hd"] == "ppm:fin" and hd2[9]["upos"] == "PART"
    assert collapse_to_mypos15("ppm:fin") == "ppm"

    # 3. Complete Base-15 UPOS coverage (no accidental fallthrough to X) + num:latn collapse + rel vs nom
    s3 = _parse_pos_line("100/fw ကောင်း/v ၍/conj ဆောင်ရွက်/v ခြင်း/part သော/part (/punc က/sb )/punc အမလေး/int ။/punc")
    hd3 = project_sentence_to_mypos_hd(s3)
    assert hd3[0]["mypos_hd"] == "num:latn" and hd3[0]["mypos15"] == "num" and hd3[0]["upos"] == "NUM"
    assert hd3[2]["mypos_hd"] == "conj:sub" and hd3[2]["upos"] == "SCONJ"
    assert hd3[4]["mypos_hd"] == "part:nom" and hd3[4]["mypos_core"] == "nom"
    assert hd3[5]["mypos_hd"] == "part:rel" and hd3[5]["mypos_core"] == "rel"
    assert hd3[7]["mypos_hd"] == "sb:enum" and hd3[7]["upos"] == "SYM"
    assert hd3[9]["upos"] == "INTJ" and hd3[10]["upos"] == "PUNCT"

    # 4. Royal title marker false positive guards vs genuine royal/personal names
    s4 = _parse_pos_line("ကျူးကျော်သူ/n အခြေအနေမျိုး/n ဦးဆုံး/n နေမျိုးသီဟသူ/n ဦးကျော်သူ/n")
    hd4 = project_sentence_to_mypos_hd(s4)
    assert hd4[0]["mypos_hd"] == "n" and hd4[0]["upos"] == "NOUN"
    assert hd4[1]["mypos_hd"] == "n" and hd4[1]["upos"] == "NOUN"
    assert hd4[2]["mypos_hd"] == "n" and hd4[2]["upos"] == "NOUN"
    assert hd4[3]["mypos_hd"] == "n:prop" and hd4[3]["upos"] == "PROPN"
    assert hd4[4]["mypos_hd"] == "n:prop" and hd4[4]["upos"] == "PROPN"

    print("SELF-TEST PASSED: myPOS-HD v4.1 (all 15 base tags, Dual-Profile, clause-bounded neg/foc, valid creaky genitives, approx/plur split, rel/nom split, lossless collapse) verified.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Project 15-tag Myanmar POS text into myPOS-HD v4.1 and UD v2.")
    parser.add_argument("--input", type=Path, help="Input POS file (`word/tag` per line) or JSONL (`tokens`, `pos_tags`)")
    parser.add_argument("--mode", choices=["pos", "jsonl"], default="pos", help="Input format")
    parser.add_argument(
        "--profile",
        choices=["auto", "unified_modern", *PROFILES],
        default="auto",
    )
    parser.add_argument("--limit", type=int, default=20, help="Max lines to emit")
    parser.add_argument("--json", action="store_true", help="Emit JSON lines")
    parser.add_argument("--self-test", action="store_true", help="Run built-in unit self-tests")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if not args.input or not args.input.is_file():
        parser.error("--input is required unless --self-test is given.")

    with args.input.open(encoding="utf-8") as f:
        for idx, raw in enumerate(f, 1):
            if idx > args.limit:
                break
            raw = raw.rstrip("\r\n")
            if args.mode == "jsonl":
                obj = json.loads(raw)
                pairs = list(zip(obj.get("tokens", []), obj.get("pos_tags", [])))
            else:
                pairs = _parse_pos_line(raw)
            projected = project_sentence_to_mypos_hd(pairs, profile=args.profile)
            if args.json:
                print(json.dumps({"line": idx, "tokens": projected}, ensure_ascii=False))
            else:
                print(" ".join(f"{r['word']}/{r['mypos_hd']}" for r in projected))
    return 0


if __name__ == "__main__":
    sys.exit(main())
