# Downstream NLP Architecture & Task Guide for Myanmar (Burmese)

This reference bridges the **Myanmar Language Commission (MLC 2013)** grammar framework (`chapters/ch01` to `ch20`) and the **Corpus Owner Rules** (`cheatsheet.md#corpus-rules`) with production **Core NLP** and **Downstream NLP** tasks: Named Entity Recognition (NER), Dependency Parsing (Universal Dependencies), Corpus Indexing & CQL, Neural Machine Translation (NMT), LLM/RAG Chunking, Speech Processing (TTS/ASR/G2P), Sentiment/Information Extraction, and Human-in-the-Loop Corpus QA.

## 1. End-to-End Myanmar NLP Pipeline Architecture

Execute preprocessing and annotation stages in strict order to prevent cascading boundary and encoding defects:

1. **Encoding Detection & Conversion**: Detect Zawgyi vs. Unicode 5.1+ before any text processing. Never emit Zawgyi codepoints downstream.
2. **Canonical Unicode Normalization (NFC)**: Apply Unicode NFC normalization and canonical combining-mark ordering (consonant + medials `\u103B..\u103E` + vowel signs `\u102B..\u1032` + nasal/anusvara `\u1036` + asat `\u103A` + tone marks `\u1037,\u1038`).
3. **Pre-Segmentation Orthographic Audit Gate**:
   - **Canonical Exemptions**: Preserve Burmese **Kinzi** (`\u1004\u103A\u1039` = `င်္`) and **stacked-consonant killers** (medial + asat, e.g., `ကျ်ား`).
   - **Confusable & Context Gate**: Distinguish Myanmar digit zero `၀` (`\u1040`) from letter wa `ဝ` (`\u101D`), and digit four `၄` (`\u1044`) from `၎င်း` (`\u104E`) and genitive `၏` (`\u104F`) using immediate script-neighbor context.
   - **Illegal Word-Start Mask (`ILLEGAL_B_CHARS`)**: Dependent vowel signs, medials, asat, virama, and tone marks (`\u102B..\u103E`, `\u1056..\u1059`) can never begin a word (`B` tag). In neural segmenters (such as `UnifiedCut` windowed character n-gram transformers) and rule engines, hard-mask `P(B) = 0` on these codepoints to guarantee `0.00%` mid-syllable corruption.
4. **Orthographical Syllabification**: Use deterministic rule-table syllable segmentation (Maung & Mikami 2008) for text pipelines. Keep phonological/voicing sandhi strictly separate for speech/G2P pipelines.
5. **Syntactic Word Segmentation (ပုဒ်ဖြတ်ခြင်း)**: Segment into syntactic words (`ပုဒ်`) using statistical/neural decoding (CRF, BiLSTM-CRF, or `UnifiedCut`) combined with lexicon protection and morphosyntactic post-rules (`references/segmentation-lexicon.md`). Do not use naive greedy dictionary lookup for corpora destined for POS tagging (requires Boundary F1 >= 0.95).
6. **Contextual POS Tagging**: Assign tags from the lowercase 15-tag `myPOS` inventory (`abb, adj, adv, conj, fw, int, n, num, part, ppm, pron, punc, sb, tn, v`) based on syntactic role in context, not static dictionary lookup (`references/pos-ud-mapping.md`).

## 2. Named Entity Recognition (NER) & Boundary Alignment

The authoritative Named Entity Recognition framework for Myanmar text (`ner-mya-v2`) is governed by the **15-Class Canonical Taxonomy**, **BIO Sequence Labeling Invariants**, and the **Zero-Clitic Bleed Principle**.

### 2.1 The 15-Class Canonical NER Taxonomy & Specifications

Every entity span is assigned one of the 15 standardized classes:

| Class | Tag | Formal Linguistic Definition & Scope | Representative Myanmar Corpus Examples |
| :--- | :---: | :--- | :--- |
| **Geo-Political Entity** | `GPE` | နိုင်ငံ၊ ပြည်နယ်၊ တိုင်းဒေသကြီး၊ ခရိုင်၊ မြို့၊ မြို့နယ်၊ ကျေးရွာ အုပ်ချုပ်ရေးဒေသများ။ ဒေသအမည်နှင့် အုပ်ချုပ်ရေးယူနစ်ကို သီးခြား token ဖြတ်ထားပါက multi-token span (`B-GPE I-GPE`) အဖြစ် တွဲဆက်သတ်မှတ်သည်။ | `မြန်မာ`, `ထိုင်း`, `တရုတ်`, `အမေရိကန်`, `ရခိုင် ပြည်နယ်`, `ရန်ကုန် တိုင်းဒေသကြီး`, `မောင်တော မြို့နယ်`, `စစ်တွေ မြို့`, `ဝါရှင်တန်`, `ဘေဂျင်း` |
| **Location (Physical)** | `LOC` | မြစ်၊ ချောင်း၊ တောင်၊ သမုဒ္ဒရာ၊ ပင်လယ်၊ ရေလက်ကြား၊ တိုက်ကြီးများနှင့် ရုပ်ပိုင်းဆိုင်ရာ ပထဝီဝင်ဒေသများ (GPE မဟုတ်သော ဒေသများ)။ | `ဧရာဝတီမြစ်`, `ချင်းတွင်းမြစ်`, `သံလွင်မြစ်`, `ရခိုင်ရိုးမ`, `ဘင်္ဂလားပင်လယ်အော်`, `ကပ္ပလီပင်လယ်`, `ဟော်မုဇ်ရေလက်ကြား`, `အာရှ`, `ဥရောပ`, `အရှေ့အလယ်ပိုင်း` |
| **Organization** | `ORG` | အစိုးရဌာန၊ ဝန်ကြီးဌာန၊ နိုင်ငံရေးပါတီ၊ တပ်မတော်၊ လက်နက်ကိုင်တပ်ဖွဲ့၊ နိုင်ငံတကာအဖွဲ့အစည်း၊ ကုမ္ပဏီ၊ တက္ကသိုလ်၊ အားကစားအသင်းများ။ | `ကုလသမဂ္ဂ`, `အာဆီယံ`, `အီးယူ`, `နေတိုး`, `NUG`, `CRPH`, `PDF`, `AA`, `KIA`, `KNU`, `စစ်တပ်`, `စစ်ကောင်စီ`, `ပြည်ထောင်စု အစိုးရ အဖွဲ့`, `OpenAI`, `Apple`, `အာဆင်နယ်` |
| **Person** | `PER` | လူပုဂ္ဂိုလ်အမည်၊ နိုင်ငံ့ခေါင်းဆောင်၊ တပ်မှူး၊ သမိုင်းဝင်ပုဂ္ဂိုလ်၊ အနုပညာရှင်၊ အားကစားသမားများ။ **လူမှုရေး/တိုင်းရင်းသား အမည်ရှေ့ဆက်များ (`ဦး, ဒေါ်, ကို, မ, မောင်, စဝ်, စော, နော်, စလိုင်း, ဆလိုင်း, မိုင်း, ဒူဝါ, နိုင်, မန်း`) အား အမည်နှင့် ပေါင်းစည်း၍ `B-PER` သတ်မှတ်သည်**။ | `ဒေါ်အောင်ဆန်းစုကြည်`, `ဦးမင်းအောင်လှိုင်`, `စဝ်စံထွန်း`, `စောမုတ်သုန်`, `ဒူဝါလရှီးလ`, `ထရမ့်`, `ပူတင်`, `ရှီကျင့်ဖျင်`, `မက်ဆီ`, `ဟာလန်း` |
| **Date** | `DATE` | သက္ကရာဇ်၊ ခုနှစ်၊ လ၊ ရက်စွဲ၊ သမိုင်းဝင်ခေတ်ကာလ၊ နှစ်ကာလအပိုင်းအခြားများ။ | `၂၀၂၆ ခုနှစ်`, `မေလ`, `ဇန်နဝါရီ ၄ ရက်`, `လွန်ခဲ့သည့် ၃ နှစ်`, `၁၉၄၇ ခုနှစ် ဇူလိုင်လ` |
| **Time** | `TIME` | အချိန်နာရီ၊ မိနစ်၊ စက္ကန့်၊ အချိန်သတ်မှတ်ချက်များ။ | `မနက် ၈ နာရီ`, `ညနေ ၄ နာရီခွဲ`, `၂၄ နာရီ`, `၁ နာရီ ၁၅ မိနစ်` |
| **Numerical Quantity** | `NUM` | အရေအတွက်၊ ရာခိုင်နှုန်း၊ အတိုင်းအတာ၊ ကိန်းဂဏန်းစာရင်းအင်းများ (ငွေကြေးနှင့် ရက်စွဲမဟုတ်သော ပမာဏများ)။ | `၂၀%`, `၅၀ ရာခိုင်နှုန်း`, `လူ ၁၀၀`, `သုံးဆ`, `၁၀ ဦး` |
| **Monetary Sum** | `MONEY` | ငွေကြေးပမာဏ၊ နိုင်ငံတကာသုံး ငွေကြေးယူနစ်များနှင့် ဈေးနှုန်းတန်ဖိုးများ။ | `ကျပ် ၁၀ သိန်း`, `ဒေါ်လာ ၂ သန်း`, `ယူရို ၄၅ သန်းခွဲ`, `ဘတ် ၆ သိန်း`, `ပေါင် ၅၂` |
| **Domain Terminology** | `TERM` | စစ်ဘက်၊ နည်းပညာ၊ ဥပဒေနှင့် သိပ္ပံဆိုင်ရာ သီးသန့်အသုံးအနှုန်းများ။ | `တိုက်ပွဲ`, `တော်လှန်ရေး`, `စစ်ရှောင်`, `စစ်ကြောင်း`, `လုံခြုံရေး`, `ဆိုက်ဘာလုံခြုံရေး`, `AI`, `LLM`, `5G`, `ပုဒ်မ ၅၀၅ ( က )` |
| **Named Event** | `EVENT` | အားကစားပြိုင်ပွဲ၊ ညီလာခံ၊ ပွဲတော်၊ သမိုင်းဝင်စစ်ဆင်ရေး၊ ရွေးကောက်ပွဲများ။ | `ကမ္ဘာ့ဖလား`, `ကမ္ဘာ့ဖလား ဘောလုံးပြိုင်ပွဲ`, `ချန်ပီယံလိဂ်`, `ပရီးမီးယားလိဂ်`, `အိုလံပစ်`, `ရွေးကောက်ပွဲ`, `သင်္ကြန်ပွဲတော်`, `ရှန်ဂရီလာ ဆွေးနွေးပွဲ` |
| **Product** | `PRODUCT` | ကူးသန်းရောင်းဝယ်ရေး ထုတ်ကုန်၊ ဆော့ဖ်ဝဲလ်၊ အက်ပ်၊ စက်ပစ္စည်း၊ အာကာသယာဉ်များ။ | `iPhone`, `iPad`, `MacBook`, `ChatGPT`, `Starlink`, `Falcon 9`, `Starship`, `Windows`, `Android` |
| **Facility** | `FACILITY` | လူလုပ်အဆောက်အအုံ၊ လေဆိပ်၊ တံတား၊ ဆိပ်ကမ်း၊ စခန်း၊ နန်းတော်များ။ | `အိမ်ဖြူတော်`, `ပင်တဂွန်`, `ကရမ်လင်`, `ရန်ကုန် အပြည်ပြည်ဆိုင်ရာ လေဆိပ်`, `ဆီဒိုးနား ဟိုတယ်` |
| **Nationality / Group** | `NORP` | နိုင်ငံသား၊ လူမျိုးစု၊ နိုင်ငံရေး/ဘာသာရေးအုပ်စုများ။ | `မြန်မာနိုင်ငံသား`, `တရုတ်နိုင်ငံသား`, `ကရင်လူမျိုး`, `ရိုဟင်ဂျာ`, `ရီပတ်ဘလစ်ကန်`, `ဒီမိုကရက်`, `ပျူစောထီး` |
| **Disease / Phenomenon** | `DISEASE_PHENOMENON` | ကူးစက်ရောဂါ၊ ဆေးပညာရောဂါဘယ၊ တိုက်ဖွန်းမုန်တိုင်းနှင့် ရာသီဥတုဖြစ်စဉ်များ။ | `ကိုဗစ်-၁၉`, `Covid-19`, `ဆားစ်`, `ရာဂိ မုန်တိုင်း`, `အယ်လ်နီညို`, `လာနီညာ` |
| **Miscellaneous** | `MISC` | တရားဝင်စာချုပ်၊ ဆုတံဆိပ်၊ ပြဋ္ဌာန်းချက်၊ ဘာသာစကားအမည်များ။ | `ဂျီနီဗာ ကွန်ဗင်းရှင်း`, `နိုဘယ်လ်ဆု`, `အော်စကာဆု`, `မြန်မာစာ`, `အင်္ဂလိပ်ဘာသာ` |

