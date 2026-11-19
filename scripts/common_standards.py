#!/usr/bin/env python3
"""
Shared linguistic standards, profile schema, and token helpers for myanmar-grammar.

Single source of truth for canonical tagsets, workflow profiles, name prefixes,
titles/ranks, classifiers, time nouns, subsection markers, owner standards,
and POS token parsing/normalization.
"""

from __future__ import annotations

import re

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

PROFILES: tuple[str, ...] = ("general", "legal70k", "news_unified", "legacy_mypos_alt")

_PROFILE_ALIASES: dict[str, str] = {
    "general": "general",
    "legal70k": "legal70k",
    "legal": "legal70k",
    "news_unified": "news_unified",
    "news": "news_unified",
    "unified_modern": "news_unified",
    "legacy_mypos_alt": "legacy_mypos_alt",
    "legacy": "legacy_mypos_alt",
    "mypos_alt": "legacy_mypos_alt",
}


def normalize_profile(
    profile: str | None,
    *,
    default: str = "general",
    allow_auto: bool = False,
) -> str:
    """Validate and normalize a workflow profile name (or alias)."""
    if profile is None or not str(profile).strip():
        return "auto" if (allow_auto and default == "auto") else default
    key = profile.strip().lower()
    if key == "auto":
        return "auto" if allow_auto else default
    if key in _PROFILE_ALIASES:
        return _PROFILE_ALIASES[key]
    valid = ("auto", *PROFILES) if allow_auto else PROFILES
    raise ValueError(f"Unknown profile {profile!r}; expected one of {valid}")


# 19 canonical personal & ethnic name prefixes (union of all repo inventories)
PERSON_PREFIXES: tuple[str, ...] = (
    "ဦး",
    "ဒေါ်",
    "ကို",
    "မ",
    "မောင်",
    "ရှင်",
    "င",
    "စဝ်",
    "စော",
    "နော်",
    "စလိုင်း",
    "ဆလိုင်း",
    "မိုင်း",
    "ဒူဝါ",
    "နိုင်",
    "မန်း",
    "ခွန်",
    "စိုင်း",
    "နန်း",
)

# 9 low-ambiguity prefixes safe for automated split-prefix validation
STRICT_TITLE_PREFIXES: tuple[str, ...] = (
    "ဦး",
    "ဒေါ်",
    "မောင်",
    "စဝ်",
    "စော",
    "နော်",
    "စလိုင်း",
    "ဆလိုင်း",
    "ဒူဝါ",
)

# Official, military, feudal, judicial, academic, and historical titles/ranks (longest-first)
TITLES_AND_RANKS: tuple[str, ...] = tuple(
    sorted(
        {
            "ဒုတိယဗိုလ်ချုပ်ကြီး",
            "ကာကွယ်ရေးဦးစီးချုပ်",
            "ပုပ်ရဟန်းမင်းကြီး",
            "ညွှန်ကြားရေးမှူးချုပ်",
            "တရားလွှတ်တော်ချုပ်",
            "အတွင်းရေးမှူးချုပ်",
            "အမြဲတမ်းအတွင်းဝန်",
            "တရားသူကြီးချုပ်",
            "မဟာဒါန်တိုက်ဝန်",
            "တောင်ဘက်တိုက်ဝန်",
            "လှေသင်းအတွင်းဝန်",
            "အုပ်ချုပ်ရေးမှူး",
            "မြဝတီမင်းကြီး",
            "ကင်းဝန်မင်းကြီး",
            "ညွှန်ကြားရေးမှူး",
            "ဒုတိယသမ္မတ",
            "ဒုတိယဝန်ကြီး",
            "ဒုတိယဥက္ကဋ္ဌ",
            "စစ်ခေါင်းဆောင်",
            "ဗိုလ်ချုပ်ကြီး",
            "ဗိုလ်မှူးချုပ်",
            "ဗိုလ်မှူးကြီး",
            "စစ်ဗိုလ်ချုပ်",
            "စော်ဘွားကြီး",
            "သံအမတ်ကြီး",
            "တရားသူကြီး",
            "စာရင်းစစ်ချုပ်",
            "ပါမောက္ခချုပ်",
            "ယောမင်းကြီး",
            "ရဲမှူးချုပ်",
            "ဝန်ကြီးချုပ်",
            "ရှေ့နေချုပ်",
            "ဦးစီးချုပ်",
            "တပ်ရင်းမှူး",
            "မြို့နယ်မှူး",
            "ဗိုလ်ချုပ်",
            "ဗိုလ်မှူး",
            "ဗိုလ်ကြီး",
            "စော်ဘွား",
            "သံအမတ်",
            "ဒေါက်တာ",
            "ပါမောက္ခ",
            "ဆရာတော်",
            "ဝန်ကြီး",
            "သမ္မတ",
            "ဥက္ကဋ္ဌ",
            "ဗိုလ်",
            "မြို့ဝန်",
            "မြို့စား",
        },
        key=lambda s: (-len(s), s),
    )
)

