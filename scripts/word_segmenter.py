#!/usr/bin/env python3
"""
tools/word_segmenter.py — Myanmar Word Segmentation & Tokenization Engine.

Uses recovered TTKeyboard dictionary lexicon (13,421 vocabulary entries)
combined with Syllable-Constrained Maximum Matching (Forward & Backward)
and Unigram Frequency Ranking.
"""

import os
import sys
from typing import List, Tuple, Dict, Optional

# Import syllable breaker
try:
    from .syllable_breaker import SyllableBreaker
except ImportError:
    from syllable_breaker import SyllableBreaker


# Closed owner forms. Rejoin these before any shorter row is allowed to cut them.
_PROTECTED_WHOLE = frozenset({
    "မြန်မာနိုင်ငံသား",
    "သာသနာရေး",
    "နှလုံးသား",
    "သဖြင့်",
    "ပြဿနာ",
    "အန္တရာယ်",
    "ဒေါသ",
    "ရာပေါင်းများစွာ",
    "ထောင်ပေါင်းများစွာ",
    "သန်းပေါင်းများစွာ",
    "ဘီလီယံပေါင်းများစွာ",
    "နှစ်ပေါင်းများစွာ",
    "လပေါင်းများစွာ",
    "ရက်ပေါင်းများစွာ",
    "ဒါဇင်ပေါင်းများစွာ",
    "ရာစုနှစ်ပေါင်းများစွာ",
    "ဦးမင်းအောင်လှိုင်",
    "ဒေါ်အောင်ဆန်းစုကြည်",
    "ဦးကျော်မိုးထွန်း",
    "စဝ်စံထွန်း",
    "ကိုမင်းကိုနိုင်",
    "မသီရိစိုး",
    "စောဘဦးကြီး",
    "စောမုတ်သုန်",
    "နော်စီဖိုးရာစိန်",
    "စလိုင်းတင်မောင်ဦး",
    "နိုင်ရွှေကျင်",
    "တကျွန်း",
    "သံအမတ်ကြီး",
    "ဗိုလ်ချုပ်ကြီး",
    "စော်ဘွားကြီး",
    "ဝန်ကြီးချုပ်",
    "တရားသူကြီးချုပ်",
    "ကောဇာ",
    "သက္ကရာဇ်",
    "လဆန်း",
    "လဆုတ်",
    "လပြည့်",
    "လပြည့်ကျော်",
    "လကွယ်",
    "အဖိတ်နေ့",
    "ဥပုသ်နေ့",
    "ဗုဒ္ဓဟူး",
})

