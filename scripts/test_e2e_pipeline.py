#!/usr/bin/env python3
"""End-to-end pipeline test: segment -> decide -> HD projection -> chunk/merge.

Asserts pipeline invariants (codepoint conservation, 15-tag gate, lossless HD
collapse, chunk/merge identity) over a small golden corpus.

Run: python3 -B scripts/test_e2e_pipeline.py -v   (or --self-test)
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common_standards import ALLOWED_15_TAGS, OWNER_FIXED_TAG_SURFACES, strip_ws
from corpus_chunk_and_remediate import chunk_corpus_file, merge_chunks
from decide import decide_tokens, load_table
from project_mypos_hd import collapse_to_mypos15, project_sentence_to_mypos_hd
from word_segmenter import WordSegmenter

GOLDEN_RAW = [
    "တရားလိုသည်လျှောက်ထားသည်။",
    "မြန်မာနိုင်ငံသည်ပြည်ထောင်စုဖြစ်သည်။",
    "ပြည်နယ်အစိုးရအဖွဲ့သည်ဆုံးဖြတ်သည်။",
    "ဦးမင်းအောင်လှိုင်သည်စာအုပ်ဖတ်သည်။",
    "ကျောင်းသားများသည်ကျောင်းသို့သွားကြသည်။",
    "တစ်ခါတစ်ရံမိုးရွာသည်။",
    "စီးပွားရေးစနစ်ကိုပြောင်းလဲမည်။",
    "ခရီးသွားများလာသည်။",
]

# Owner fixed forms must map to the closed 15-tag set.
OWNER_FIXED = dict(OWNER_FIXED_TAG_SURFACES)

# Annotated sentences for the HD projection / chunk tests (word/tag).
GOLDEN_POS = [
    "ဦးစ/n သည်/ppm ကောင်း/v တာ/part ပဲ/part ။/punc",
    "တရားလို/n သည်/ppm လျှောက်ထား/v သည်/part ။/punc",
    "မြန်မာ/n နိုင်ငံ/n သည်/ppm ပြည်ထောင်စု/n ဖြစ်/v သည်/part ။/punc",
    "100/num ကောင်း/v ၍/conj အမလေး/int ။/punc",
]


def parse_pos(line: str) -> list[tuple[str, str]]:
    out = []
    for tok in line.split():
        w, _, t = tok.rpartition("/")
        out.append((w, t))
    return out


class TestE2EPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seg = WordSegmenter(profile="legal70k")
        cls.table = load_table()

    def test_segmentation_conserves_codepoints(self):
        for raw in GOLDEN_RAW:
            toks = self.seg.segment(raw)
            self.assertTrue(toks, raw)
            self.assertEqual(strip_ws("".join(toks)), strip_ws(raw), raw)

    def test_segmentation_is_deterministic(self):
        for raw in GOLDEN_RAW:
            self.assertEqual(self.seg.segment(raw), self.seg.segment(raw))

    def test_decide_outputs_legal_statuses_and_tags(self):
        for raw in GOLDEN_RAW:
            toks = self.seg.segment(raw)
            res = decide_tokens(toks, self.table, profile="legal70k")
            self.assertEqual(len(res), len(toks))
            for r in res:
                self.assertIn(r["status"], {"closed", "open", "review", "catalog"})
                if r["status"] == "closed":
                    self.assertIn(r["tag"], ALLOWED_15_TAGS, r)
                if r["status"] == "review":
                    self.assertTrue(r.get("readings"), r)
                    for rd in r["readings"]:
                        self.assertIn(rd["tag"], ALLOWED_15_TAGS, r)

    def test_owner_fixed_forms_are_closed(self):
        for surface, tag in OWNER_FIXED.items():
            res = decide_tokens([surface], self.table, profile="legal70k")
            self.assertEqual(res[0]["status"], "closed", surface)
            self.assertEqual(res[0]["tag"], tag, surface)

    def test_clause_final_vs_subject_particle(self):
        res = decide_tokens(["တရားလို", "သည်", "လျှောက်ထား", "သည်", "။"], self.table)
        self.assertEqual(res[3]["tag"], "part")

    def test_hd_projection_lossless_roundtrip(self):
        for line in GOLDEN_POS:
            pairs = parse_pos(line)
            for profile in ("general", "legal70k", "news_unified", "legacy_mypos_alt"):
                hd = project_sentence_to_mypos_hd(pairs, profile=profile)
                self.assertEqual(len(hd), len(pairs))
                for (w, base), row in zip(pairs, hd):
                    self.assertIn(row["mypos15"], ALLOWED_15_TAGS)
                    self.assertEqual(collapse_to_mypos15(row["mypos_hd"]), row["mypos15"])
                    # Base-15 tag must survive projection except documented ASCII-digit fw->num.
                    if not (base == "fw" and w.isdigit()):
                        self.assertEqual(row["mypos15"], base, (w, base, row))

    def test_hd_never_emits_ud_tags_in_base15(self):
        for line in GOLDEN_POS:
            for row in project_sentence_to_mypos_hd(parse_pos(line)):
                self.assertNotIn(row["mypos15"], {"DET", "AUX", "SCONJ", "PROPN"})

    def test_chunk_merge_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            src = td / "corpus.txt"
            lines = [" ".join(self.seg.segment(r)) for r in GOLDEN_RAW] * 5
            src.write_text("\n".join(lines) + "\n", encoding="utf-8")
            manifest = chunk_corpus_file(src, td / "chunks", chunk_size=10, subchunk_size=5)
            self.assertTrue(manifest)
            out = td / "merged.txt"
            merge_chunks(td / "chunks" / "manifest.json", out, src)
            self.assertEqual(
                strip_ws(out.read_text(encoding="utf-8")),
                strip_ws(src.read_text(encoding="utf-8")),
            )
            self.assertEqual(
                out.read_text(encoding="utf-8").splitlines(),
                src.read_text(encoding="utf-8").splitlines(),
            )


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--self-test"]
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestE2EPipeline)
    verbose = 2 if "-v" in argv else 1
    result = unittest.TextTestRunner(verbosity=verbose).run(suite)
    if result.wasSuccessful():
        print("SELF-TEST PASSED: e2e pipeline (segment/decide/HD/chunk-merge).")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
