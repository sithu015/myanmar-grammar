# Large-Corpus Chunking, Line-by-Line Streaming & Staged Regex Remediation Pipeline

This reference defines the architecture and operational rules for processing large Myanmar NLP corpora (such as `Legal70k` with 70,242+ lines or `segmented_mm.txt` with 899,000+ lines) using **deterministic chunking**, **line-by-line streaming inspection and remediation**, and a **6-stage token-bounded regex cascade**.

## 1. Large-Corpus Chunking & Sub-Chunking Architecture (Chunk လုပ်ဆောင်ခြင်း စနစ်)

When a corpus file exceeds memory or LLM context/output limits, never process or rewrite the entire file in a single unbounded pass. Split the file into deterministic, line-indexed chunks and sub-chunks:

### 1.1 Two-Tier Chunk Sizing Strategy

| Tier | Recommended Size | Target Use Case | Output Format |
| --- | --- | --- | --- |
| **Primary Batch Chunk** | `1,000` to `2,000` lines (or `250` lines for dense legal JSON) | Automated batch validation, CRF/UnifiedCut inference, and milestone checkpointing | `chunk_lines_00001_01000.txt` / `.json` |
| **Inspection Sub-Chunk** | `50` to `100` lines | Human-in-the-loop review and LLM line-by-line audit (guarantees zero output truncation) | `subchunk_lines_00251_00350.json` / `_compact.txt` |

### 1.2 Chunking Invariants (Never Violate)

1. **1-Based Global Line Number Preservation**: Every chunk and sub-chunk record must retain its original 1-based global `line_number` from the master source file (`1 .. N`). Never reset line numbers to `1` inside chunk files.
2. **Manifest & Checksum Tracking**: When splitting a file, emit a `manifest.json` recording the source `sha256`, `total_lines`, and each chunk's `chunk_id`, `start_line`, `end_line`, `line_count`, and `sha256`.
3. **Lossless Reassembly (`merge`)**: Before merging chunks back into a master release file, verify:
   - Contiguous, non-overlapping line ranges covering `1 .. N` with zero missing or duplicate lines.
   - Exact non-whitespace character conservation (`strip_ws(merged_line) == strip_ws(original_line)`) on every line.
   - Exact WS-to-POS token parity (`len(ws_tokens) == len(pos_tokens)`).

### 1.3 CLI Commands for Chunking & Merging

```bash
# Split a large corpus into 1000-line chunks and 100-line review sub-chunks
python3 scripts/corpus_chunk_and_remediate.py chunk \
  --input legal_70k_ws.txt \
  --outdir chunks_ws \
  --chunk-size 1000 \
  --subchunk-size 100

# Merge audited/remediated chunks back into a unified file with full parity verification
python3 scripts/corpus_chunk_and_remediate.py merge \
  --manifest chunks_ws/manifest.json \
  --output legal_70k_ws_merged.txt \
  --reference legal_70k_ws.txt
```

---

## 2. Line-by-Line Streaming Inspection & Remediation (Line-by-Line စစ်ဆေးပြင်ဆင်ခြင်း)

Process files line by line using a streaming generator (`enumerate(infile, start=1)`) with $O(1)$ memory overhead per line:

```text
Raw/Candidate Line (line_no)
   │
   ├─► 1. Pre-Read Snapshot: orig_chars = re.sub(r"\s+", "", raw_surface)
   ├─► 2. Stage 1..5 Cascaded Regex & Token-Level Remediation
   ├─► 3. Stage 6 Verification Gate:
   │      ├─ Check: re.sub(r"\s+", "", new_surface) == orig_chars
   │      │    └─ If mismatch -> ROLLBACK line to original & log CHAR_CONSERVATION_ROLLBACK
   │      ├─ Check: WS <-> POS token count parity & 15-tag vocabulary compliance
   │      └─ Scan: 8 Owner Record-Only Typo Leads -> log as RECORD_ONLY_NOT_APPLIED
   └─► 4. Emit remediated line + append diffs to remediation_ledger.tsv
```

### Key Line-by-Line Guardrails