# Exact-token splits. Longer surfaces first.
_EXACT_SPLITS = [
    ("ကောဇာသက္ကရာဇ်", ["ကောဇာ", "သက္ကရာဇ်"]),
    ("တန်ဆောင်မုန်းလဆုတ်", ["တန်ဆောင်မုန်း", "လဆုတ်"]),
    ("တန်ဆောင်မုန်းလဆန်း", ["တန်ဆောင်မုန်း", "လဆန်း"]),
    ("တန်ဆောင်မုန်းလပြည့်", ["တန်ဆောင်မုန်း", "လပြည့်"]),
    ("တန်ဆောင်မုန်းလကွယ်", ["တန်ဆောင်မုန်း", "လကွယ်"]),
    ("နတ်တော်လဆုတ်", ["နတ်တော်", "လဆုတ်"]),
    ("နတ်တော်လဆန်း", ["နတ်တော်", "လဆန်း"]),
    ("နတ်တော်လပြည့်", ["နတ်တော်", "လပြည့်"]),
    ("နတ်တော်လကွယ်", ["နတ်တော်", "လကွယ်"]),
    ("တန်ခူးလဆုတ်", ["တန်ခူး", "လဆုတ်"]),
    ("တန်ခူးလဆန်း", ["တန်ခူး", "လဆန်း"]),
    ("ကဆုန်လဆုတ်", ["ကဆုန်", "လဆုတ်"]),
    ("ကဆုန်လဆန်း", ["ကဆုန်", "လဆန်း"]),
    ("နယုန်လဆုတ်", ["နယုန်", "လဆုတ်"]),
    ("နယုန်လဆန်း", ["နယုန်", "လဆန်း"]),
    ("ဝါဆိုလဆုတ်", ["ဝါဆို", "လဆုတ်"]),
    ("ဝါဆိုလဆန်း", ["ဝါဆို", "လဆန်း"]),
    ("ဝါခေါင်လဆုတ်", ["ဝါခေါင်", "လဆုတ်"]),
    ("ဝါခေါင်လဆန်း", ["ဝါခေါင်", "လဆန်း"]),
    ("တော်သလင်းလဆုတ်", ["တော်သလင်း", "လဆုတ်"]),
    ("တော်သလင်းလဆန်း", ["တော်သလင်း", "လဆန်း"]),
    ("သီတင်းကျွတ်လဆုတ်", ["သီတင်းကျွတ်", "လဆုတ်"]),
    ("သီတင်းကျွတ်လဆန်း", ["သီတင်းကျွတ်", "လဆန်း"]),
    ("သီတင်းကျွတ်လပြည့်", ["သီတင်းကျွတ်", "လပြည့်"]),
    ("ပြာသိုလဆုတ်", ["ပြာသို", "လဆုတ်"]),
    ("ပြာသိုလဆန်း", ["ပြာသို", "လဆန်း"]),
    ("တပို့တွဲလဆုတ်", ["တပို့တွဲ", "လဆုတ်"]),
    ("တပို့တွဲလဆန်း", ["တပို့တွဲ", "လဆန်း"]),
    ("တပေါင်းလဆုတ်", ["တပေါင်း", "လဆုတ်"]),
    ("တပေါင်းလဆန်း", ["တပေါင်း", "လဆန်း"]),
    ("တပေါင်းလပြည့်", ["တပေါင်း", "လပြည့်"]),
    ("ပြည်နယ်အစိုးရအဖွဲ့", ["ပြည်နယ်", "အစိုးရ", "အဖွဲ့"]),
    ("ပြည်နယ်အစိုးရ", ["ပြည်နယ်", "အစိုးရ"]),
    ("မြန်မာနိုင်ငံတော်", ["မြန်မာ", "နိုင်ငံတော်"]),
    ("မြန်မာနိုင်ငံ", ["မြန်မာ", "နိုင်ငံ"]),
    ("ပြည်ထောင်စုအစိုးရ", ["ပြည်ထောင်စု", "အစိုးရ"]),
    ("အစိုးရအဖွဲ့ဝင်", ["အစိုးရ", "အဖွဲ့ဝင်"]),
    ("အစိုးရအဖွဲ့", ["အစိုးရ", "အဖွဲ့"]),
    ("အာဏာပိုင်နက်", ["အာဏာ", "ပိုင်နက်"]),
    ("ဝန်ကြီးရုံး", ["ဝန်ကြီး", "ရုံး"]),
    ("ဘာသာသာသနာ", ["ဘာသာ", "သာသနာ"]),
    ("စီးပွားရေးစနစ်", ["စီးပွားရေး", "စနစ်"]),
    ("သယံဇာတပစ္စည်း", ["သယံဇာတ", "ပစ္စည်း"]),
    ("ရေပေါ်ရေအောက်", ["ရေပေါ်", "ရေအောက်"]),
    ("မြေပေါ်မြေအောက်", ["မြေပေါ်", "မြေအောက်"]),
    ("တကျွန်းပို့ဒဏ်ခံ", ["တကျွန်းပို့ဒဏ်", "ခံ"]),
    ("ဗိုလ်ချုပ်အောင်ဆန်း", ["ဗိုလ်ချုပ်", "အောင်ဆန်း"]),
    ("ဗိုလ်ကြီးဇင်ယော်", ["ဗိုလ်ကြီး", "ဇင်ယော်"]),
    ("ဗိုလ်မှူးစောမုတ်သုန်", ["ဗိုလ်မှူး", "စောမုတ်သုန်"]),
    ("စော်ဘွားကြီးစဝ်စံထွန်း", ["စော်ဘွားကြီး", "စဝ်စံထွန်း"]),
    # 2026-10-19 arbitration and 2026-11-02 adjudication. Longer surfaces first.
    # These are agent over-merges, not the 10 owner rows above.
    ("နေထိုင်အသုံးပြုသူ", ["နေထိုင်", "အသုံးပြု", "သူ"]),
    ("အသုံးပြုသူ", ["အသုံးပြု", "သူ"]),
    ("နေထိုင်သူ", ["နေထိုင်", "သူ"]),
    ("တည်ဆဲဥပဒေ", ["တည်ဆဲ", "ဥပဒေ"]),
    ("စက်မှုဒီဇိုင်း", ["စက်မှု", "ဒီဇိုင်း"]),
    ("သဘောထားမှတ်ချက်", ["သဘောထား", "မှတ်ချက်"]),
    ("ပေါ်ပေါက်လာ", ["ပေါ်ပေါက်", "လာ"]),
    ("ဦးစီးဌာန", ["ဦးစီး", "ဌာန"]),
    ("ရန်အခါ", ["ရန်", "အခါ"]),
    ("ဒဏ်ရာရ", ["ဒဏ်ရာ", "ရ"]),
]
_SPLIT_MAP = {src: parts for src, parts in _EXACT_SPLITS}
# အရသာ ("taste") is a real word, but after a legal head it is the trap အရ + သာ.
_AYAR_THA_HEADS = {"ဥပဒေ", "နည်းဥပဒေ", "အက်ဥပဒေ", "တည်ဆဲဥပဒေ", "ပုဒ်မ", "ချက်"}
_SUBSECTION = set("ကခဂဃငစဆဇဈဉညဋဌဍဎဏတထဒဓနပဖဗဘမယရလဝသဟဠအဣဤဥဦဧဩဪ")
_FORM_HEADS = {"ပုံစံ", "ပုံစံပြု", "ဧည့်"}
# A real compound never ends in these clitic chains. Legal70k candidates such as
# ကော်မရှင်သည်၎င်း were false compounds.
_CLITIC_CHAINS = [
    ("ကိုသော်၎င်း", ["ကို", "သော်", "၎င်း"]),
    ("၌သော်၎င်း", ["၌", "သော်", "၎င်း"]),
    ("တွင်သော်၎င်း", ["တွင်", "သော်", "၎င်း"]),
    ("မှသော်၎င်း", ["မှ", "သော်", "၎င်း"]),
    ("နှင့်သော်၎င်း", ["နှင့်", "သော်", "၎င်း"]),
    ("အားသော်၎င်း", ["အား", "သော်", "၎င်း"]),
    ("သည်သော်၎င်း", ["သည်", "သော်", "၎င်း"]),
    ("သို့သော်၎င်း", ["သို့", "သော်", "၎င်း"]),
    ("ဖြင့်သော်၎င်း", ["ဖြင့်", "သော်", "၎င်း"]),
    ("သော်၎င်း", ["သော်", "၎င်း"]),
    ("သည်၎င်း", ["သည်", "၎င်း"]),
    ("ကို၎င်း", ["ကို", "၎င်း"]),
    ("၌၎င်း", ["၌", "၎င်း"]),
    ("တွင်၎င်း", ["တွင်", "၎င်း"]),
    ("မှ၎င်း", ["မှ", "၎င်း"]),
    ("နှင့်၎င်း", ["နှင့်", "၎င်း"]),
    ("အား၎င်း", ["အား", "၎င်း"]),
    ("သို့၎င်း", ["သို့", "၎င်း"]),
    ("ဖြင့်၎င်း", ["ဖြင့်", "၎င်း"]),
]
_KNOWN_FORMS = set(_PROTECTED_WHOLE)
_KNOWN_FORMS.update(_SPLIT_MAP)