---

### 2.2 Word Segmentation vs. NER Span Rules & Structural Invariants

| Invariant / Category | Word Segmentation (WS) Rule | BIO Tagging & Span Boundary Rule | Example |
| :--- | :--- | :--- | :--- |
| **Personal Names (`PER`) vs. Titles/Ranks** | • အမည်ရှေ့ဆက်များ (`ဦး, ဒေါ်, ကို, မ, စဝ်, စော, နော်, စလိုင်း, ဆလိုင်း, မိုင်း, ဒူဝါ, နိုင်, မန်း`) ကို အမည်နှင့် **မခွဲရ** (`1 Token /n`)။<br>• ရာထူး၊ အဆင့်အတန်း၊ ဂုဏ်ပုဒ်များ (`ဗိုလ်ချုပ်ကြီး, သံအမတ်ကြီး, စော်ဘွားကြီး, ဒေါက်တာ, သမ္မတ`) ကို သီးခြားခွဲထုတ်ရမည် (`/n`)။ | • Personal name token အား `B-PER` သတ်မှတ်သည်။<br>• ရာထူး/ဂုဏ်ပုဒ် token အား Outside (`O`) သတ်မှတ်သည်။ | `[ဦးမင်းအောင်လှိုင်/n]_B-PER`<br>`[ဒေါ်အောင်ဆန်းစုကြည်/n]_B-PER`<br>`မိုင်းပွန်/B-GPE စော်ဘွားကြီး/O [စဝ်စံထွန်း/n]_B-PER`<br>`သံအမတ်ကြီး/O [ဦးကျော်မိုးထွန်း/n]_B-PER`<br>`ဗိုလ်ချုပ်/O [အောင်ဆန်း/n]_B-PER`<br>`ဒေါက်တာ/O [ဇော်ဝေစိုး/n]_B-PER` |
| **Administrative Units (`GPE`)** | ဒေသအမည်သီးသန့်နှင့် အုပ်ချုပ်ရေးယူနစ် (`ပြည်နယ်, တိုင်းဒေသကြီး, မြို့နယ်, ခရိုင်, မြို့, ရွာ`) ကို သီးခြားခွဲထားသည်။ | Multi-token span အဖြစ် `B-GPE I-GPE` တွဲဆက်သတ်မှတ်သည်။ | `[ရခိုင်/n]_B-GPE [ပြည်နယ်/n]_I-GPE`<br>`[မောင်တော/n]_B-GPE [မြို့နယ်/n]_I-GPE`<br>`[ရန်ကုန်/n]_B-GPE [မြို့/n]_I-GPE` |
| **Institutional Phrases (`ORG`)** | Owner 10-Row component splits အတိုင်း ခွဲထားသည်။ | Institutional noun phrase တစ်ခုလုံးအား `B-ORG I-ORG...` သတ်မှတ်သည်။ | `[ပြည်ထောင်စု/n]_B-ORG [အစိုးရ/n]_I-ORG [အဖွဲ့/n]_I-ORG` |
| **Dates & Citations (`DATE` / `MISC`)** | ဂဏန်းသင်္ချာ (`num`) နှင့် ယူနစ်နာမ် (`n`) ကို သီးခြားခွဲထားသည်။ | နေ့စွဲကာလတစ်ခုလုံးအား `B-DATE I-DATE` သတ်မှတ်သည်။ ကွင်းစ/ကွင်းပိတ်ကို ပြင်ပတွင် ထားသည်။ | `[၂၀၂၆/num]_B-DATE [ခုနှစ်/n]_I-DATE`<br>`[မေလ/n]_B-DATE [၁၀/num]_I-DATE [ရက်/n]_I-DATE` |