- **Automatic Rollback on Character Drift**: A segmentation or POS rule may only add/remove whitespace or update `/tag` labels. If a regex bug alters even a single Myanmar codepoint, the engine automatically restores the original line and flags the line in the audit log.
- **Dual-Stream Synchronization**: When processing POS lines (`word/tag`), derive the companion WS line directly from the remediated POS tokens (`" ".join(w for w, _ in tokens)`) so WS and POS files can never drift out of alignment.
- **Append-Only Change Ledger**: Every line modified by any stage writes a structured row to `remediation_ledger.tsv` (`line_number`, `stage`, `rule_id`, `before`, `after`).

---

## 3. Six-Stage Cascaded Regex Remediation System (Regex နှင့် အဆင့်လိုက် ပြင်ဆင်ခြင်း စနစ်)

Naive, unordered regex replacements in Burmese cause severe boundary regressions (for example, a naive regex splitting `မြန်မာနိုင်ငံ` will corrupt `မြန်မာနိုင်ငံသား` into `မြန်မာ နိုင်ငံသား`, or splitting `တရား` inside `ယန္တရား`). Always execute regex rules in **6 ordered stages** using strict **whitespace/token boundary lookarounds** (`(?<!\S)...(?!\S)`):

### Stage 1: Orthographic & Structural Boundary Recovery (အက္ခရာနှင့် ကွင်းစကွင်းပိတ် ပြန်ညှိခြင်း)

Fixes broken grapheme clusters and punctuation spacing before any lexical matching runs:

| Rule ID | Target Defect | Token-Bounded Regex Pattern | Replacement |
| --- | --- | --- | --- |
| `S1_KINZI_JOIN` | Space-broken kinzi (`ဆန္ ဒမဲ`, `ကုမ္ ပဏီ`) | `(\u1004\u103a\u1039)\s+` | `\1` |
| `S1_VIRAMA_JOIN` | Space-broken stacked consonant | `(\u1039)\s+` | `\1` |
| `S1_DEP_SIGN_JOIN` | Orphaned dependent vowel/asat/tone at token start (`ခ ံ` -> `ခံ`) | `(?<=\S)\s+([\u102b-\u103e\u1056-\u1059]+)` | `\1` |
| `S1_BRACKET_PAD` | Unpadded brackets/parentheses (`(က)` -> `( က )`) | `([(\[{])\s*([^\s()\[\]{}]+)\s*([)\]}])` | `\1 \2 \3` |
| `S1_SHATTERED_TYPO` | Shattered archaic/OCR words (join without modernizing spelling) | `(?<!\S)ဦး\s+စီ\s+ချုပ်(?!\S)`<br>`(?<!\S)ပြည်\s+တောင်\s+စု(?!\S)`<br>`(?<!\S)အ\s+ထင်း\s+အ\s+ရှား(?!\S)` | `ဦးစီချုပ်`<br>`ပြည်တောင်စု`<br>`အထင်းအရှား` |

### Stage 2: Protected Multi-Syllable Lexemes & `[တ/တစ် + X + တ/တစ် + Y]` Idioms

Re-joins over-split lexicalized idioms and fixes boundary shifts around them while preserving `တ` vs `တစ်` spelling:

| Rule ID | Target Defect | Token-Bounded Regex Pattern | Replacement |
| --- | --- | --- | --- |
| `S2_TA_IDIOM_JOIN` | Shattered 4-syllable `တ/တစ်` idioms | `(?<!\S)(တ(?:စ်)?)\s+စုံ\s+(တ(?:စ်)?)\s+(ရာ|ဦး|ယောက်|ခု)(?!\S)` | `\1စုံ\2\3` |
| `S2_TA_BOUNDARY_SHIFT` | Boundary shift (`ကိစ္စတစုံ တရာ`, `တစုံ တရာသော`) | `(?<!\S)ကိစ္စ(တ(?:စ်)?စုံ)\s+(တ(?:စ်)?ရာ)(?!\S)`<br>`(?<!\S)(တ(?:စ်)?စုံ)\s+(တ(?:စ်)?ရာ)(သော\|သည်\|ကို\|က)(?!\S)` | `ကိစ္စ \1\2`<br>`\1\2 \3` |
| `S2_TA_FIXED_JOIN` | Over-split fixed `တ/တစ်` compounds (`တ ပြိုင် နက်`, `တ ဖက် သတ်`, `တ ခါ တ ရံ`) | `(?<!\S)(တ(?:စ်)?)\s+ပြိုင်\s*နက်(?!\S)`<br>`(?<!\S)(တ(?:စ်)?)\s+ဖက်\s*သတ်(?!\S)`<br>`(?<!\S)(တ(?:စ်)?)\s+ခါ\s*(တ(?:စ်)?)\s*ရံ(?!\S)` | `\1ပြိုင်နက်`<br>`\1ဖက်သတ်`<br>`\1ခါ\2ရံ` |
| `S2_TAKYUN_PENALTY` | Boundary shift on `တကျွန်းပို့ဒဏ်` (leaves `တကျွန်း အပို့ ခံ` untouched) | `(?<!\S)(တ(?:စ်)?ကျွန်း)\s+ပို့\s+ဒဏ်\s*ခံ(?!\S)` | `\1ပို့ဒဏ် ခံ` |
| `S2_IDIOM_4SYL` | Split 4-syllable idioms (`စာ ပေး စာ ယူ`, `သက် သက် သာ သာ`) | `(?<!\S)စာ\s+ပေး\s*စာ\s+ယူ(?!\S)`<br>`(?<!\S)သက်\s+သက်\s+သာ\s+သာ(?!\S)` | `စာပေးစာယူ`<br>`သက်သက်သာသာ` |
| `S2_PROTECTED_JOIN` | High-frequency over-split protected words (`သ ဖြင့်`, `နှ လုံး သား`) | `(?<!\S)သ\s+ဖြင့်(?!\S)`<br>`(?<!\S)နှ\s*လုံး\s+သား(?!\S)`<br>`(?<!\S)သု\s+သာန်(?!\S)` | `သဖြင့်`<br>`နှလုံးသား`<br>`သုသာန်` |

### Stage 3: Owner 10-Row Component Split Standards (Longest Complete Match First)

Applies the 10 Owner Component Rows strictly on complete tokens (`(?<!\S)...(?!\S)`), ordered longest-first so `ပြည်နယ်အစိုးရအဖွဲ့` matches before `ပြည်နယ်အစိုးရ` and `မြန်မာနိုင်ငံသား` or `သာသနာရေး` are never split:

| Rule ID | Complete Surface (Token-Bounded) | WS Split Output | Flat POS Split Output |
| --- | --- | --- | --- |
| `S3_ROW04B` | `(?<!\S)ပြည်နယ်အစိုးရအဖွဲ့(?!\S)` | `ပြည်နယ် အစိုးရ အဖွဲ့` | `ပြည်နယ်/n အစိုးရ/n အဖွဲ့/n` |
| `S3_ROW04A` | `(?<!\S)ပြည်နယ်အစိုးရ(?!\S)` | `ပြည်နယ် အစိုးရ` | `ပြည်နယ်/n အစိုးရ/n` |
| `S3_ROW01B` | `(?<!\S)မြန်မာနိုင်ငံတော်(?!\S)` | `မြန်မာ နိုင်ငံတော်` | `မြန်မာ/n နိုင်ငံတော်/n` |
| `S3_ROW01A` | `(?<!\S)မြန်မာနိုင်ငံ(?!\S)` | `မြန်မာ နိုင်ငံ` | `မြန်မာ/n နိုင်ငံ/n` |
| `S3_ROW02` | `(?<!\S)ပြည်ထောင်စုအစိုးရ(?!\S)` | `ပြည်ထောင်စု အစိုးရ` | `ပြည်ထောင်စု/n အစိုးရ/n` |
| `S3_ROW03B` | `(?<!\S)အစိုးရအဖွဲ့ဝင်(?!\S)` | `အစိုးရ အဖွဲ့ဝင်` | `အစိုးရ/n အဖွဲ့ဝင်/n` |
| `S3_ROW03A` | `(?<!\S)အစိုးရအဖွဲ့(?!\S)` | `အစိုးရ အဖွဲ့` | `အစိုးရ/n အဖွဲ့/n` |
| `S3_ROW05` | `(?<!\S)အာဏာပိုင်နက်(?!\S)` | `အာဏာ ပိုင်နက်` | `အာဏာ/n ပိုင်နက်/n` |
| `S3_ROW06` | `(?<!\S)ဝန်ကြီးရုံး(?!\S)` | `ဝန်ကြီး ရုံး` | `ဝန်ကြီး/n ရုံး/n` |
| `S3_ROW07` | `(?<!\S)ဘာသာသာသနာ(?!\S)` | `ဘာသာ သာသနာ` | `ဘာသာ/n သာသနာ/n` |
| `S3_ROW08` | `(?<!\S)စီးပွားရေးစနစ်(?!\S)` | `စီးပွားရေး စနစ်` | `စီးပွားရေး/n စနစ်/n` |
| `S3_ROW09` | `(?<!\S)သယံဇာတပစ္စည်း(?!\S)` | `သယံဇာတ ပစ္စည်း` | `သယံဇာတ/n ပစ္စည်း/n` |
| `S3_ROW10A` | `(?<!\S)ရေပေါ်ရေအောက်(?!\S)` | `ရေပေါ် ရေအောက်` | `ရေပေါ်/n ရေအောက်/n` |
| `S3_ROW10B` | `(?<!\S)မြေပေါ်မြေအောက်(?!\S)` | `မြေပေါ် မြေအောက်` | `မြေပေါ်/n မြေအောက်/n` |

### Stage 3B: Title/Rank Splitting vs. Personal Name Prefix Preservation (ရာထူး/ဂုဏ်ပုဒ် ခွဲထုတ်ခြင်း နှင့် အမည်ရှေ့ဆက် မခွဲဘဲ ထိန်းသိမ်းခြင်း စံ)

- **Official, Feudal, Military & Academic Titles/Ranks (ရာထူး၊ အဆင့်အတန်း၊ ဂုဏ်ပုဒ်များ - Split as Separate Token `/n`)**:
  - `စော်ဘွားကြီး`, `ဗိုလ်ချုပ်ကြီး`, `ဗိုလ်မှူးချုပ်`, `ဗိုလ်မှူးကြီး`, `ဗိုလ်မှူး`, `ဗိုလ်ချုပ်`, `ဗိုလ်ကြီး`, `သံအမတ်ကြီး`, `ဒေါက်တာ`, `ပါမောက္ခ`, `သမ္မတ`, `ဝန်ကြီးချုပ်`, `ဆရာတော်`, `ဥက္ကဋ္ဌ` စသည်တို့ကို အမည်ရှေ့မှ သီးခြားခွဲထုတ်သည်:
    - `ဗိုလ်ချုပ်အောင်ဆန်း` -> `ဗိုလ်ချုပ် အောင်ဆန်း` (`ဗိုလ်ချုပ်/n အောင်ဆန်း/n`)
    - `ဗိုလ်ကြီးဇင်ယော်` -> `ဗိုလ်ကြီး ဇင်ယော်` (`ဗိုလ်ကြီး/n ဇင်ယော်/n`)
    - `ဗိုလ်မှူးစောမုတ်သုန်` -> `ဗိုလ်မှူး စောမုတ်သုန်` (`ဗိုလ်မှူး/n စောမုတ်သုန်/n`)
    - `မိုင်းပွန် စော်ဘွားကြီး စဝ်စံထွန်း` -> `မိုင်းပွန် စော်ဘွားကြီး စဝ်စံထွန်း` (`မိုင်းပွန်/n စော်ဘွားကြီး/n စဝ်စံထွန်း/n`)
