# myanmar-grammar

မြန်မာသဒ္ဒါနှင့် NLP skill။ MLC 2013 ဝါစင်္ဂ၊ myPOS 15-tag၊ Legal70k ပုဒ်ဖြတ်စံ၊ Multi-Workflow Profiles နှင့် Universal Dependencies (UD v2) ဆုံးဖြတ်ချက်ကိရိယာများ ပါဝင်သည်။

စတင်ဖတ်ရန် [SKILL.md](SKILL.md)။ Tag မဆုံးဖြတ်မီ `scripts/decide.py` ကို အရင်သုံးပါ။ Corpus ဖိုင်ထဲတွင် Canonical myPOS tag ၁၅ လုံး (`ALLOWED_15_TAGS`) သာ ထားရှိရမည်ဖြစ်ပြီး `DET` နှင့် `PROPN` ကို တိုက်ရိုက် မထည့်ရပါ။

## 1. Single Source of Truth (`scripts/common_standards.py`)

Repository တစ်ခုလုံးရှိ စံနှုန်းများ၊ Constants များနှင့် စည်းမျဉ်းများကို `scripts/common_standards.py` တွင် ဗဟိုပြု သတ်မှတ်ထားသည်:
- **`ALLOWED_15_TAGS`**: တရားဝင် Canonical 15-Tag အသေးလုံးစစ်စစ် (`abb, adj, adv, conj, fw, int, n, num, part, ppm, pron, punc, sb, tn, v`)။
- **Legacy Tag Rejection**: ပြင်ပ/မူကြမ်းသုံး tag များဖြစ်သည့် `prpn` (Proper Noun -> use `n`), `for` (Foreign Word -> use `fw`), `tnum` (Text Number -> use `tn`) များကို Base-15 တွင် လုံးဝ အသုံးမပြုရ (Validator မှ `invalid_pos_tag` အဖြစ် ပယ်ချသည်)။
- **ASCII Digits**: `1, 2, 3, 2026` ကဲ့သို့သော လက်တင်ဂဏန်းများကို `fw` မတပ်ရ; ကိန်းဂဏန်းအက္ခရာ `num` အဖြစ်သာ တပ်ရမည် (myPOS-HD တွင် `num:latn` -> UD `NUM` အဖြစ် lossless ချိတ်ဆက်သည်)။
- **Prefixes & Titles**: `PERSON_PREFIXES` (၁၉ မျိုး), `STRICT_TITLE_PREFIXES` (၉ မျိုး), `TITLES_AND_RANKS` (၄၉ မျိုး)။
- **Classifiers & Measures**: `CLASSIFIERS` (၂၅ မျိုး), `TIME_MEASURE_NOUNS` (၈ မျိုး), `SUBSECTION_CONSONANTS` (၄၁ လုံး)။
- **Owner Standards**: `OWNER_FIXED_TAG_SURFACES` (၁၁ မျိုး), `OWNER_COMPONENT_STANDARDS_ORDERED` (၁၄ surfaces / ၁၀ rows), `RECORD_ONLY_LEADS` (၈ မျိုး)။

## 2. Multi-Workflow Profiles (`--profile`)

CLI ကိရိယာများနှင့် scripts များအားလုံးတွင် `--profile {general, legal70k, news_unified, legacy_mypos_alt}` ဖြင့် profile ရွေးချယ်နိုင်သည်:
1. **`general`** (General Burmese text — `scripts/decide.py` default): ဝါကျပိတ်ကြိယာနောက်ဆက် = `part`, ရည်ရွယ်ချက်ပြ `ရန်/အောင်` = `conj`, `သော်` = `conj`, modal `သင့်` = `part`။
2. **`legal70k`** (Institutional Legal Corpus — `scripts/nlp_cli.py -w` default): Owner component standards (10 rows), ဝါကျပိတ် = `part`, `သော်` = `part`, modal `သင့်` = `part`။
3. **`news_unified`** (News Gold Corpus — News SOP v3.2): ၅ ဝဏ္ဏ သတင်းဝေါဟာရ (`လေ့လာသုံးသပ်သူ`) = `1 Token /n`, ဝါကျပိတ် = `part`, `သော်` = `part`, modal `သင့်` after verb = `v` (UD: `VERB`)။
4. **`legacy_mypos_alt`** (MLC 2013 / myPOS v3.0 / Legal L1-2k): ဝါကျပိတ်ကြိယာဝိဘတ် (`သည်/တယ်/မည်/မယ်/၏`) = `ppm` (`pos_copula_ppm`), `သော်` = `conj`, modal `သင့်` = `part`။

