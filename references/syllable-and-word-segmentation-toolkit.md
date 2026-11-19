# မြန်မာစကားလုံးနှင့် ဝဏ္ဏပိုင်းခြားရေး Toolchain (High-Speed Myanmar Syllable & Word Segmentation Toolkit)

ဤလက်စွဲစာတမ်းသည် TTKeyboard auto-suggestion engine မှ reverse-engineer လုပ်ထားသော Trie Lexicon (`my_MM_lexicon.txt` ၁၃,၄၂၁ နှင့် `my_MM_comprehensive_lexicon.txt` ၈,၈၂၉ cleaned entries၊ `owner_keep_whole.txt` ၃၇၈ entries) နှင့် ThanLwinSoft / myOpenware Pair-Rule အင်ဂျင်ကို ပေါင်းစပ်တည်ဆောက်ထားသည့် စွမ်းဆောင်ရည်မြင့် မြန်မာစကားလုံးနှင့် ဝဏ္ဏပိုင်းခြားရေး ကိရိယာအစုံအလင် (`scripts/syllable_breaker.py`, `scripts/word_segmenter.py`, `scripts/compound_builder.py`, `scripts/nlp_cli.py`) ၏ အသုံးပြုနည်းနှင့် နည်းပညာဆိုင်ရာ အသေးစိတ် အချက်အလက်များ ဖြစ်သည်။

---

## 📌 အဓိက အစိတ်အပိုင်းများနှင့် စွမ်းဆောင်ရည်

```mermaid
flowchart TD
    Raw["မြန်မာစာသား (Raw Text)"] --> SB["syllable_breaker.py<br/>(ThanLwinSoft/myOpenware Pair-Rule)"]
    SB --> Syllables["ဝဏ္ဏအစု (Syllables)<br/>(Kinzi, ဗျည်းဆင့်, သရ/အသတ် ထိန်းသိမ်းမှု)"]
    
    Lexicon["resources/lexicon/<br/>my_MM_lexicon.txt (13,421 entries)<br/>my_MM_comprehensive_lexicon.txt (8,829 entries)<br/>owner_keep_whole.txt (378 entries)"] --> WS["word_segmenter.py<br/>(Syllable-Constrained FMM + BMM)"]
    Syllables --> WS
    
    WS --> Tokens["စကားလုံး Token များ & Spans<br/>[token, start, end, in_dict, freq]"]
    Tokens --> CLI["nlp_cli.py<br/>(-s, -w, -t, -l, -f, -c, --profile, --normalize-confusables, --benchmark)"]
```

| ကိရိယာ | ဖိုင်လမ်းကြောင်း | လုပ်ဆောင်ချက် | စွမ်းဆောင်ရည် |
| :--- | :--- | :--- | :--- |
| **Syllable Breaker** | `scripts/syllable_breaker.py` | Pair-rule အခြေခံ ဝဏ္ဏခွဲခြမ်းစနစ် | Kinzi, ဗျည်းဆင့်, သရ/အသတ် 100% တည်တံ့မှု (spans ရယူနိုင်) |
| **Word Segmenter** | `scripts/word_segmenter.py` | Syllable-constrained FMM + BMM, then a closed owner post-pass (profile-aware, span-preserving) | Dictionary candidate. Not Legal70k gold outside the closed lists |
| **Compound Builder** | `scripts/compound_builder.py` | TTKeyboard Trie Node များမှ ပေါင်းစပ်ပုဒ်များ ထုတ်လုပ်ခြင်း | ၁၃,၄၂၁ မှ ၈,၈၂၉ cleaned ပေါင်းစပ်ပုဒ်များ |
| **NLP CLI Tool** | `scripts/nlp_cli.py` | Syllable, Word, Span Tokenize, Lookup, Decide CLI (`--profile`, `--normalize-confusables`) | Re-measure with `--benchmark` (~500k chars/sec) |
| **Test Suite** | `scripts/test_nlp_tools.py` | Unit tests for syllables, compounds, owner post-pass, spans, profiles | Run the file; comprehensive test coverage |
| **Lexicon Database** | `resources/lexicon/` | Base (13,421), Comprehensive (8,829) ဝေါဟာရဘဏ် နှင့် `owner_keep_whole.txt` (378 entries) | Trie ဝေါဟာရ။ Owner protected list နှင့် အမြဲမတူ |

