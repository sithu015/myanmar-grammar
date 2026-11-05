#!/usr/bin/env python3
"""
tools/test_suite.py — Unit & Integration Test Suite for Myanmar NLP Tools.
"""

import unittest
import sys
import os

from syllable_breaker import SyllableBreaker
from word_segmenter import WordSegmenter


class TestMyanmarNLP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.breaker = SyllableBreaker()
        cls.segmenter = WordSegmenter()

    def test_syllable_breaker_basic(self):
        # Basic syllable segmentation
        text = "မြန်မာနိုင်ငံ"
        expected = ["မြန်", "မာ", "နိုင်", "ငံ"]
        self.assertEqual(self.breaker.segment(text), expected)

    def test_syllable_breaker_kinzi(self):
        # Kinzi test (U+1004 U+103A U+1039)
        text = "မင်္ဂလာပါ"
        expected = ["မင်္ဂ", "လာ", "ပါ"]
        self.assertEqual(self.breaker.segment(text), expected)

    def test_syllable_breaker_virama_stack(self):
        # Consonant stack test (Pint-sint)
        text = "ဗုဒ္ဓဘာသာ"
        expected = ["ဗုဒ္ဓ", "ဘာ", "သာ"]
        self.assertEqual(self.breaker.segment(text), expected)

    def test_word_segmenter_compounds(self):
        # Multi-syllable compound recognition
        text = "အတွေ့အကြုံဖလှယ်ဆွေးနွေးပွဲ"
        words = self.segmenter.segment(text)
        self.assertIn("အတွေ့အကြုံဖလှယ်ဆွေးနွေးပွဲ", words)

    def test_word_segmenter_honorific(self):
        text = "ကာကွယ်ရေးဦးစီးချုပ်"
        words = self.segmenter.segment(text)
        self.assertEqual(words, ["ကာကွယ်ရေးဦးစီးချုပ်"])

    def test_authoritative_compounds(self):
        # Compounds verified by user rulings and corpus remediation standards
        targets = [
            "စီးပွားရေး", "လူစာရင်း", "ဒဏ်ခံ", "ပထမနေ့",
            "ဆီမီးကွန်ဒတ်တာ", "စစ်သည်တော်", "တစ်နေ့နေ့",
            "မဖြစ်မနေ", "မငြိမ်မသက်", "အနိုင်ယူ"
        ]
        for t in targets:
            self.assertEqual(self.segmenter.segment(t), [t], f"Compound {t} was split!")

    def test_indefinite_reduplications(self):
        # User ruling: [တစ်] [NN] must be segmented as 2 tokens
        pairs = [
            ("တစ်ဦးဦး", ["တစ်", "ဦးဦး"]),
            ("တစ်ယောက်ယောက်", ["တစ်", "ယောက်ယောက်"]),
            ("တစ်နည်းနည်း", ["တစ်", "နည်းနည်း"]),
            ("တစ်နေရာရာ", ["တစ်", "နေရာရာ"]),
        ]
        for inp, exp in pairs:
            self.assertEqual(self.segmenter.segment(inp), exp, f"Indefinite {inp} failed to segment as 2 tokens!")

    def test_token_spans(self):
        text = "စာအုပ်ဖတ်ပါ"
        tokens = self.segmenter.tokenize(text)
        reconstructed = "".join(t["token"] for t in tokens)
        self.assertEqual(reconstructed, text)
        for t in tokens:
            self.assertEqual(text[t["start"]:t["end"]], t["token"])

    def test_dictionary_lookup(self):
        self.assertTrue(self.segmenter.is_word("အစိုးရ"))
        self.assertGreater(self.segmenter.get_frequency("အစိုးရ"), 0)

    def test_owner_postpass_does_not_trust_the_trie(self):
        # Forms the bare trie used to split or glue against Legal70k owner rules.
        cases = {
            "မြန်မာနိုင်ငံသား": ["မြန်မာနိုင်ငံသား"],
            "သာသနာရေး": ["သာသနာရေး"],
            "နှလုံးသား": ["နှလုံးသား"],
            "ရာပေါင်းများစွာ": ["ရာပေါင်းများစွာ"],
            "ဦးမင်းအောင်လှိုင်": ["ဦးမင်းအောင်လှိုင်"],
            "မြန်မာနိုင်ငံတော်": ["မြန်မာ", "နိုင်ငံတော်"],
            "တကျွန်းပို့ဒဏ်ခံ": ["တကျွန်းပို့ဒဏ်", "ခံ"],
            "ဗိုလ်ချုပ်အောင်ဆန်း": ["ဗိုလ်ချုပ်", "အောင်ဆန်း"],
            "စော်ဘွားကြီးစဝ်စံထွန်း": ["စော်ဘွားကြီး", "စဝ်စံထွန်း"],
            "သံအမတ်ကြီးဦးကျော်မိုးထွန်း": ["သံအမတ်ကြီး", "ဦးကျော်မိုးထွန်း"],
            "တကျွန်းအပို့ခံ": ["တကျွန်း", "အပို့", "ခံ"],
        }
        for src, expected in cases.items():
            self.assertEqual(self.segmenter.segment(src), expected, src)

    def test_keep_whole_vocabulary_and_trap(self):
        for whole in ("ပြဿနာ", "စာပေးစာယူ", "တမင်", "ပါရာစီတမော", "ဥပဒေ", "ကော်မတီ"):
            self.assertEqual(self.segmenter.segment(whole), [whole], whole)
        self.assertEqual(self.segmenter.segment("ဥပဒေအရသာ"), ["ဥပဒေ", "အရ", "သာ"])
        self.assertEqual(self.segmenter.segment("ထမင်းအရသာ"), ["ထမင်း", "အရသာ"])

    def test_memory_arbitration_splits_and_headwords(self):
        splits = {
            "တည်ဆဲဥပဒေ": ["တည်ဆဲ", "ဥပဒေ"],
            "စက်မှုဒီဇိုင်း": ["စက်မှု", "ဒီဇိုင်း"],
            "သဘောထားမှတ်ချက်": ["သဘောထား", "မှတ်ချက်"],
            "ပေါ်ပေါက်လာ": ["ပေါ်ပေါက်", "လာ"],
            "ဦးစီးဌာန": ["ဦးစီး", "ဌာန"],
            "ရန်အခါ": ["ရန်", "အခါ"],
            "ဒဏ်ရာရ": ["ဒဏ်ရာ", "ရ"],
            "အသုံးပြုသူ": ["အသုံးပြု", "သူ"],
            "နေထိုင်သူ": ["နေထိုင်", "သူ"],
            "နေထိုင်အသုံးပြုသူ": ["နေထိုင်", "အသုံးပြု", "သူ"],
        }
        wholes = [
            "ခရီးသွား", "သွားလာ", "တိုက်နယ်", "ဝင်ငွေ", "ထွက်ချက်",
            "ယစ်မျိုးခွန်", "အကျိုးငွေ", "စီရင်ဆုံးဖြတ်", "ဦးစီးဌာနမှူး",
            "တိုင်းဒေသကြီး", "နှင့်တကွ", "အပါအဝင်", "နေ့စဉ်မှတ်စု",
        ]
        for src, expected in splits.items():
            self.assertEqual(self.segmenter.segment(src), expected, src)
        for whole in wholes:
            self.assertEqual(self.segmenter.segment(whole), [whole], whole)
        self.assertEqual(self.segmenter.segment("ပုံစံ - က"), ["ပုံစံ-က"])
        self.assertEqual(self.segmenter.segment("ပုံစံပြု - ၁၀"), ["ပုံစံပြု-၁၀"])
        self.assertEqual(
            self.segmenter.segment("ကော်မရှင်သည်၎င်း"),
            ["ကော်မရှင်", "သည်", "၎င်း"],
        )
        self.assertEqual(
            self.segmenter.segment("ကျင့်ထုံးကိုသော်၎င်း"),
            ["ကျင့်ထုံး", "ကို", "သော်", "၎င်း"],
        )
        self.assertEqual(self.segmenter.segment("မက္ကဆီကို"), ["မက္ကဆီကို"])
        self.assertEqual(self.segmenter.segment("အမှုသည်"), ["အမှုသည်"])
        self.assertEqual(self.segmenter.segment("ကြားခံပုဂ္ဂိုလ်"), ["ကြားခံပုဂ္ဂိုလ်"])

    def test_lookalike_keystrokes(self):
        from confusable import correct
        self.assertEqual(correct("စျေး")[0], "ဈေး")
        self.assertEqual(correct("၂ဝ၂၄")[0], "၂၀၂၄")
        self.assertEqual(correct("၀န်ကြီး")[0], "ဝန်ကြီး")
        self.assertEqual(correct("၄င်း")[0], "၎င်း")
        self.assertEqual(correct("ဂ၀၀")[0], "၈၀၀")
        self.assertEqual(correct("ပုဒ်မ ၇")[0], "ပုဒ်မ ၇")
        self.assertEqual(correct("ဩ")[0], "ဩ")
        self.assertEqual(correct("ဪဪ")[0], "ဪဪ")
        self.assertTrue(self.segmenter.segment("၀န်ကြီး"))

    def test_verb_pair_lookup(self):
        from verb_pair import lookup
        got = lookup("ဖွင့်")
        self.assertEqual(got["role"], "causative")
        self.assertEqual(got["pair"], "ပွင့်")
        self.assertEqual(got["tag"], "v")

    def test_register_pair(self):
        from register import lookup
        got = lookup("တယ်")
        self.assertEqual(got["rows"][0]["pair"], "သည်")
        self.assertEqual(got["rows"][0]["tag"], "part")
        self.assertEqual(lookup("ပွင့်")["status"], "open")

    def test_nominal_classes(self):
        from nominal import lookup
        self.assertEqual(lookup("noun")["rows"][0]["tag"], "n")
        self.assertEqual(lookup("adjective-demonstrative")["rows"][0]["tag"], "adj")
        self.assertTrue(all(row["tag"] != "DET" for row in lookup("noun")["rows"]))

    def test_traditional_calendar_segmentation_and_confusable(self):
        from confusable import correct
        self.assertEqual(correct("ဥပုပ်နေ့")[0], "ဥပုသ်နေ့")
        self.assertEqual(correct("ဥပုပ်")[0], "ဥပုသ်")
        self.assertEqual(self.segmenter.segment("ကောဇာသက္ကရာဇ်"), ["ကောဇာ", "သက္ကရာဇ်"])
        self.assertEqual(self.segmenter.segment("တန်ဆောင်မုန်းလဆုတ်"), ["တန်ဆောင်မုန်း", "လဆုတ်"])
        self.assertEqual(self.segmenter.segment("တန်ဆောင်မုန်းလဆန်း"), ["တန်ဆောင်မုန်း", "လဆန်း"])
        self.assertEqual(self.segmenter.segment("နတ်တော်လပြည့်"), ["နတ်တော်", "လပြည့်"])
        for whole in ("လဆန်း", "လဆုတ်", "လပြည့်", "လပြည့်ကျော်", "လကွယ်", "အဖိတ်နေ့", "ဥပုသ်နေ့", "ဗုဒ္ဓဟူး"):
            self.assertEqual(self.segmenter.segment(whole), [whole], whole)


if __name__ == "__main__":
    unittest.main()