---

### 2.3 The Zero-Clitic Bleed Principle (ဝိဘတ်မဲ့ သီးသန့်စံ)

**သံမဏိစည်းမျဉ်း (Ironclad Invariant)**: မည်သည့် Entity Span အတွင်း၌မျှ နာမ်ဝိဘတ် (`ppm`)၊ သမ္ဗန္ဓ (`conj`) သို့မဟုတ် အောက်ပါ Clitic စာလုံးများ ကပ်ပါခွင့် **လုံးဝ မရှိစေရ**-
`COMMON_CLITICS = {'သည်', 'က', 'ကို', 'အား', '၌', 'တွင်', 'မှ', 'သို့', '၏', 'ရဲ့', 'ဖြင့်', 'နှင့်', 'နဲ့', 'အတွက်', 'ကြောင့်'}`

- ❌ **အမှား (Clitic Bleed)**: `[မြန်မာနိုင်ငံသို့]_GPE`၊ `[ဦးမင်းအောင်လှိုင်က]_PER`၊ `[စစ်တပ်သည်]_ORG`၊ `[ရန်ကုန်တွင်]_GPE`
- ✅ **အမှန် (Zero-Clitic Standard)**:
  - `မြန်မာနိုင်ငံသို့` $\rightarrow$ `မြန်မာ/n နိုင်ငံ/n သို့/ppm` $\rightarrow$ `မြန်မာ/B-GPE` `နိုင်ငံ/I-GPE` `သို့/O`
  - `ဦးမင်းအောင်လှိုင်က` $\rightarrow$ `ဦးမင်းအောင်လှိုင်/n က/ppm` $\rightarrow$ `ဦးမင်းအောင်လှိုင်/B-PER` `က/O`
  - `စစ်တပ်သည်` $\rightarrow$ `စစ်တပ်/n သည်/ppm` $\rightarrow$ `စစ်တပ်/B-ORG` `သည်/O`
  - `ရန်ကုန်တွင်` $\rightarrow$ `ရန်ကုန်/n တွင်/ppm` $\rightarrow$ `ရန်ကုန်/B-GPE` `တွင်/O`