def _load_keep_whole():
    """Documented one-token forms. Rejoin them, and prefer them in the trie."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resources",
        "lexicon",
        "owner_keep_whole.txt",
    )
    words = []
    if not os.path.exists(path):
        return words
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            word = line.split("#", 1)[0].strip()
            if word:
                words.append(word)
    return words


_KEEP_WHOLE = _load_keep_whole()
_KNOWN_FORMS.update(_KEEP_WHOLE)


def _rejoin_known(tokens, known):
    """Merge a token window when its concatenation is a known owner form."""
    out = []
    i = 0
    n = len(tokens)
    while i < n:
        acc = ""
        best_k = None
        for k in range(i, min(n, i + 12)):
            acc += tokens[k]
            if acc in known:
                best_k = k
        if best_k is None or best_k == i:
            out.append(tokens[i])
            i += 1
        else:
            out.append("".join(tokens[i:best_k + 1]))
            i = best_k + 1
    return out


def _apply_owner_postpass(tokens):
    """Rejoin protected forms, then apply exact-token owner splits."""
    rejoined = _rejoin_known(tokens, _KNOWN_FORMS)
    out = []
    for tok in rejoined:
        out.extend(_SPLIT_MAP.get(tok, [tok]))
    fixed = []
    for tok in out:
        if tok == "အရသာ" and fixed and fixed[-1] in _AYAR_THA_HEADS:
            fixed.extend(["အရ", "သာ"])
        else:
            fixed.append(tok)
    return _peel_clitic_chains(_join_form_codes(fixed))


def _peel_clitic_chains(tokens):
    """Split a function-word chain off the right edge. Do not touch protected words."""
    out = []
    protected = _PROTECTED_WHOLE | set(_KEEP_WHOLE)
    for token in tokens:
        if token in protected:
            out.append(token)
            continue
        peeled = None
        for tail, parts in _CLITIC_CHAINS:
            if token.endswith(tail) and len(token) > len(tail):
                stem = token[: -len(tail)]
                if len(stem) >= 2:
                    peeled = [stem, *parts]
                    break
        out.extend(peeled or [token])
    return out


def _form_tail(token: str) -> bool:
    if token in _SUBSECTION:
        return True
    core = token.replace(",", "")
    return bool(core) and (core.isdigit() or all("၀" <= ch <= "၉" for ch in core))


def _hyphen_code(token: str):
    text = token.strip()
    if text.startswith("-"):
        code = text[1:].strip()
        if _form_tail(code):
            return code
    return None


def _join_form_codes(tokens):
    """ပုံစံ - က and ပုံစံပြု - ၁၀ keep the hyphen and drop only the stray spaces."""
    out = []
    i = 0
    n = len(tokens)
    while i < n:
        if i + 1 < n and tokens[i] in _FORM_HEADS:
            code = _hyphen_code(tokens[i + 1])
            if code:
                out.append(tokens[i] + "-" + code)
                i += 2
                continue
        if (
            i + 2 < n
            and tokens[i] in _FORM_HEADS
            and tokens[i + 1].strip() == "-"
            and _form_tail(tokens[i + 2].strip())
        ):
            out.append(tokens[i] + "-" + tokens[i + 2].strip())
            i += 3
        else:
            out.append(tokens[i])
            i += 1
    return out


class TrieNode:
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_word: bool = False
        self.freq: int = 0
        self.word: str = ""


class WordSegmenter:
    def __init__(self, lexicon_path: Optional[str] = None):
        self.root = TrieNode()
        self.syllable_breaker = SyllableBreaker()
        self.word_count = 0
        
        if lexicon_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates = [
                os.path.join(base_dir, "resources", "lexicon", "my_MM_comprehensive_lexicon.txt"),
                os.path.join(base_dir, "resources", "lexicon", "my_MM_lexicon.txt"),
                os.path.join(base_dir, "my_MM_comprehensive_lexicon.txt"),
                os.path.join(base_dir, "my_MM_lexicon.txt"),
            ]
            for c in candidates:
                if os.path.exists(c):
                    lexicon_path = c
                    break

        if lexicon_path and os.path.exists(lexicon_path):
            self.load_lexicon(lexicon_path)
        for word in _KEEP_WHOLE:
            self.add_word(word, 10**9)

    def add_word(self, word: str, freq: int = 1):
        """Insert a word and its frequency into the trie."""
        word = word.strip()
        if not word:
            return
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True
        node.freq = max(node.freq, freq)
        node.word = word
        self.word_count += 1

    def load_lexicon(self, path: str):
        """Load tab-separated (word, freq) lexicon."""
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if not parts or not parts[0]:
                    continue
                word = parts[0]
                freq = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                self.add_word(word, freq)

    def is_word(self, token: str) -> bool:
        """Check if token is in the dictionary."""
        node = self.root
        for ch in token:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_word

    def get_frequency(self, token: str) -> int:
        """Get frequency of word, or 0 if not present."""
        node = self.root
        for ch in token:
            if ch not in node.children:
                return 0
            node = node.children[ch]
        return node.freq if node.is_word else 0

    def _segment_fmm(self, syllables: List[str]) -> List[str]:
        """Forward Maximum Matching constrained to syllable units."""
        words = []
        i = 0
        n = len(syllables)
        
        while i < n:
            # Greedily search for longest match of syllables[i..j]
            matched_word = None
            matched_j = i
            
            # Lookahead up to 8 syllables
            for j in range(min(n, i + 8), i, -1):
                candidate = "".join(syllables[i:j])
                if self.is_word(candidate):
                    matched_word = candidate
                    matched_j = j
                    break
                    
            if matched_word is not None:
                words.append(matched_word)
                i = matched_j
            else:
                # No multi-syllable word matched, take single syllable
                words.append(syllables[i])
                i += 1
                
        return words

    def _segment_bmm(self, syllables: List[str]) -> List[str]:
        """Backward Maximum Matching constrained to syllable units."""
        words = []
        i = len(syllables)
        
        while i > 0:
            matched_word = None
            matched_j = i
            
            for j in range(max(0, i - 8), i):
                candidate = "".join(syllables[j:i])
                if self.is_word(candidate):
                    matched_word = candidate
                    matched_j = j
                    break
                    
            if matched_word is not None:
                words.append(matched_word)
                i = matched_j
            else:
                words.append(syllables[i - 1])
                i -= 1
                
        words.reverse()
        return words

    def segment(self, text: str) -> List[str]:
        """
        Segment Myanmar text into words using Bi-directional Maximum Matching
        with frequency-weighted disambiguation.
        """
        if not text:
            return []
        from confusable import correct
        text, self.last_confusables = correct(text)
        self.last_text = text

        # First break into syllables
        syllables = self.syllable_breaker.segment(text)
        if not syllables:
            return []
            
        fmm_result = self._segment_fmm(syllables)
        bmm_result = self._segment_bmm(syllables)
        
        if fmm_result == bmm_result:
            chosen = fmm_result
        elif len(fmm_result) < len(bmm_result):
            chosen = fmm_result
        elif len(bmm_result) < len(fmm_result):
            chosen = bmm_result
        else:
            fmm_score = sum(self.get_frequency(w) for w in fmm_result)
            bmm_score = sum(self.get_frequency(w) for w in bmm_result)
            chosen = fmm_result if fmm_score >= bmm_score else bmm_result
        return _apply_owner_postpass(chosen)

    def tokenize(self, text: str) -> List[Dict[str, any]]:
        """Return structured tokens with word, span, and in-dictionary status."""
        words = self.segment(text)
        tokens = []
        offset = 0
        for w in words:
            start = text.find(w, offset)
            if start == -1:
                start = offset
            end = start + len(w)
            offset = end
            tokens.append({
                "token": w,
                "start": start,
                "end": end,
                "in_dict": self.is_word(w),
                "freq": self.get_frequency(w)
            })
        return tokens

    def segment_with_delimiter(self, text: str, delimiter: str = " | ") -> str:
        """Convenience method to join segmented words with a delimiter."""
        return delimiter.join(self.segment(text))


if __name__ == "__main__":
    segmenter = WordSegmenter()
    print(f"Loaded {segmenter.word_count} dictionary entries.")
    
    test_sentences = [
        "မြန်မာနိုင်ငံတော်အစိုးရနှင့်ပြည်သူလူထု",
        "ကာကွယ်ရေးဦးစီးချုပ်သည်စစ်ဆေးရေးအရာရှိချုပ်နှင့်တွေ့ဆုံခဲ့သည်",
        "ကိုယ်တိုင်ရေးအတ္ထုပ္ပတ္တိစာအုပ်ကိုဖတ်ရှုပါ",
        "အတွေ့အကြုံဖလှယ်ဆွေးနွေးပွဲတွင်ကျန်းမာရေးဝန်ထမ်းများတက်ရောက်သည်",
        "သတင်းထောက်များသတင်းရယူခွင့်ရှိသည်"
    ]
    
    for s in test_sentences:
        segmented = segmenter.segment_with_delimiter(s)
        print("\nInput :", s)
        print("Output:", segmented)