---

## ၁။ Syllable Breaker (`scripts/syllable_breaker.py`)

ThanLwinSoft နှင့် myOpenware တို့၏ Pair-Rule Engine (`myparser.py`) ကို အသုံးပြုထားသည်။ ၎င်းသည် ဗျည်းနှင့် သရ/အသတ် စာလုံးတွဲများကို ဇယား matrix စည်းမျဉ်းအရ စစ်ဆေးဖြတ်တောက်သဖြင့် ပုံမှန် Regex များတွင် ဖြစ်ပေါ်လေ့ရှိသော အောက်ပါ အမှားများကို လုံးဝ ကင်းဝေးစေသည်-

1. **ကင်းစီးမပြိုကွဲခြင်း (Kinzi Preservation)**: `မင်္ဂလာပါ` -> `['မင်္ဂ', 'လာ', 'ပါ']` (`င်္ဂ` အား သီးခြားမပြတ်စေရ)။
2. **ဗျည်းဆင့်မပြိုကွဲခြင်း (Consonant Stack Preservation)**: `ဗုဒ္ဓဘာသာ` -> `['ဗုဒ္ဓ', 'ဘာ', 'သာ']` (`ဗုဒ္` နှင့် `ဓ` ကို မခွဲရ)။
3. **ဗျည်းတွဲများနှင့် အသတ်များ တည်တံ့ခြင်း**: ယပင့်၊ ရရစ်၊ ဝဆွဲ၊ ဟထိုး တွဲစပ်မှုများနှင့် အသတ် ၈ မျိုးကို မူရင်းအသံထွက် ယူနစ်အတိုင်း ထိန်းသိမ်းသည်။

### Python အသုံးပြုနည်း
```python
from scripts.syllable_breaker import SyllableBreaker

breaker = SyllableBreaker()

# ၁။ ဝဏ္ဏ ခွဲထုတ်ခြင်း
syllables = breaker.segment("ပြည်ထောင်စုသမ္မတမြန်မာနိုင်ငံတော်")
print(syllables)
# Output: ['ပြည်', 'ထောင်', 'စု', 'သမ္မ', 'တ', 'မြန်', 'မာ', 'နိုင်', 'ငံ', 'တော်']

# ၂။ ဝဏ္ဏ Character Spans ထုတ်ယူခြင်း
spans = breaker.get_spans("ပြည်ထောင်စုသမ္မတမြန်မာနိုင်ငံတော်")
print(spans)
# Output: [(0, 4, 'ပြည်'), (4, 9, 'ထောင်'), (9, 11, 'စု'), (11, 15, 'သမ္မ'), (15, 16, 'တ'), (16, 20, 'မြန်'), (20, 22, 'မာ'), (22, 27, 'နိုင်'), (27, 29, 'ငံ'), (29, 33, 'တော်')]
```

---

## ၂။ Word Segmenter (`scripts/word_segmenter.py`)

Trie Data Structure နှင့် Syllable Boundary Constraint ကို ပေါင်းစပ်ထားသော ရှေ့ပြေးနှင့် နောက်ပြန် အရှည်ဆုံးကိုက်ညီမှု စနစ် (Bi-directional Maximum Matching - FMM + BMM) ဖြစ်သည်။