### 2.4 BIO Sequence Labeling Invariants (BIO အထားအသို စည်းမျဉ်းများ)

1. **စတင်ခြင်း (Beginning)**: Entity တစ်ခု စတင်တိုင်း `B-[TYPE]` ဖြင့် စတင်ရမည် (ဥပမာ - `B-GPE`, `B-PER`)။
2. **ဆက်စပ်ခြင်း (Continuation)**: Entity သည် Token တစ်ခုထက် ပိုပါက နောက်ဆက်တွဲ Token များကို `I-[TYPE]` ဖြင့်သာ သတ်မှတ်ရမည်။
3. **တားမြစ်ချက် (No Orphan `I-`)**: ရှေ့တွင် `B-[TYPE]` သို့မဟုတ် တူညီသော `I-[TYPE]` မရှိဘဲ `I-[TYPE]` တိုက်ရိုက် ရောက်ရှိလာခြင်း (`O` နောက်တွင် `I-[TYPE]` ကပ်ပါခြင်း သို့မဟုတ် `B-ORG` နောက်တွင် `I-GPE` လိုက်ခြင်း) သည် တရားမဝင်သော Labeling Violation ဖြစ်သည်။
4. **အမည်ကွဲ လက်သည်းကွင်း (Alias Parentheticals)**:
   - တရားဝင်အမည်ကွဲဖော်ပြချက်များ (ဥပမာ - `ဦးစိန်ညွန့် ( ခ ) ဦးတင်မောင်`) တွင် `( ခ )` သို့မဟုတ် `( ခေါ် )` အား `O` ထားပြီး နှစ်ဖက်အမည်များကို သီးခြား `B-PER` များအဖြစ် ခွဲထုတ်သတ်မှတ်ရမည်-
     - `ဦးစိန်ညွန့်/B-PER (/O ခ/O )/O ဦးတင်မောင်/B-PER`

---

### 2.5 Authoritative Large-Scale NER Datasets & Gazetteers (`release_v1.1`)

The news-corpus release v1.1 is a separate dataset owned with the corpus, not a path inside this skill. Do not assume `/Volumes/Extreme SSD/...` exists. Download it only when the user asks, via `scripts/fetch_corpus_v1_1_from_gdrive.py` on a machine that has the `gdrive` CLI. The release provides:

1. **Grounded Parallel Sentences (`sentences/parallel_sentences_5d.jsonl.gz`)**:
   - **173,176 parallel Myanmar-English sentences** with character-offset aligned NER spans (`text`, `type`, `start_char`, `end_char`, `confidence`) and 5D document metadata.
2. **Global Entity Catalog (`mappings/ner_entity_catalog.json.gz`)**:
   - **42,210 unique named entities** with **167,650 verified mentions** across 15 canonical classes:
     - `TERM`: 8,887 entities | `PER`: 8,602 entities | `ORG`: 8,306 entities
     - `NUM`: 5,177 entities | `GPE`: 3,882 entities | `LOC`: 2,525 entities
     - `DATE`: 2,097 entities | `MONEY`: 1,911 entities | `TIME`: 680 entities
     - `EVENT`: 66 entities | `PRODUCT`: 49 entities | `FACILITY`: 19 entities
     - `DISEASE_PHENOMENON`: 6 entities | `MISC`: 3 entities