## 3. Codepoint Conservation vs. Opt-In Normalization

- **Default (Codepoint Conservation)**: Tool အားလုံးသည် မူရင်းအက္ခရာစဉ်နှင့် character offsets များကို အတိအကျ ထိန်းသိမ်းသည် (`re.sub(r"\s+", "", before) == re.sub(r"\s+", "", after)`)။ မူရင်းစာသားရှိ အက္ခရာများကို အလိုအလျောက် အစားထိုးပြင်ဆင်ခြင်း မပြုပါ။
- **Opt-In (`--normalize-confusables`)**: အမြင်တူ အက္ခရာမှားရိုက်ချက်များ (`၀/ဝ`, `၇/ရ`, `၈/ဂ`, `၄/၎`, `စျ/ဈ`, `ဦ/ဦ`) ကို ပြင်ဆင်လိုပါက CLI တွင် `--normalize-confusables` flag ပေးပို့ရမည်။
- **Rollback Guard**: `scripts/corpus_chunk_and_remediate.py` နှင့် `scripts/validate_nlp_corpus.py` တွင် non-whitespace character ပြောင်းလဲမှု ဖြစ်ပေါ်ပါက data corruption ကာကွယ်ရန် အလိုအလျောက် rollback စနစ် ပါဝင်သည်။

## 4. `myPOS-HD v4.1` Additive Dual-Layer Projection

Canonical Base-15 tagset ကို မထိခိုက်စေဘဲ Universal Dependencies (UD v2) နှင့် NER/IE လုပ်ငန်းစဉ်များအတွက် `scripts/project_mypos_hd.py` ဖြင့် lossless additive projection ပြုလုပ်နိုင်သည်:
- **Layer 1 (mypos15)**: Canonical 15 tags (lossless recovery via `collapse_to_mypos15(hd_tag)`)။
- **Layer 2 (mypos_hd)**: 46 hierarchical tags (`base:sub`, e.g., `n:prop`, `v:stat`, `conj:sub`, `part:aux`, `ppm:fin`)။
- **Layer 3 (mypos_core)**: 10 expanded flat syntactic tags (`propn`, `aux`, `clf`, `neg`, `nom`, `rel`, `sfp`, `cconj`, `sconj`, `det`)။
- **Layer 4 (Universal Dependencies v2)**: Complete UPOS (17 categories) + FEATS mapping။

## 5. Phase 5 Open Design Trade-Offs

1. **Title/Rank vs Personal Name Segmentation (`မြဝတီမင်းကြီး`, `လှေသင်းအတွင်းဝန်`)**:
   - အုပ်ချုပ်ရေး၊ စစ်ဘက်နှင့် နန်းတွင်းရာထူးများ (`TITLES_AND_RANKS`) ကို modern news/legal တွင် **1 Token `/n`** အဖြစ် ထားရှိပြီး ကိုယ်ပိုင်အမည်မှ ခွဲထုတ်သည် (`မြဝတီမင်းကြီး/n ဦးစ/n`)။
   - Decomposing titles (e.g. `မြဝတီ/n မင်းကြီး/n`) breaks Downstream NER Title-Person boundaries (`B-PER` / `O`). Modern administrative corpora require atomic titles, whereas historical morphological analyses may prefer compositional breakdown.
2. **Reversible 3-Slot `compound_groups` Layering**:
   - Slot 1 (Syllables) <-> Slot 2 (Base-15 Words) <-> Slot 3 (MWE Compounds)။ Syntactic dependency parsing အတွက် Slot 2 ကို အသုံးပြုပြီး၊ Search/NER/MT အတွက် Slot 3 ကို အသုံးချနိုင်သည်။