# 25 true nominal classifiers (tagged `part` / `part:clf` after num/tn)
CLASSIFIERS: tuple[str, ...] = (
    "ဦး",
    "ယောက်",
    "ခု",
    "ရပ်",
    "ပါး",
    "ကြိမ်",
    "မျိုး",
    "စုံ",
    "လုံး",
    "ကောင်",
    "စီး",
    "အုပ်",
    "ထည်",
    "ချပ်",
    "ချောင်း",
    "ဆူ",
    "ပင်",
    "ဖွဲ့",
    "တပ်",
    "သွယ်",
    "ထပ်",
    "ဦးဦး",
    "ခုခု",
    "ရပ်ရပ်",
    "ယောက်ယောက်",
)

# 8 time/measure nouns after numerals (stay `n`, NOT `part:clf`; used for `တ/တစ် -> tn` context)
TIME_MEASURE_NOUNS: tuple[str, ...] = (
    "နှစ်",
    "လ",
    "ရက်",
    "နာရီ",
    "မိနစ်",
    "စက္ကန့်",
    "ပတ်",
    "ရာစု",
)

# 41 Myanmar letters used as parenthetical subsection markers ( က ) / ( ခ ) ...
SUBSECTION_CONSONANTS: frozenset[str] = frozenset(
    "ကခဂဃငစဆဇဈဉညဋဌဍဎဏတထဒဓနပဖဗဘမယရလဝသဟဠအဣဤဥဦဧဩဪ"
)

# 11 Owner fixed-tag exact archaic/standard surfaces
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

# 10 Owner component-standard rows (14 surfaces, ordered longest-first)
OWNER_COMPONENT_STANDARDS_ORDERED: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...] = (
    ("S3_ROW04B", "ပြည်နယ်အစိုးရအဖွဲ့", (("ပြည်နယ်", "n"), ("အစိုးရ", "n"), ("အဖွဲ့", "n"))),
    ("S3_ROW04A", "ပြည်နယ်အစိုးရ", (("ပြည်နယ်", "n"), ("အစိုးရ", "n"))),
    ("S3_ROW01B", "မြန်မာနိုင်ငံတော်", (("မြန်မာ", "n"), ("နိုင်ငံတော်", "n"))),
    ("S3_ROW01A", "မြန်မာနိုင်ငံ", (("မြန်မာ", "n"), ("နိုင်ငံ", "n"))),
    ("S3_ROW02", "ပြည်ထောင်စုအစိုးရ", (("ပြည်ထောင်စု", "n"), ("အစိုးရ", "n"))),
    ("S3_ROW03B", "အစိုးရအဖွဲ့ဝင်", (("အစိုးရ", "n"), ("အဖွဲ့ဝင်", "n"))),
    ("S3_ROW03A", "အစိုးရအဖွဲ့", (("အစိုးရ", "n"), ("အဖွဲ့", "n"))),
    ("S3_ROW05", "အာဏာပိုင်နက်", (("အာဏာ", "n"), ("ပိုင်နက်", "n"))),
    ("S3_ROW06", "ဝန်ကြီးရုံး", (("ဝန်ကြီး", "n"), ("ရုံး", "n"))),
    ("S3_ROW07", "ဘာသာသာသနာ", (("ဘာသာ", "n"), ("သာသနာ", "n"))),
    ("S3_ROW08", "စီးပွားရေးစနစ်", (("စီးပွားရေး", "n"), ("စနစ်", "n"))),
    ("S3_ROW09", "သယံဇာတပစ္စည်း", (("သယံဇာတ", "n"), ("ပစ္စည်း", "n"))),
    ("S3_ROW10A", "ရေပေါ်ရေအောက်", (("ရေပေါ်", "n"), ("ရေအောက်", "n"))),
    ("S3_ROW10B", "မြေပေါ်မြေအောက်", (("မြေပေါ်", "n"), ("မြေအောက်", "n"))),
)