- **Personal & Ethnic Name Prefixes (အမည်ရှေ့ဆက်များ - Do NOT Split, Keep Unified as 1 Token `/n`)**:
  - လူမှုရေးနှင့် တိုင်းရင်းသား အမည်ရှေ့ဆက်များ (`ဦး`, `ဒေါ်`, `ကို`, `မ`, `စဝ်`, `စော`, `နော်`, `ခွန်`, `စိုင်း`, `နန်း`, `မန်း`, `ဆလိုင်း`, `ဒူဝါ`, `နိုင်`, `မောင်`) ကို အမည်မှ မခွဲရ:
    - ❌ `ဦး မင်းအောင်လှိုင်` -> ✅ `ဦးမင်းအောင်လှိုင်/n`
    - ❌ `ဒေါ် အောင်ဆန်းစုကြည်` -> ✅ `ဒေါ်အောင်ဆန်းစုကြည်/n`
    - ❌ `ဦး ကျော်မိုးထွန်း` -> ✅ `ဦးကျော်မိုးထွန်း/n`
    - ❌ `စဝ် စံထွန်း` -> ✅ `စဝ်စံထွန်း/n`
    - ❌ `စော မုတ်သုန်` -> ✅ `စောမုတ်သုန်/n`
    - `ကိုမင်းကိုနိုင်/n`, `မသီရိစိုး/n`, `စိုင်းဆု/n`, `ခွန်ထွန်းဦး/n`, `ဆလိုင်းတင်မောင်ဦး/n`.

### Stage 3C: Indefinite Multiplier Reunification (`-ပေါင်းများစွာ`) & Counting Compounds (`[Noun]ပေါင်း + Numeral`)
- **Indefinite Multipliers (`-ပေါင်းများစွာ`)**:
  - `([A-Za-z\u1000-\u109F]+)ပေါင်း\s+များစွာ` -> `\1ပေါင်းများစွာ`
  - `([A-Za-z\u1000-\u109F]+)ပေါင်း\s+များ\s+စွာ` -> `\1ပေါင်းများစွာ`
  - Examples: `ဒါဇင်ပေါင်းများစွာ/adj`, `သန်းပေါင်းများစွာ/adj`, `ထောင်ပေါင်းများစွာ/adj`, `ရာပေါင်းများစွာ/adj`, `နှစ်ပေါင်းများစွာ/adv`, `လပေါင်းများစွာ/adv`, `ရာစုနှစ်ပေါင်းများစွာ/adv`.
- **Counting Compounds (`[Noun]ပေါင်း + Numeral`)**:
  - `(တိုက်ပွဲ|အဖွဲ့အစည်း|ရက်|နိုင်ငံ|ပစ်မှတ်|အမှု|လူ)\s+ပေါင်း\s+(\d+|[၀-၉]+)` -> `\1ပေါင်း \2`
  - Examples: `တိုက်ပွဲပေါင်း/n ၁၀၀/num`, `အဖွဲ့အစည်းပေါင်း/n ၁၀၀/num`, `ရက်ပေါင်း/n ၁၀၀/num`, `နိုင်ငံပေါင်း/n ၃၉/num`, `ပစ်မှတ်ပေါင်း/n ၈၀/num`, `အမှုပေါင်း/n ၅၀၀/num`.

### Stage 4: Morphosyntactic Chain Rules (`-ရေး`, `၍`, `မ`, `-ချက်`, `-သူ`, `အား`, Classifiers)