3. **Archaic vs Modern Corpus Expectations**:
   - ရှေးဟောင်းပေမူ၊ ကုန်းဘောင်ခေတ်အမိန့်တော်ပြန်တမ်းများရှိ သတ်ပုံ (`တပါးသူ`, `ရွှေမင်ကြောင်း`) ကို ခေတ်သစ်စံနှုန်းများဖြင့် ဇွတ်အတင်း မပြင်ဆင်စေရန် Profile Decoupling (`legacy_mypos_alt` သို့မဟုတ် historical config) ဖြင့် ထိန်းသိမ်းသည်။

## 6. Domain Lexicon (`resources/lexicon/domain_legal.txt`)

`scripts/mine_domain_lexicon.py` သည် gold POS corpus ၏ မဂဏန်းလိုင်း (odd lines) မှ ≥5 ကြိမ် ပါသော token များကို ရှာ၍ supplementary lexicon ပြုလုပ်သည် (trap forms၊ `agent-hard-cases.md` "Do not glue"၊ indefinite reduplication ကို ဖယ်ထုတ်)။ `legal70k` နှင့် `news_unified` profile တွင်သာ default load လုပ်သည် (`domain_legal.txt` 4,408 / `domain_news.txt` 5,071 လုံး)။ Held-out စုံလိုင်း 3,000 တွင် boundary F1 — legal 0.635 → 0.921၊ news (Drive: `news_gold_lines_0001_70000_pos.txt`) 0.488 → 0.826။ Legal စာသားသည် boilerplate ထပ်တတ်သဖြင့် ဤအမှတ်သည် အထက်ပိုင်း ခန့်မှန်းချက်ဖြစ်နိုင်သည်။ ပြန်ထုတ်ရန်: `python3 scripts/mine_domain_lexicon.py --gold <gold_pos.txt> --profile news_unified --out resources/lexicon/domain_news.txt --evaluate`

`news_unified` ရဲ့ gold-mined lexicon တွင် `domain_myposalt.txt` (myPOS v3 + ALT၊ 4,047) နှင့် `domain_medical.txt` (MyMedicon၊ 1,210) ကိုလည်း `general` / `legacy_mypos_alt` profile တွင် load လုပ်သည် (Drive: `mypos-myalt-mymedicon.compound.txt`၊ 77,894 လိုင်း၊ `--sid-prefix SNT.MYMEDICON` / `--exclude-sid-prefix SNT.MYMEDICON`၊ `[a/n|b/n]/n` ကို component အဖြစ် flatten)။ Held-out F1: medical 0.575 → 0.708၊ myPOS+ALT 0.674 → 0.802။ `--min-freq` 3/2 သုံးရင် F1 ကျသဖြင့် 5 ကို ထားသည်။

`news_unified`: News gold တွင် `အပေါ်/အောက်` သည် ppm ~70% / n ~30% ဖြစ်သဖြင့် ဤ profile တွင် `always n` မသုံးဘဲ review (ppm, n နှစ်မျိုး) သို့ ပြောင်းထားသည်။ `#`/`$` သည် gold တွင် punc/sb ~50:50 ကွဲနေသဖြင့် owner ဆုံးဖြတ်ချက် မရမီ မပြောင်းသေးပါ။

## 7. Verification & Self-Test

`make test` သည် self-test အားလုံး + `scripts/test_e2e_pipeline.py` (segment → decide → myPOS-HD → chunk/merge E2E) + unit tests ကို တစ်ခါတည်း run သည်။ `make hooks` ဖြင့် git pre-commit hook ထည့်သွင်းပြီး၊ `.github/workflows/test.yml` က CI တွင် `make test` ကို run သည်။

```bash
python3 -B scripts/test_nlp_tools.py -v
python3 scripts/decide.py --self-test
python3 scripts/project_mypos_hd.py --self-test
python3 scripts/validate_nlp_corpus.py --self-test
python3 scripts/corpus_chunk_and_remediate.py --self-test
python3 scripts/legal70k_audit.py --self-test
```