OWNER_COMPONENT_STANDARDS: dict[str, list[tuple[str, str]]] = {
    surface: list(parts) for _rule_id, surface, parts in OWNER_COMPONENT_STANDARDS_ORDERED
}

RECORD_ONLY_LEADS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("LEAD_01", re.compile(r"စည်းမျည်း"), "စည်းမျဉ်း"),
    ("LEAD_02", re.compile(r"စေကာမှု"), "စေကာမူ"),
    ("LEAD_03", re.compile(r"ပြည်ထ(?:ယ်|ာင်)စု"), "ပြည်ထောင်စု"),
    ("LEAD_04", re.compile(r"အံဆဲဆဲ"), "အံ့ဆဲဆဲ"),
    ("LEAD_05", re.compile(r"ပြီးလျင်"), "ပြီးလျှင်"),
    ("LEAD_06", re.compile(r"ပြည်နယ်(?:/[a-z]+)?\s+ကော်စီ"), "ပြည်နယ် ကောင်စီ"),
    ("LEAD_07", re.compile(r"ကျင့်ဝပ်(?:/[a-z]+)?\s+သိက္ခာ"), "ကျင့်ဝတ် သိက္ခာ"),
    ("LEAD_08", re.compile(r"ပြဿ(?:/[a-z]+)?\s+သို့(?:/[a-z]+)?\s+ကို"), "ပြဿနာကို"),
)

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
_UNESCAPE_RE = re.compile(r"\\([\\/])")


def strip_ws(line: str, normalize: bool = False) -> str:
    """Strip whitespace and optionally normalize zero-width chars and canonical codepoints."""
    t = re.sub(r"\s+", "", line)
    if normalize:
        t = _ZERO_WIDTH_RE.sub("", t)
        t = t.replace("\u1005\u103b", "\u1008").replace("\u1025\u102e", "\u1026")
        t = t.replace("\u103a\u1037", "\u1037\u103a")
    return t


def parse_pos_token(
    tok: str,
    *,
    allowed_tags: frozenset[str] | None = None,
) -> tuple[str, str] | None:
    """Parse a flat 'word/tag' token using the last unescaped '/' delimiter."""
    if not tok:
        return None
    idx = tok.rfind("/")
    if idx <= 0 or idx == len(tok) - 1:
        return None
    prefix = tok[:idx]
    tag = tok[idx + 1 :]
    if not tag or any(ch.isspace() for ch in tag):
        return None
    j = idx - 1
    bs_count = 0
    while j >= 0 and tok[j] == "\\":
        bs_count += 1
        j -= 1
    if bs_count % 2 == 1:
        return None
    surface = _UNESCAPE_RE.sub(r"\1", prefix)
    if allowed_tags is not None and tag not in allowed_tags:
        return None
    return surface, tag