| Rule ID | Linguistic Rule | Pattern & Guard | Remediation |
| --- | --- | --- | --- |
| `S4_SPLIT_YWE` | Split fused `၍` from preceding verb/adverb stem (except `ဟူ၍`, `အကယ်၍`) | `(?<!\S)(?!ဟူ၍\|အကယ်၍)([^\s/]{2,})၍(?:/([a-z]+))?(?!\S)` | `ပို၍` -> `ပို/adv ၍/part`, `ဆက်လက်၍` -> `ဆက်လက်/adv ၍/part`, else `<stem>/v ၍/conj` |
| `S4_YAY_CHAIN` | Attach `-ရေး` only to the final auxiliary in a chain | `(?<!\S)(လာ\|နိုင်\|ပေး\|ဖြစ်)စေရေး(?!\S)`<br>`(?<!\S)ပေးနိုင်ရေး(?!\S)` | `\1 စေရေး`<br>`ပေး နိုင်ရေး` |
| `S4_CHAK_AUX` | Split `-ချက်` when an auxiliary intervenes | `(?<!\S)(သတ်မှတ်\|ဖော်ပြ\|ပြဋ္ဌာန်း)\s*(ထား\|ပါ)ချက်(?!\S)` | `\1 \2 ချက်` |
| `S4_PRODUCTIVE_SU` | Split productive `V + သူ` relative-clause agents (protect lexicalized `-သူ` whitelist) | `(?<!\S)(လျှောက်ထား\|ကြီးကြပ်\|ကျူးလွန်\|ပိုင်ဆိုင်\|ရင်းနှီးမြှုပ်နှံ)သူ(?!\S)` | `\1 သူ` |
| `S4_MARKER_AA` | Split dative/accusative `အား` glued to nouns (protect `ဖိအား, ဓာတ်အား, အင်အား, စွမ်းအား, လုပ်အား`) | `(?<!\S)(သမ္မတ\|တရားခံ\|တရားလို\|တဦး\|တစ်ဦး\|၎င်း)အား(?!\S)` | `\1 အား` |
| `S4_REDUP_CLF` | Join reduplicated classifiers after `တ/တစ်` (`တစ် ဦး ဦး` -> `တစ် ဦးဦး`, guarding against `ဦးဆောင်`) | `(?<!\S)(တ(?:စ်)?)\s+(ဦး\|ခု\|ရပ်\|ယောက်\|မျိုး)\s+\2(?!ဆောင်\|\S)` | `\1 \2\2` |

### Stage 5: Boundary-Shift Trap Remediation & Contextual POS Tag Refinement

1. **Boundary-Shift Trap Replacements**:
   - `အများ ကလေး စား ထိုက်` -> `အများ က လေးစား ထိုက်`
   - `ခံ ရ သူမ ဟုတ် ဘဲ` -> `ခံ ရ သူ မ ဟုတ် ဘဲ`
   - `ဥပဒေ အရသာ` -> `ဥပဒေ အရ သာ`
   - `အစည်းအဝေးခန်း မ` -> `အစည်းအဝေး ခန်းမ`
   - `ဗုဒ္ဓ ဘာသာသာ သ နာ` -> `ဗုဒ္ဓ ဘာသာ သာသနာ`
   - `မီးငြှိမ်း သတ် ရေး` -> `မီး ငြှိမ်းသတ်ရေး`
   - `စီရင်ချက်ချ မှတ်` -> `စီရင်ချက် ချမှတ်`
   - `သတိမထား ရှိ ဘဲ` -> `သတိ မ ထားရှိ ဘဲ`
   - `ဦး ရေအနက်` -> `ဦးရေ အနက်`
   - `တာဝန် ယူဆောင် ရွက်` -> `တာဝန် ယူ ဆောင်ရွက်`
   - `ခေတ္တရပ် စောင့်` -> `ခေတ္တ ရပ် စောင့်`
   - `အန္တရာယ် ကင်းဖိအား` -> `အန္တရာယ် ကင်း ဖိအား`
   - `ကစား ပြိုင်ပွဲ ကွင်းကြီး` -> `ကစားပြိုင်ပွဲကွင်း ကြီး`