3. **Linguistic Audit & Remediation Inventories (`audit_and_reports/`)**:
   - `INVENTORY_POSTPOSITIONS.md`: 234 postposition/particle infiltration patterns (`များ`, `က`, `တို့`, `ကို`, `အတွင်း`, `မှာ`, `သို့`, `မှ`, `အတွက်`) and zero-clitic detachment rules.
   - `INVENTORY_COMPOUND_SUFFIXES.md`: 102 truncated compound head suffixes (`ပြိုင်ပွဲ`, `အသင်း`, `ရွာ`, `ကျေးရွာ`, `ရပ်ကွက်`, `အဖွဲ့`, `လေဆိပ်`) and compound expansion rules.
   - `NER_15TYPE_REANNOTATION_REPORT.md` & `NER_TAXONOMY_DISCOVERY_REPORT.md`: Complete reannotation reports across 11,567 proposals with 99.4% precision.

## 3. Dependency Parsing & Syntactic Treebanks (`CoNLL-U` / `myUDTree`)

Myanmar is a strictly head-final, Subject-Object-Verb (**SOV**) postpositional language (Chapters 15, 18, 19). When constructing or parsing Universal Dependencies (`CoNLL-U`) or converting between constituency clauses and dependency trees:

### Core Head-Attachment Principles

1. **Clause Root (`root`)**: The finite main verb (`v`) at the end of the main clause (`အမှီခံဝါကျ`) is the `root` of the sentence (`HEAD = 0`).
2. **Postpositional Case Markers (`case`)**: Noun case markers (`ppm`: `သည်`, `က`, `မှာ`, `ကို`, `အား`, `မှ`, `သို့`, `တွင်`, `၌`, `ဖြင့်`, `နှင့်`, `၏`, `ရဲ့`) attach **leftward** to their preceding nominal head (`N <--case-- PPM`), while the nominal head attaches **rightward** to the governing verb (`N --nsubj/obj/obl--> V`) or modified noun (`N --nmod--> N`).
3. **Verbal Auxiliaries & Particles (`aux` / `mark` / `advmod`)**:
   - Post-verbal auxiliaries and aspect/modality particles (`part`: `ခဲ့`, `နေ`, `ပြီး`, `နိုင်`, `ရ`, `စေ`, `သင့်`, `ထား`, `လာ`, `သွား`, `ပေး`, `လိမ့်`, `ပါ`, `ဘူး`) attach **leftward** to the main verb (`V <--aux/mark-- PART`).
   - Pre-verbal negation `မ` (`part`) attaches **rightward** to the negated verb (`မ --advmod/aux--> V`).
   - Sentence-final realis/irrealis markers (`သည်`, `မည်`, `ပြီ`, `၏`, `တယ်`, `မယ်`) attach **leftward** to the main verb.
4. **Subordinate Clauses (Chapter 19 -> UD Clauses)**:
   - **Adnominal / Relative Clause (`နာမဝိသေသနဝါကျကဏ္ဍ` -> `acl`)**: In `[V + သော/သည့်/တဲ့] + N`, the relative verb attaches **rightward** to the modified head noun as `acl`, and the relativizer (`သော`, `သည့်`, `တဲ့`) attaches **leftward** to the relative verb as `mark`.
   - **Adverbial Clause (`ကြိယာဝိသေသနဝါကျကဏ္ဍ` -> `advcl`)**: In `[V + သဖြင့်/သောကြောင့်/သော်လည်း/လျှင်/၍/ပြီး] ... V_main`, the subordinate verb attaches **rightward** to `V_main` as `advcl`, and the subordinating conjunction/particle attaches **leftward** to the subordinate verb as `mark`.
   - **Nominal / Complement Clause (`နာမ်ဝါကျကဏ္ဍ` -> `ccomp` / `xcomp` / `nsubj`)**: Clauses nominalized with `ခြင်း`, `မှု`, `ကြောင်း`, `ရန်`, `ဖို့` attach to the matrix predicate as core or oblique arguments.
5. **Numeral & Classifier Constructions (`nummod` / `clf`)**:
   - In `N + NUM/TN + CLF` (e.g., `လူ/n သုံး/tn ဦး/part`), `သုံး` and `ဦး` form a quantifier phrase modifying `လူ` (`nummod`).

