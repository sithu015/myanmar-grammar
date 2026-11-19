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

    def test_mypos_hd_projection_and_validator_gates(self):
        from project_mypos_hd import collapse_to_mypos15, project_sentence_to_mypos_hd
        from validate_nlp_corpus import audit_line

        pairs = [
            ("ဦးစ", "n"),
            ("သည်", "ppm"),
            ("တကယ်", "adv"),
            ("ပဲ", "part"),
            ("။", "punc"),
            ("မ", "part"),
            ("သွား", "v"),
            ("ပဲ", "part"),
            ("။", "punc"),
        ]
        projected = project_sentence_to_mypos_hd(pairs, proper_nouns={"ဦးစ"})
        self.assertEqual(projected[0]["mypos_hd"], "n:prop")
        self.assertEqual(projected[1]["mypos_hd"], "ppm:subj")
        self.assertEqual(projected[3]["mypos_hd"], "part:foc")
        self.assertEqual(projected[5]["mypos_hd"], "part:neg")
        self.assertEqual(projected[7]["mypos_hd"], "part:neg")
        self.assertEqual(collapse_to_mypos15("num:latn"), "num")
        self.assertEqual(collapse_to_mypos15("ppm:fin"), "ppm")

        bad = "မိမိ/pron ၏/punc ၄၄၀/num ဦး/n 8/fw ဦး/n ကျော်ဇော/n"
        types = {x["type"] for x in audit_line(bad, 1, mode="pos")}
        self.assertIn("burmese_letter_tagged_punc", types)
        self.assertIn("num_classifier_tagged_n", types)
        self.assertIn("ascii_digit_tagged_fw", types)
        self.assertIn("split_name_prefix_violation", types)