2. **Contextual POS Tag Refinement (on `word/tag` streams)**:
   - **11 Owner Fixed-Tag Archaic/Standard Surfaces**: Enforce `တမျိုးတည်း/adj`, `တဖက်သတ်/adv`, `တဆက်တည်း/adv`, `တဦးတည်းပိုင်/adj`, `တချိန်တည်း/adv`, `တပြိုင်နက်/adv`, `တခါတရံ/adv`, `အခါတမျိုးမျိုး/adv`, `တချက်လွှတ်/adj`, `တကျွန်းပို့ဒဏ်/n`, `တသီးတခြား/adv`.
   - **`ဆိုသည်မှာ` & Post-Verbal Nominalizer `သည်`**: In `ဆို + သည် (+ မှာ)`, `သည်` nominalizes the verb `ဆို/v` and is strictly enforced as `သည်/part`, while `မှာ` is enforced as the topic/subject postposition `မှာ/ppm` (`ဆို/v သည်/part မှာ/ppm`, never `သည်/ppm` or `မှာ/part`).
   - **Post-Verbal `ရာ` (`[V] + ရာ/part` vs Place/Object `/n` vs Numeral `ရာ/tn`)**: When `ရာ` follows an action/process verb (`v` or `part`) in `[V] + ရာ + တွင်/၌/မှ`, `[V] + ရာ + ရောက်/v`, `[V1] + ရာ + [V1] + ကြောင်း`, or `[V] + ရာ + [Head Noun]` (`ပြန့်/v ရာ/part နယ်မြေ/n`, `စုဝေး/v ရာ/part နေရာ/n`), enforce `ရာ/part` (never `ရာ/v` or `ရာ/n`). Preserve `ရာ/tn` after multiplier numerals (`တ/tn ရာ/tn`, `နှစ်/tn ရာ/tn`, `သုံး/tn ရာ/tn`), and keep lexicalized place/object nouns (`နေရာ/n`, `အရာ/n`, `ရိုက်ရာ/n`) as `/n`.
   - **Pre-verbal Negation `မ`**: When `မ` precedes `v` or `adj`, enforce `မ/part` (preserving `ကျား/n -/punc မ/n ဘာဝ/n`).
   - **Sentence-Final `မည်` and `သည်`**: At sentence/clause end (before `။`), enforce `/part`.
   - **Post-verbal Aspect & Modal Auxiliaries**: When `ခဲ့, ပြီး, လိုက်, နေ, နိုင်, ရ, စေ, သင့်` immediately follow a verb (`v` or `part`) inside a verb chain (and not `ပြီးနောက်/conj` or `ပြီးလျှင်/conj`), enforce `/part`.
   - **Quotative Particles & Productive Nominalizers**: Always enforce `/part` on `ဟု, ဟူ၍, ဟူသော, ဟူသည်`, and enforce `/part` on `ခြင်း, မှု, ခွင့်` immediately following `v`.
   - **Spelled Numerals & Decimal `ဒသမ`**: When `တ` or `တစ်` precedes a classifier (`ဦး, ယောက်, ခု, ရပ်, ပါး, ကြိမ်, လ, နှစ်, ရက်, မျိုး, စုံ, ရာ`), enforce `/tn`. Enforce `/adj` on ordinals (`ပထမ, ပဌမ, ဒုတိယ, တတိယ ...`), except `ဒသမ/n` when between two numerals (`သုည/tn ဒသမ/n တစ်/tn`).
   - **Parenthetical Subclause Bullets vs Foreign/Place Names**: Enforce `/sb` on single Myanmar subclause letters/symbols inside `( ... )` (`(/punc က/sb )/punc`), while preserving `/fw` on parenthetical Latin legal terms (`Mandamus/fw`, `Prohibition/fw`, `Certiorari/fw`) and `/n` on parenthetical alternate place names (`ပန်ခမ်း/n`). Never allow `/sb` outside parentheses or `/fw` on Burmese script tokens.

### Stage 6: Verification Gate, JSON/TSV Field Alignment & Record-Only Typo Lead Logging

- Asserts `strip_ws(before) == strip_ws(after)` on every line.
- For JSON chunk records, asserts `len(ws_text.split()) == len(pos_line.split()) == len(tokens) == token_count` and exact 1-based `token_id` sequence (`1 .. token_count`).
- Scans for the 8 Owner Record-Only Typo Leads (`စည်းမျည်း`, `စေကာမှု`, `ပြည်ထယ်စု`, `ပြည်ထာင်စု`, `အံဆဲဆဲ`, `ပြီးလျင်`, `ပြည်နယ် ကော်စီ`, `ကျင့်ဝပ် သိက္ခာ`, `ပြဿ သို့ ကို`) and writes hits to `record_only_leads.jsonl` with `status: "RECORD_ONLY_NOT_APPLIED"`.