## 4. Corpus Indexing, WPL `.vert`, CQL & Word Sketch

When exporting or querying Myanmar corpora in Sketch Engine / WPL `.vert` format (`corpus_manager` Stage 3):

- **Vertical Formats**:
  - **v1 (3-column)**: `word<TAB>xpos<TAB>lemma` inside `<doc>` and `<s>...</s>` blocks.
  - **v2 (5-column dependency vertical)**: Begins with header `#VERT v2 columns=word,xpos,lemma,head,deprel`.
- **CQL Query Rules on `myPOS` Corpora**:
  - Always target `xpos` (the 15-tag lowercase myPOS layer), not `upos` or `lemma`, unless the target vertical explicitly populates them.
  - **Numeral Queries**: Because digits are tagged `num` (`၁၀`, `၁၀၀`) and spelled numbers are tagged `tn` (`တစ်`, `နှစ်`, `တစ်ရာ`), any CQL rule matching numerals before classifiers must include both (`[xpos="tn|num"]`).
  - **Empirically Verified Syntactic Sketch Frames**:
    - **Subject (`ကတ္တား`)**: `[xpos="n|pron|abb"] [word="သည်|က|မှာ" & xpos="ppm"] []{0,4} [xpos="v"]`
    - **Object (`ကံ`)**: `[xpos="n|pron|abb"] [word="ကို|အား" & xpos="ppm"] []{0,3} [xpos="v"]`
    - **Locative (`နေရာ/အချိန်`)**: `[xpos="n|pron"] [word="တွင်|၌|မှာ|ထဲ" & xpos="ppm"] []{0,4} [xpos="v"]`
    - **Relative Clause (`နာမဝိသေသနဝါကျကဏ္ဍ`)**: `[xpos="v"] [word="တဲ့|သော|သည့်" & xpos="part"] [xpos="n|pron"]`
    - **Adjectival Modification**: Bare `[xpos="adj"] [xpos="n"]` (accounts for ~86% of adjectival hits) plus marker-mediated `[xpos="adj"] [word="သော|တဲ့|သည့်"] [xpos="n"]`
    - **Genitive (`ပိုင်ဆိုင်ရာ`)**: `[xpos="n|pron"] [word="၏|ရဲ့" & xpos="ppm"] [xpos="n"]`
- **GDEX (Good Dictionary Examples) Heuristics**:
  - Prefer complete sentences (`is_whole_sentence`) starting with a valid Myanmar head letter and ending with `။`.
  - Optimal sentence length: **8 to 22 syntactic words**.
  - Penalize high density of `fw`, `abb`, `sb`, raw digits, or unbalanced brackets.

## 5. Neural Machine Translation (NMT) & Parallel Corpora

1. **Pre-BPE Syntactic Word Tokenization**: Applying BPE or SentencePiece directly to unsegmented Burmese merges case markers (`ကို`, `သည်`, `မှာ`) and verbal particles (`ခဲ့`, `နိုင်`, `သည်`) with adjacent content syllables across word boundaries. Always segment into syntactic words first, then apply subword tokenization (or use space-preserving markers) so subword units respect morpheme boundaries.
2. **Structural Reordering (SOV <-> SVO)**:
   - Map Burmese postpositional phrases (`[NP] + PPM`) to English prepositional phrases (`PREP + [NP]`).
   - Unpack left-branching Burmese relative clauses (`[RC + သော/သည့်] + Head_NP`) into right-branching English relative clauses (`Head_NP + [that/which/who + RC]`).
   - Preserve modality and negation polarity carefully (`မ + [V] + နိုင် + သေး + ပါ` -> "cannot yet [V]").

## 6. LLM Tokenization, RAG Chunking & Prompt Engineering

1. **Grapheme-Safe Text Chunking**:
   - Standard character-length splitters (`chunk_size=500`) frequently slice Myanmar grapheme clusters in half, separating a base consonant (`\u1000..\u1021`) from its pre-base vowel `ေ` (`\u1031`), medials (`\u103B..\u103E`), asat (`\u103A`), or tone marks (`\u1037,\u1038`).
   - **Rule**: Always split chunks on sentence boundaries (`။` followed by whitespace/newline), paragraph breaks (`\n\n`), or clause boundaries (`၊` following a subordinate marker). If hard character truncation is unavoidable, snap the split point to a valid syllable boundary where the next character is not in `ILLEGAL_B_CHARS` (`\u102B..\u103E`, `\u1056..\u1059`).