class TestM1M2Hardening(unittest.TestCase):
    """Milestone 1 & Milestone 2 Hardening Regression & Parity Test Suite."""

    @classmethod
    def setUpClass(cls):
        cls.breaker = SyllableBreaker()
        cls.ws_general = WordSegmenter(profile="general", normalize_confusables=False)
        cls.ws_legal = WordSegmenter(profile="legal70k", normalize_confusables=False)
        cls.ws_news = WordSegmenter(profile="news_unified", normalize_confusables=False)
        cls.ws_legacy = WordSegmenter(profile="legacy_mypos_alt", normalize_confusables=False)

    def test_f1_myparser_three_char_dot_below_no_crash(self):
        from myparser import MyParser
        p = MyParser()
        # "ကမ့" has C1 + C2 + \u1037 (dot below), previously caused evaluate_context IndexError
        res = p.evaluate_context("ကမ့", 0, 0)
        self.assertIsInstance(res, int)

    def test_f1_f4_syllable_breaker_whitespace_and_numerals(self):
        # Syllable breaker handles leading/interleaved spaces and mixed numerals cleanly
        spans = self.breaker.get_spans(" ၁၃")
        self.assertTrue(any(syl == "၁၃" for _, _, syl in spans))
        seg = self.breaker.segment(" (")
        self.assertEqual(seg, ["("])
        self.assertEqual(self.breaker.segment(" "), [])

    def test_f3_f4_word_segmenter_conservation_spans_and_u1029(self):
        # Spans map exactly to input characters by default (no confusable normalization by default)
        text = "ဝန်ကြီး သမက်တော်ဩယာဓမ္မရာဇာ ဩဘာ လက်ယာ"
        toks = self.ws_general.tokenize(text)
        for t in toks:
            self.assertEqual(text[t["start"]:t["end"]], t["token"])
        words = [t["token"] for t in toks]
        self.assertIn("ဝန်ကြီး", words)
        self.assertIn("ဩယာ", words)
        self.assertIn("ဓမ္မရာဇာ", words)
        self.assertIn("ဩဘာ", words)
        self.assertIn("လက်ယာ", words)

        # Opt-in confusable normalization correctly normalizes digit zero
        ws_norm = WordSegmenter(profile="general", normalize_confusables=True)
        norm_words = ws_norm.segment("၀န်ကြီး")
        self.assertEqual(norm_words, ["ဝန်ကြီး"])

    def test_profile_switching_word_segmenter(self):
        # Comparing segmentation across profiles
        legal_words = self.ws_legal.segment("ပုံစံ - က")
        self.assertEqual(legal_words, ["ပုံစံ-က"])
        # Verify profiles exist and can be instantiated cleanly
        self.assertEqual(self.ws_legal.profile, "legal70k")
        self.assertEqual(self.ws_general.profile, "general")
        self.assertEqual(self.ws_news.profile, "news_unified")
        self.assertEqual(self.ws_legacy.profile, "legacy_mypos_alt")

    def test_f10_confusable_multipass_punctuation_and_shan(self):
        from confusable import correct
        self.assertEqual(correct("၁ဝဝ")[0], "၁၀၀")
        self.assertEqual(correct("ဝ.၅")[0], "၀.၅")
        self.assertEqual(correct("က့်")[0], "က့်")
        self.assertEqual(correct("၁ဝ။")[0], "၁၀။")
        self.assertEqual(correct("႞၀")[0], "႞၀")  # Shan One + Myanmar zero preserved
        self.assertEqual(correct("႞ဝ")[0], "႞ဝ")

    def test_f5_decide_ascii_next_textnum_and_chained_aux(self):
        import decide
        self.assertFalse(decide._is_number(","))
        self.assertFalse(decide._is_number(""))
        self.assertTrue(decide._is_number("123"))
        self.assertTrue(decide._is_number("၁၂၃"))
        table = decide.load_table()
        # Test ASCII digits/punctuation categorization
        d_num = decide.decide_tokens(["123"], table, profile="general")
        self.assertEqual(d_num[0]["tag"], "num")
        d_punc = decide.decide_tokens([":"], table, profile="general")
        self.assertEqual(d_punc[0]["tag"], "punc")
        # Chained auxiliary test: သွား ခဲ့ သည် ကို -> ကို/ppm
        d_chain = decide.decide_tokens(["သွား", "ခဲ့", "သည်", "ကို"], table, profile="general")
        self.assertEqual(d_chain[3]["tag"], "ppm")

    def test_profile_switching_decide_and_hd(self):
        import decide
        table = decide.load_table()
        # Profile-specific triage of သော် after a clause word
        d_gen = decide.decide_tokens(["ဖြစ်", "သော်"], table, profile="general")
        d_leg = decide.decide_tokens(["ဖြစ်", "သော်"], table, profile="legal70k")
        self.assertEqual(d_gen[1]["tag"], "conj")
        self.assertEqual(d_leg[1]["tag"], "part")

    def test_f11_project_mypos_hd_escaped_slash_conj_propn(self):
        from project_mypos_hd import _parse_pos_line, project_sentence_to_mypos_hd
        line = r"km\/h/n ဒါပေမယ့်/conj စောဘဦးကြီး/n ကျူးကျော်သူ/n အခြေအနေမျိုး/n ဦးဆုံး/n နေမျိုးသီဟသူ/n"
        toks = _parse_pos_line(line)
        hd = project_sentence_to_mypos_hd(toks)
        # km/h unescaped
        self.assertEqual(hd[0]["word"], "km/h")
        # sentence-initial discourse conjunction
        self.assertEqual(hd[1]["mypos_hd"], "conj:disc")
        # personal name PROPN
        self.assertEqual(hd[2]["mypos_hd"], "n:prop")
        # non-person nouns NOT corrupted to PROPN
        self.assertEqual(hd[3]["mypos_hd"], "n")
        self.assertEqual(hd[4]["mypos_hd"], "n")
        self.assertEqual(hd[5]["mypos_hd"], "n")
        # genuine royal title PROPN
        self.assertEqual(hd[6]["mypos_hd"], "n:prop")

    def test_f2_legal70k_audit_ws_pos_parity_malformed_token(self):
        from legal70k_audit import _ws_pos_parity
        res = _ws_pos_parity(["မြန်မာ နိုင်ငံ"], ["မြန်မာ/n နိုင်ငံ"])
        self.assertTrue(any(i["type"] == "missing_pos_tag" for i in res))
        self.assertFalse(any(i["type"] == "ws_pos_character_mismatch" for i in res))

    def test_f6_validate_zawgyi_shan_karen_and_escaped_brackets(self):
        from validate_nlp_corpus import ZAWGYI_INDICATORS, audit_line
        # Shan/Karen false positive immunity
        self.assertIsNone(ZAWGYI_INDICATORS.search("တႆး"))
        self.assertIsNone(ZAWGYI_INDICATORS.search("ၡ"))
        # Zawgyi indicators
        self.assertIsNotNone(ZAWGYI_INDICATORS.search("(\u1031က)"))
        self.assertIsNotNone(ZAWGYI_INDICATORS.search("လေးေသောင်း"))
        # Escaped brackets in bracket mode
        esc_line = r"\[/sb ဥပမာ/n \]/sb"
        issues = audit_line(esc_line, 1, mode="bracket")
        self.assertEqual(issues, [])

    def test_f8_validate_u103f_classifiers_subsection_and_profiles(self):
        from validate_nlp_corpus import audit_line
        # U+103F starting char
        t_103f = {i["type"] for i in audit_line("ဿာန်/n", 1, mode="pos")}
        self.assertIn("illegal_word_start_dependent_sign", t_103f)
        # 25 Classifiers: ၃/num အုပ်/n
        t_clf = {i["type"] for i in audit_line("၃/num အုပ်/n", 2, mode="pos")}
        self.assertIn("num_classifier_tagged_n", t_clf)
        # Subsection marker in legal70k: ( က ) /n
        t_sub = {i["type"] for i in audit_line("(/punc က/n )/punc", 3, mode="pos", profile="legal70k")}
        self.assertIn("subsection_marker_pos_violation", t_sub)
        # Split name prefix immunity on အဆောက်အဦး ကို
        t_clean = {i["type"] for i in audit_line("အဆောက်အဦး/n ကို/n", 4, mode="pos", profile="legal70k")}
        self.assertNotIn("split_name_prefix_violation", t_clean)

    def test_f7_audit_ner_tsv_clitics_and_protected_nouns(self):
        from validate_nlp_corpus import audit_ner_tsv
        tsv = [
            "line_number\ttoken_id\ttoken\tpos\tner_bio",
            "1\t1\tဦးကိုကို\tn\tB-PER",
            "1\t2\tအသောက\tn\tB-PER",
            "1\t3\tသံဃာ့နာယက\tn\tB-ORG",
            "1\t4\tများ\tpart\tB-ORG",
            "1\t5\tနှင့်\tconj\tI-PER",
        ]
        issues = audit_ner_tsv(tsv)
        types = {i["type"] for i in issues}
        self.assertNotIn("clitic_bleed_in_token", types)
        self.assertIn("clitic_bleed_part_tagged", types)
        self.assertIn("clitic_bleed_conj_tagged", types)

    def test_f9_remediate_ws_pos_alignment_and_sync_ws(self):
        from corpus_chunk_and_remediate import remediate_single_line, stream_remediate_file
        import tempfile
        from pathlib import Path
        # Shattered word in POS mode
        rem_pos, _, _ = remediate_single_line("ဦး/n စီ/n ချုပ်/n ရုံး/n", 1, mode="pos")
        self.assertIn("ဦးစီချုပ်/n", rem_pos)
        # Stage 2 idiom in POS mode
        rem_idiom, _, _ = remediate_single_line("တ/tn စုံ/n တ/tn ယောက်/n", 2, mode="pos")
        self.assertIn("တစုံတယောက်/pron", rem_idiom)
        # Verbal chains: သွား ခဲ့ နိုင် ခြင်း
        rem_chain, _, _ = remediate_single_line("သွား/v ခဲ့/v နိုင်/v ခြင်း/n", 3, mode="pos")
        self.assertIn("သွား/v ခဲ့/part နိုင်/part ခြင်း/part", rem_chain)
        # Medial သည် conversion
        rem_med, _, _ = remediate_single_line("သွား/v ခဲ့/part သည်/ppm ကို/ppm", 4, mode="pos")
        self.assertIn("သည်/part ကို/ppm", rem_med)
        # Profile-aware final သည် under legacy_mypos_alt
        rem_leg, _, _ = remediate_single_line("သွား/v သည်/ppm ။/punc", 5, mode="pos", profile="legacy_mypos_alt")
        self.assertIn("သည်/ppm ။/punc", rem_leg)
        # Sync WS out check
        with tempfile.TemporaryDirectory() as tmp:
            p_in = Path(tmp) / "in.txt"
            p_out = Path(tmp) / "out.txt"
            p_sync = Path(tmp) / "sync.txt"
            p_in.write_text("ဦး/n စီ/n ချုပ်/n က/ppm တ/tn စုံ/n တ/tn ယောက်/n\n", encoding="utf-8")
            stream_remediate_file(p_in, p_out, mode="pos", sync_ws_path=p_sync)
            self.assertEqual(p_sync.read_text(encoding="utf-8").strip(), "ဦးစီချုပ် က တစုံတယောက်")

    def test_common_standards_single_source_and_parse_pos_token(self):
        from common_standards import (
            ALLOWED_15_TAGS, PROFILES, TITLES_AND_RANKS, CLASSIFIERS,
            parse_pos_token, strip_ws, normalize_profile
        )
        self.assertEqual(len(ALLOWED_15_TAGS), 15)
        self.assertEqual(PROFILES, ("general", "legal70k", "news_unified", "legacy_mypos_alt"))
        self.assertEqual(len(TITLES_AND_RANKS), 52)
        self.assertEqual(len(CLASSIFIERS), 25)
        self.assertEqual(parse_pos_token(r"km\/h/n"), ("km/h", "n"))
        self.assertEqual(parse_pos_token(r"\/sb"), ("\\", "sb"))
        self.assertEqual(parse_pos_token("မြန်မာ/n"), ("မြန်မာ", "n"))
        self.assertIsNone(parse_pos_token("မြန်မာ/invalid_tag", allowed_tags=ALLOWED_15_TAGS))
        self.assertIsNone(parse_pos_token("မြန်မာ"))
        self.assertEqual(strip_ws(" မြန်မာ   နိုင်ငံ "), "မြန်မာနိုင်ငံ")
        self.assertEqual(normalize_profile(None, default="general"), "general")
        with self.assertRaises(ValueError):
            normalize_profile("UNKNOWN")

    def test_clitic_and_pronoun_segmentation_across_profiles(self):
        """Ensure high-frequency clitics and pronouns are not over-merged into single tokens."""
        cases = [
            ("ကျွန်တော်တို့", ["ကျွန်တော်", "တို့"]),
            ("၎င်းတို့", ["၎င်း", "တို့"]),
            ("ခင်ဗျားကို", ["ခင်ဗျား", "ကို"]),
            ("တစ်ခု", ["တစ်", "ခု"]),
            ("တွေကို", ["တွေ", "ကို"]),
        ]
        for name, seg in [
            ("general", self.ws_general),
            ("legal70k", self.ws_legal),
            ("news_unified", self.ws_news),
            ("legacy_mypos_alt", self.ws_legacy),
        ]:
            for surface, expected in cases:
                res = seg.segment(surface)
                self.assertEqual(
                    res,
                    expected,
                    f"Profile '{name}' failed to split clitic '{surface}': got {res}, expected {expected}",
                )


if __name__ == "__main__":
    unittest.main()