### အဓိက အားသာချက်များ:
- **Syllable-Constrained**: စကားလုံးဖြတ်တောက်မှုကို ဝဏ္ဏနိမိတ် (Syllable Boundary) များပေါ်တွင်သာ ကန့်သတ်ထားသဖြင့် `က ဏန်း` သို့မဟုတ် `လမ်းမ ပျက်စီး` ကဲ့သို့သော အက္ခရာအလယ်တွင် စကားလုံးပြတ်ထွက်သည့် Boundary-Shift Traps များကို အလိုအလျောက် တားဆီးပေးသည်။
- **Character Spans ပါဝင်ခြင်း**: စကားလုံးတစ်ခုချင်းစီ၏ စာကြောင်းအတွင်း တည်နေရာ Offset `(start, end)` များကို တိကျစွာ ထုတ်ပေးနိုင်သဖြင့် Named Entity Recognition (NER), Word Alignment နှင့် Dependency Parsing (CoNLL-U) အတွက် အထူးသင့်လျော်သည်။
- **Unigram Frequency Ranking**: စကားလုံးနှစ်ခွ ဖြစ်နိုင်သော အခြေအနေများတွင် TTKeyboard ၏ အကြိမ်ရေအများဆုံး စကားလုံးကို ဦးစားပေး ရွေးချယ်သည်။

### Python အသုံးပြုနည်း
```python
from scripts.word_segmenter import WordSegmenter

# default: profile="legal70k", normalize_confusables=False (conserve exact raw codepoints and spans)
segmenter = WordSegmenter()

# ၁။ စကားလုံး ပုဒ်ဖြတ်ခြင်း (Live Verbatim Output)
words = segmenter.segment("ကာကွယ်ရေးဦးစီးချုပ် ရုံးသို့ သွားရောက်ခဲ့သည်။")
print(words)
# Output: ['ကာကွယ်ရေးဦးစီးချုပ်', 'ရုံး', 'သို့', 'သွား', 'ရောက်', 'ခဲ့', 'သည်', '။']

# ၂။ Span နှင့် in_dict / frequency ပါဝင်သော Tokenize ပြုလုပ်ခြင်း
tokens = segmenter.tokenize("စာအုပ်ဖတ်ပါ")
for t in tokens:
    print(t)
# Output:
# {'token': 'စာအုပ်', 'start': 0, 'end': 6, 'in_dict': True, 'freq': 0}
# {'token': 'ဖတ်', 'start': 6, 'end': 9, 'in_dict': True, 'freq': 0}
# {'token': 'ပါ', 'start': 9, 'end': 11, 'in_dict': True, 'freq': 0}
```

---

## ၃။ Command-Line Interface (`scripts/nlp_cli.py`)

Terminal မှ တိုက်ရိုက်ခေါ်ယူ အသုံးပြုနိုင်သော စွမ်းဆောင်ရည်မြင့် CLI ကိရိယာ ဖြစ်သည်။

### Command Syntax & Examples