2. **Lexicon-Grounded Prompting**:
   - When using LLMs for Myanmar annotation, inject the explicit 15-tag table and boundary-shift trap pairs into the prompt and verify output with `scripts/validate_nlp_corpus.py` to enforce zero character drift.

## 7. Speech Processing (TTS, ASR, G2P Phonemic Conversion)

Use Chapters 4, 5, 6, and 7 for Grapheme-to-Phoneme (G2P) and ASR lexicon construction, while keeping orthographic text unchanged:

1. **Voicing Sandhi (သံပြင်းမှ သံပျော့သို့ ကူးပြောင်းခြင်း - Chapter 7)**:
   - After a **smooth vowel rhyme** or **nasal rhyme** (`-င်, -န်, -မ်, -ံ, -ဉ်`), voice the initial unaspirated/aspirated obstruent of the following closely bound syllable inside a compound or affixed word:
     - `က / ခ` -> `[ဂ]` (e.g., `ရွှေကျောင်း` -> `[ရွှေဂျောင်း]`, `စာသင်ခန်း` -> `[ဇာဒင်ဂန်း]`)
     - `စ / ဆ` -> `[ဇ]` (e.g., `စာအုပ်` -> `[ဇာအုပ်]`)
     - `တ / ထ` -> `[ဒ]` (e.g., `စာသင်တိုက်` -> `[ဇာဒင်ဒိုက်]`)
     - `ပ / ဖ` -> `[ဗ]` (e.g., `မီးပုံး` -> `[မီးဗုံး]`)
   - **Blocking Environments (Do Not Voice)**:
     - After a **stopped/glottal rhyme** (`-က်, -စ်, -တ်, -ပ်`): `သစ်ပင်` -> `[သစ်ပင်]` (never `*[သစ်ဗင်]`), `လက်ခေါက်` -> `[လက်ခေါက်]`.
     - Across major syntactic boundaries (between separate phrases or after pause `၊`) and in unassimilated Pali/foreign loanwords.
2. **Vowel Weakening (အသံလျော့ခြင်း / Schwa Reduction)**:
   - In `တစ်` + classifier (`တစ်ခု` -> `[တခု / tə kʰṵ]`) and `အ-` prefix nouns (`အကောင်` -> `[အဂောင် / ə ɡàʊɴ]`), the first syllable reduces to `/ə/` in natural speech (TTS/ASR pronunciation dictionary), even though orthographic text strictly preserves `တစ်` or `တ` as written in the source.

## 8. Sentiment Analysis, Negation Scope & Information Extraction

1. **Negation Scope (`မ ... [Aux] ... [Ending]`)**:
   - In Myanmar, negation `မ` precedes the main verb (or the final verb/auxiliary in a compound predicate: `အတည် မ ပြု`, `လက်ခံ နိုင် ခြင်း မ ရှိ`), while negative polarity particles (`ဘူး`, `ပါ`, `ချေ`, `ပေ`, `သေး`, `တော့`) follow the verb.
   - **Double / Correlative Negation (Positive or Conditional Polarity)**:
     - `မ [V] မချင်း` ("until [V]")
     - `မ [V] ဘဲ မ နေ` ("cannot help but [V]" -> affirmative)
     - `[V] သည် ဖြစ်စေ ၊ မ [V] သည် ဖြစ်စေ` ("whether [V] or not" -> conditional/exhaustive, neutral polarity)
   - **Lexicalized `မ` (Not Syntactic Negation)**: Do not flip clause polarity on lexicalized idioms or nouns containing `မ` (`တရားမ` = civil law, `သွေးကြောမကြီး` = main artery, `ခန်းမ` = hall, `မသန်မစွမ်း` = disabled, `မတော်တဆ` = accidental, `သို့မဟုတ်` = or).
2. **Modality & Legal Deontic Extraction**:
   - **Obligation / Mandate**: `[V] ရ မည်` ("shall [V]"), `[V] သင့် သည်` ("should [V]"), `[V] အပ် သည်`.
   - **Permission / Right**: `[V] နိုင် သည်` ("may [V]"), `[V] ခွင့် ရှိ သည်` ("has the right to [V]"), `[V] ပိုင် ခွင့်`.
   - **Prohibition**: `မ [V] ရ` ("shall not [V]"), `[V] ခြင်း မ ပြု ရ` ("must not perform [V]").