```bash
# ၁။ ဝဏ္ဏ ပိုင်းခြားခြင်း (Syllable Breaking)
python3 scripts/nlp_cli.py -s "မြန်မာနိုင်ငံတော်"
# Output: မြန် | မာ | နိုင် | ငံ | တော်

# ၂။ စကားလုံး ပုဒ်ဖြတ်ခြင်း (Word Segmentation)
python3 scripts/nlp_cli.py -w "ပြည်ထောင်စုသမ္မတမြန်မာနိုင်ငံတော်"
# Output: ပြည် | ထောင် | စု | သမ္မတ | မြန်မာ | နိုင်ငံတော်

# ၃။ Token Spans များကို JSON format ဖြင့် ထုတ်ယူခြင်း
python3 scripts/nlp_cli.py -t "စာအုပ်ဖတ်ပါ" --json
# Output:
# [
#   {
#     "token": "စာအုပ်",
#     "start": 0,
#     "end": 6,
#     "in_dict": true,
#     "freq": 0
#   },
#   {
#     "token": "ဖတ်",
#     "start": 6,
#     "end": 9,
#     "in_dict": true,
#     "freq": 0
#   },
#   {
#     "token": "ပါ",
#     "start": 9,
#     "end": 11,
#     "in_dict": true,
#     "freq": 0
#   }
# ]

# ၄။ TTKeyboard ဝေါဟာရဘဏ်အတွင်း စကားလုံး စစ်ဆေးရှာဖွေခြင်း (Lookup)
python3 scripts/nlp_cli.py -l "အစိုးရ"
# Output:
# {
#   "query": "အစိုးရ",
#   "in_dict": true,
#   "frequency": 250,
#   "syllables": [
#     "အစိုး",
#     "ရ"
#   ]
# }

# ၅။ myPOS Tag ဆုံးဖြတ်ခြင်း (Decide Mode)
python3 scripts/nlp_cli.py -c "တရားလိုသည်လျှောက်ထားသည်။"
# Output:
# Tokens: ['တရားလို', 'သည်', 'လျှောက်', 'ထား', 'သည်', '။']
# Closed decisions: သည်/ppm (THI_SUBJECT), သည်/part (THI_FINAL), ။/punc
# Review items: ထား (status: review)

# ၆။ Corpus Profile ရွေးချယ်၍ ပုဒ်ဖြတ်ခြင်း (--profile {general, legal70k, news_unified, legacy_mypos_alt})
python3 scripts/nlp_cli.py -w "လေ့လာသုံးသပ်သူ" --profile news_unified
# Output: လေ့လာသုံးသပ်သူ
python3 scripts/nlp_cli.py -w "လေ့လာသုံးသပ်သူ" --profile general
# Output: လေ့ | လာ | သုံး | သပ် | သူ

# ၇။ Lookalike Confusables ကို စစ်ဆေးပြင်ဆင်ခြင်း (--normalize-confusables)
# default: normalize_confusables=False (မူရင်း codepoint နှင့် exact span ကို 100% ထိန်းသိမ်းသည်)
# opt-in: --normalize-confusables ဖြင့် စာလုံးတူအမှားများကို ပြင်ဆင်ပြီး span map ပြန်ချိတ်ပေးသည်

# ၈။ ဖိုင်အလိုက် တစ်လိုင်းချင်း Stream လုပ်၍ ပုဒ်ဖြတ်ခြင်း
python3 scripts/nlp_cli.py -f input_raw.txt -d " " > output_segmented.txt

# ၉။ စွမ်းဆောင်ရည် စမ်းသပ်ခြင်း (Benchmark)
python3 scripts/nlp_cli.py --benchmark
# Output:
# === Performance Benchmark ===
# Total Sentences Processed: 2,400
# Total Characters Processed: 118,500
# Total Time Taken          : ~0.24 seconds
# Throughput                : ~485,000–500,000 chars/sec
# Sentences/sec             : ~9,800–10,200 sentences/sec
```

---

## ၄။ Unit & Regression Test Suite (`scripts/test_nlp_tools.py`)

Toolkit ၏ တိကျခိုင်မာမှုကို အောက်ပါ command ဖြင့် အချိန်မရွေး စစ်ဆေးနိုင်သည်-

```bash
python3 scripts/test_nlp_tools.py -v
```

အဓိက စစ်ဆေးပေးသော စမ်းသပ်မှုကဏ္ဍများ:
- ဝဏ္ဏခွဲခြမ်းမှု (Syllable Breaker): အခြေခံဝဏ္ဏ၊ ကင်းစီး (`င်္ဂ`)၊ ပါဠိဆင့်/ဗျည်းဆင့် (`ဗုဒ္ဓ`) နှင့် သရ/အသတ် မပြိုကွဲစေရေး စစ်ဆေးမှု။
- စကားလုံးဖြတ်တောက်မှု (Word Segmenter): အဆင့်မြင့် ပေါင်းစပ်ပုဒ်ရှည်များ၊ ဂုဏ်ထူးဆောင်/ရာထူးတံဆိပ်များ၊ တိုက်ဆိုင်မှုအရှည်ဆုံး FMM+BMM စစ်ဆေးမှု။
- Owner Post-Pass & Keep-Whole: Institutional splits (`မြန်မာ နိုင်ငံတော်`)၊ keep-whole ထိန်းသိမ်းမှု၊ trap concatenations ရှောင်ရှားမှု စစ်ဆေးမှု။
- Offset Spans တည်တံ့မှု: Tokenization တွင် မူရင်းစာသား character offset `(start, end)` များ တိကျစွာ ကိုက်ညီမှု (`join(spans) == raw`) စစ်ဆေးမှု။
- Confusables & Profiles: Confusable lookalike များကို မူရင်း codepoint မပြောင်းလဲစေဘဲ span ထိန်းသိမ်းနိုင်မှုနှင့် corpus profiles (`general`, `legal70k`, `news_unified`, `legacy_mypos_alt`) အလိုက် စည်းမျဉ်းများ တိကျမှု။
- ဝေါဟာရဘဏ် Lookup & Triage: Dictionary lookup၊ Unigram Frequency နှင့် `decide.py` ၏ `closed` / `review` triage မှန်ကန်မှု။
*(မှတ်ချက် — scripts/ အတွင်းရှိ standalone `--self-test` tools ၉ ခုဖြစ်သော `confusable.py`, `corpus_chunk_and_remediate.py`, `decide.py`, `legal70k_audit.py`, `nominal.py`, `project_mypos_hd.py`, `register.py`, `validate_nlp_corpus.py`, `verb_pair.py` တို့ဖြင့်လည်း အစိတ်အပိုင်းအလိုက် သီးခြားစစ်ဆေးနိုင်သည်)*

---

## ၅။ Downstream NLP နှင့် Legal70k Corpus Pipeline သို့ ပေါင်းစပ်မှု

1. **Pre-segmentation Phase (Stage 0)**:
   * ကြီးမားသော စာသားများ (သောင်း/သိန်းချီ) ကို စတင် စိစစ်ရာတွင် `nlp_cli.py -f` ဖြင့် စွမ်းဆောင်ရည်မြင့်စွာ (~500,000 chars/sec နှုန်းဖြင့်) ကနဦး Candidate Segmentation ရယူနိုင်သည်။
2. **Syllable-Boundary Gatekeeper**:
   * Staged Regex Cascade ပြုလုပ်ရာတွင် Regex နယ်နိမိတ်များကို Syllable Breaker ဖြင့် စစ်ဆေးထိန်းချုပ်ခြင်းဖြင့် စာလုံးပေါင်းပြိုကွဲသည့် အမှားများ မဖြစ်ပွားစေရန် အာမခံသည်။
3. **Exact Token Span Alignment**:
   * Token Spans `(start, end)` ကို အသုံးပြု၍ Named Entity Recognition (NER), CoNLL-U Word Order, UD Treebank များနှင့် CQL Vertical Indexing ဖိုင်များ တည်ဆောက်ရာတွင် နေရာလွဲမှားမှု မရှိစေရန် စနစ်တကျ ချိတ်ဆက်အသုံးချနိုင်သည်။

---

## ၆။ Numeric, Date Entity & Special Token Segmentation Rules

### ၆.၁ ဂဏန်းသင်္ကေတ (Numeric Digits `num`) နှင့် ဂဏန်းစကားလုံး (Textual Numbers `tn`)

| Pattern | Tokenization | POS | Example |
|---|---|---|---|
| Myanmar digits alone | 1 token | `num` | `၁/num`, `၂၅/num`, `၁,၀၀၀/num`, `၁၉၆၆/num` |
| Spelled-out number | 1 token | `tn` | `တစ်/tn`, `နှစ်ဆယ်/tn`, `တစ်ထောင်/tn` |
| `တ`/`တစ်` + classifier | 2 tokens | `tn + part` | `တစ်/tn ဦး/part`, `တ/tn ယောက်/part` |
| `ရာ` after multiplier numeral | 2 tokens | `tn + tn` | `တ/tn ရာ/tn`, `နှစ်/tn ရာ/tn` |
| Decimal: `ဒသမ` between numerals | 3 tokens | `tn + n + tn` | `သုည/tn ဒသမ/n တစ်/tn` |
| Ordinal (`ပထမ/ဒုတိယ/တတိယ...`) | 1 token | `adj` | `ပထမ/adj`, `ဒုတိယ/adj`, `ဒသမ/adj` |

**Key disambiguation traps:**
- `နှစ်` = "two" → `tn`; `နှစ်` = "year" → `n` (ဥပမာ `ခုနှစ်/n`, `သုံး/tn နှစ်/n ကြာ/v`)
- `သုံး` = "three" → `tn`; `သုံး` = "to use" → `v`
- `ဦး` = person classifier after numerals (`တစ်/tn ဦး/part`, `၃/num ဦး/part`) → **`part`**; never `tn`။ Name prefix အဖြစ်မူ အမည်နှင့် မခွဲဘဲ ပေါင်းစည်းထားသော သမ္မာနာမ် (`ဦးမင်းအောင်လှိုင်/n`) ဖြစ်သည်။ ရာထူး/ဂုဏ်ပုဒ် (`ဗိုလ်ချုပ်ကြီး/n`, `သံအမတ်ကြီး/n`, `စော်ဘွားကြီး/n`) ကိုသာ သီးခြားခွဲထုတ်သည်။

### ၆.၂ ရက်/လ/နှစ် Date Expressions

```
ပုံစံ: [DAY/num] ရက်/n [MONTH/n] လ/n [YEAR/num] ခုနှစ်/n
ဥပမာ: ၁/num ရက်/n ဇန်နဝါရီ/n လ/n ၂၀၂၆/num ခုနှစ်/n
```

| Component | POS | Note |
|---|---|---|
| Day digit (`၁`, `၂၅`) | `num` | Myanmar digit |
| `ရက်` | `n` | noun "day" |
| Month name (`ဇန်နဝါရီ`, `ဖေဖော်ဝါရီ`) | `n` | loanword → `n` not `fw` |
| `လ` | `n` | noun "month" |
| Year digit (`၂၀၂၆`) | `num` | Myanmar digit |
| `ခုနှစ်` | `n` | lexicalized "year (CE)" |
| Spelled day (`ပဉ္စမ/adj ရက်/n`) | `adj + n` | ordinal + "day" |

### ၆.၃ Legal Section References (`ပုဒ်မ`/`ပုဒ်မခွဲ`)

```
ပုဒ်မ/n ၁၃/num (/punc က/sb )/punc — 1-token noun + digit + 3-token parenthetical sub-clause marker
ပုဒ်မ/n ၇/num (/punc ဂ/sb )/punc — keep (/punc က/sb )/punc as 3 separate tokens
```

- `ပုဒ်မ` = 1-token noun `n`; never split
- Parenthetical `( က )` = `(/punc က/sb )/punc` (3 tokens); `က` = `sb` only within parentheses
- ASCII digits in modern references tag as num: `Article/fw 13/num` (legacy corpus ၌သာ `fw` -> myPOS-HD `num:latn` -> `NUM`; `validate_nlp_corpus.py` flags `[0-9]+/fw` as `ascii_digit_tagged_fw`)

### ၆.၄ Percentage, Currency, Units

| Pattern | Tokenization | POS |
|---|---|---|
| `ရာခိုင်နှုန်း` / `%` | `ရာခိုင်နှုန်း/n` OR `%/sb` (Latin) | `n` / `sb` |
| `ကျပ်` (Kyat) | `num ကျပ်/n` | digit + `n` |
| `ဒေါ်လာ` | 1 token `n` | never split |
| `ကီလိုမီတာ` / `မီတာ` / `ဂရမ်` | 1 token `n` | loanword noun |
| `%/sb`, `$/sb`, `+/sb` | 1 token each | `sb` |

---
