# POS Tagset & Universal Dependencies Mapping (`MLC 9-Class` <-> `myPOS 15-Tag` <-> `UD v2`)

This reference defines the exact cross-framework mapping and contextual disambiguation rules between:

1. **MLC 9 Word Classes (ဝါစင်္ဂ ၉ မျိုး)**: The Myanmar Language Commission reference grammar (`chapters/ch10-*.md` to `ch17-*.md`).
2. **Corpus `myPOS` 15-Tag Vocabulary**: The canonical lowercase 15-tag output set used in `myPOS-ver.3.0`, `Legal70k`, and `corpus_manager` (`abb`, `adj`, `adv`, `conj`, `fw`, `int`, `n`, `num`, `part`, `ppm`, `pron`, `punc`, `sb`, `tn`, `v`).
3. **Universal Dependencies (`UD v2`)**: The `UPOS` and `DEPREL` layers used in `myUDTree` and `CoNLL-U` exports.

**Important Output Rule**: Never mix tagsets in a single output stream. When producing `myPOS` / `Legal70k` annotations, emit **only** the 15 lowercase tags (`abb, adj, adv, conj, fw, int, n, num, part, ppm, pron, punc, sb, tn, v`). Do not emit UD tags like `DET`, `PROPN`, `AUX`, `ADP`, or `SCONJ` into a `myPOS` tag column.

## 1. Complete 3-Way Tagset Alignment Matrix

| `myPOS` Tag (15-Tag Set) | MLC 9-Class Equivalent (ဝါစင်္ဂ ၉ မျိုး) | `UD v2` UPOS Mapping (`mya-pos-v1`) | Primary Syntactic / Dependency Roles (`DEPREL`) | Examples (`word/tag`) |
| --- | --- | --- | --- | --- |
| **`n`** | နာမ် (သာမညနာမ်၊ သမ္မာနာမ်၊ စုပေါင်းနာမ်၊ ဒြပ်ရှိ/ဒြပ်မဲ့နာမ်) (Ch 10) | `NOUN` (or `PROPN` for proper names in UD) | `nsubj`, `obj`, `obl`, `nmod`, `compound`, `appos`, `root` (nominal predicate) | `ကျောင်း/n`, `ရန်ကုန်/n`, `လွတ်လပ်ရေး/n`, `တကျွန်းပို့ဒဏ်/n` |
| **`pron`** | နာမ်စား (ပုဂ္ဂလ၊ အညွှန်း၊ အမေး၊ သင်္ချာနာမ်စား) (Ch 11) | `PRON` | `nsubj`, `obj`, `obl`, `nmod:poss` | `ကျွန်တော်/pron`, `သူ/pron`, `၎င်း/pron`, `အဲဒါ/pron`, `တစ်စုံတစ်ရာ/pron` (nominal use), `ဆက်နွှယ်/v သူ/pron` (relativizer pronoun; myPOS-HD projects to `pron` -> `PRON`; `pron:rel` is not used) |
| **`v`** | ကြိယာ (ကံလို၊ ကံမလို၊ ဖြစ်ခြင်းပြ၊ ရှိခြင်းပြ) (Ch 13) | `VERB` (or `ADJ` for stative roots in UD; see Section 2.1) | `root`, `acl`, `advcl`, `ccomp`, `xcomp`, `compound:svc` | `ဆောင်ရွက်/v`, `စစ်ဆေး/v`, `ဖြစ်/v`, `ရှိ/v`, `လိုက်နာ/v` |
| **`adj`** | နာမဝိသေသန (ဂုဏ်ရည်ပြ၊ အညွှန်း၊ အရေအတွက်ပြ) (Ch 12) | `ADJ` (or `DET` for demonstratives in pure UD; never use `DET` in myPOS) | `amod`, `acl` | `ရဲရင့်/adj`, `အဆိုပါ/adj`, `အချင်းဖြစ်/adj`, `တမျိုးတည်း/adj`, `တဦးတည်းပိုင်/adj`, `တချက်လွှတ်/adj` |
| **`adv`** | ကြိယာဝိသေသန (အမူအရာ၊ အချိန်၊ ပမာဏပြ) (Ch 14) | `ADV` | `advmod` | `လွတ်လပ်စွာ/adv`, `ချက်ချင်း/adv`, `တပြိုင်နက်/adv`, `တခါတရံ/adv`, `တဖက်သတ်/adv`, `တဆက်တည်း/adv` |
| **`ppm`** | ဝိဘတ် (နာမ်ဝိဘတ် ၇ မျိုး နှင့် ကြိယာဝိဘတ်) (Ch 15) | `ADP` | `case` (when attached to nominal head), `mark` | `သည်/ppm`, `က/ppm`, `ကို/ppm`, `အား/ppm`, `တွင်/ppm`, `၌/ppm`, `မှ/ppm`, `သို့/ppm`, `ဖြင့်/ppm`, `၏/ppm` |
| **`part`** | ပစ္စည်း (နာမ်ပစ္စည်း၊ ကြိယာပစ္စည်း၊ မျိုးပြပစ္စည်း၊ အငြင်းပြ `မ`) (Ch 16) | `PART` (or `AUX` for modal/aspect auxiliaries in UD) | `aux`, `mark`, `advmod` (negation `မ`), `clf`, `case` | `များ/part`, `တို့/part`, `မ/part`, `ခဲ့/part`, `နိုင်/part`, `စေ/part`, `သော/part`, `သည့်/part`, `မှု/part`, `ခြင်း/part`, `ဦး/part` |
| **`conj`** | သမ္ဗန္ဓ (ပုဒ်ချင်းဆက်၊ ဝါကျဆက်) (Ch 16) | `CCONJ` (coordinating) / `SCONJ` (subordinating in UD) | `cc`, `mark` | `နှင့်/conj`, `သို့မဟုတ်/conj`, `သော်လည်း/conj`, `သောကြောင့်/conj`, `သဖြင့်/conj`, `၍/conj`, `ဖြစ်စေ/conj` |
| **`num`** | ကိန်းဂဏန်းအက္ခရာ (သင်္ချာနာမ်/နာမဝိသေသန - ဂဏန်းသင်္ကေတ) (Ch 11, 12) | `NUM` | `nummod` | `၁/num`, `၂/num`, `၁၀၀/num`, `၁,၀၀၀/num`, `၁၉၆၆/num`, `100/num` (modern ASCII digits; see §2.2) |
| **`tn`** | စာလုံးဖြင့်ရေးသော ကိန်းဂဏန်း (Textual Number) (Ch 11, 12) | `NUM` | `nummod` | `တစ်/tn`, `နှစ်/tn`, `သုံး/tn`, `ငါးဆယ်/tn`, `တစ်ထောင်/tn`, `နှစ်သိန်း/tn` |
| **`int`** | အာမေဍိတ် (Ch 17) | `INTJ` | `discourse` | `အမလေး/int`, `ဪ/int`, `ဟယ်/int` |
| **`punc`** | ပုဒ်ဖြတ်ပုဒ်ရပ်သင်္ကေတ (Ch 20) | `PUNCT` | `punct` | `၊/punc`, `။/punc`, `(/punc`, `)/punc`, `“/punc`, `”/punc` *(never tag `၏`/`၍` as `punc`)* |
| **`abb`** | အတိုကောက် စကားလုံး (Abbreviation) | `NOUN` / `PROPN` (`Abbr=Yes`) | `nsubj`, `obl`, `compound`, `appos` | `အထက/abb`, `လ.ဝ/abb`, `ကုလ/abb`, `ပုဒ်မခွဲ/n` (full words are `n`, only true abbreviations are `abb`) |
| **`fw`** | နိုင်ငံခြားစကားလုံး (Foreign Word / Script) | `X` (`Foreign=Yes`) | `flat:foreign`, `appos`, `compound` | `Myanmar/fw`, `BBC/fw`, `Google/fw` *(legacy `1/fw` maps to `NUM` / `num:latn`; Myanmar-script loanwords like `ဒိုင်ယာရီ`, `စင်တီဂရိတ်` stay `n`)* |
| **`sb`** | သင်္ကေတ (Symbol) | `SYM` | `dep`, `cc`, `punct` | `%/sb`, `$/sb`, `+/sb`, `=/sb`, `#/sb`, `&/sb`, `@/sb`, `(/punc က/sb )/punc` |

> [!IMPORTANT]
> **Canonical Tagset Invariant (`ALLOWED_15_TAGS` in `scripts/common_standards.py`)**:
> Canonical corpus output streams (`ws.txt`, `pos.txt`, TSV `pos`) must strictly adhere to the exact 15 lowercase tags:
> `abb, adj, adv, conj, fw, int, n, num, part, ppm, pron, punc, sb, tn, v`.
> External or legacy tags found in older academic literature or uncurated sets — specifically:
> - **`prpn`** (Proper Noun): Strictly prohibited in Base-15; must be tagged as **`n`** (projects to `n:prop` -> `PROPN` in `myPOS-HD v4.1`).
> - **`for`** (Foreign Word): Strictly prohibited in Base-15; must be tagged as **`fw`** (projects to `fw` -> `X[Foreign=Yes]`).
> - **`tnum`** (Text Number): Strictly prohibited in Base-15; must be tagged as **`tn`** (projects to `tn` -> `NUM`).
> Any occurrence of `prpn`, `for`, or `tnum` will cause `scripts/validate_nlp_corpus.py` to fail with `invalid_pos_tag`.

## 2. Framework Alignment & Structural Harmonization Rules

### 2.1 Stative / Descriptive Roots (`myPOS: v` <-> `UD: ADJ`)

In Burmese morphosyntax, descriptive/quality roots (`လွယ်ကူ`, `ခက်ခဲ`, `လှပ`, `ရဲရင့်`, `ကြီးမား`, `ကောင်းမွန်`) can take verbal endings directly (`လွယ်ကူ သည်`) or adjectival relativizers (`လွယ်ကူ သော`).

- **In `myPOS` (`mya-pos-v1` Doc_016)**: Predicative/verbal occurrences and morphosyntactic stative verbs are tagged `v` (e.g., `လွယ်ကူ/v သည်/part` in `unified_modern`, or `သည်/ppm` in `legacy_mypos_alt`), whereas pre-nominal modifier roots or dedicated adjectival forms are tagged `adj`.
- **In `myUDTree` (`UD v2`)**: Quality words are mapped semantically to `ADJ`.
- **Cross-Project Rule**: Do not blindly re-tag an entire corpus from `v` to `adj` or vice versa; use the `myPOS-HD` tag `v:stat` (`myPOS:v[stative] <-> UD:ADJ`) when projecting to UD v2.

### 2.2 Numeral Tag Split (`num` vs. `tn`)

- **`num`**: Digits (`၀-၉`, plus modern ASCII numerals `[0-9]+`, e.g., `၁/num`, `၂၅/num`, `၁,၀၀၀/num`, `2026/num`). `scripts/decide.py` (`CHAR_ASCIIDIGIT`) natively classifies `[0-9]+(?:[.,][0-9]+)*` as `num`, `scripts/validate_nlp_corpus.py` flags `[0-9]+/fw` as `ascii_digit_tagged_fw`, and `scripts/project_mypos_hd.py` bridges legacy `[0-9]+/fw` records into `num:latn` (`UD: NUM`, collapsing losslessly to base-15 `num`).
- **`tn`**: Numerals spelled out in Myanmar letters (`တစ်/tn`, `နှစ်/tn`, `သုံး/tn`, `ဆယ်/tn`, `တစ်ရာ/tn`, `တစ်ထောင်/tn`, `တစ်သိန်း/tn`).
- **Disambiguation Trap**:
  - `နှစ်`: Tagged `tn` when meaning "two" (`နှစ်/tn ဦး/part`, `နှစ်/tn ကြိမ်/part`), but tagged `n` when meaning "year" (`၁၉၆၆/num ခုနှစ်/n`, `သုံး/tn နှစ်/n ကြာ/v`).
  - `သုံး`: Tagged `tn` when meaning "three" (`သုံး/tn ခု/part`), but tagged `v` when meaning "to use/spend" (`သုံး/v စွဲ/v`, `ငွေ/n သုံး/v သည်/part`).
  - `ဦး`:
    - သင်္ချာ/ဂဏန်းနောက်မှ လူမျိုးပြပစ္စည်း (Person classifier after numerals, e.g., `တစ်/tn ဦး/part`, `၃/num ဦး/part`, `၄၄၀/num ဦး/part`) ဖြစ်ပါက **အမြဲ `part` (`part:clf`)** အဖြစ် tag လုပ်သည်။ ဘယ်သောအခါမျှ `tn` သို့မဟုတ် `n` ဟု မ tag ရ။
    - လူအမည်ရှေ့ဆက် ၁၉ မျိုး (`ဦး`, `ဒေါ်`, `ကို`, `မ`, `မောင်`, `ရှင်`, `င`, `စဝ်`, `စော`, `နော်`, `စလိုင်း`, `ဆလိုင်း`, `မိုင်း`, `ဒူဝါ`, `နိုင်`, `မန်း`, `ခွန်`, `စိုင်း`, `နန်း` — `scripts/common_standards.py`) ဖြစ်ပါက အမည်မှ **ဘယ်သောအခါမျှ မခွဲထုတ်ဘဲ** တစ်ဆက်တည်း ပေါင်းစည်း၍ သမ္မာနာမ် (`/n` -> `n:prop`) အဖြစ် သတ်မှတ်သည် (`ဦးမင်းအောင်လှိုင်/n`, `ဦးစ/n`, `ဦးကျော်ဇော/n`, `ဒေါ်ပြည့်ပြည့်ထွန်း/n`, `ငဘွယ်/n`, `ရှင်ရွှေပုံ/n`, `စိုင်းထီးဆိုင်/n`, `ခွန်ထွန်းဦး/n`)။ အလိုအလျောက် split-prefix စစ်ဆေးမှုများတွင် သံသယကင်းသော ၉ မျိုး (`STRICT_TITLE_PREFIXES: ဦး, ဒေါ်, မောင်, စဝ်, စော, နော်, စလိုင်း, ဆလိုင်း, ဒူဝါ`) ကို အဓိက စံပြုသည်။
    - နိုင်ငံခြားအမည်များအတွင်း ပါဝင်သော `ကို` (`ဒိုမီနစ်/n လီဗာကိုဗစ်ချ်/n` — Serbian/Croatian `-vić`, Latin `Ko-`) ကို ရှေ့ဆက် `ကို` ဟု မှားမဖြတ်ရ (`လီဗာ ကို ဗစ်ချ်` မဖြစ်စေရ)။
    - ရာထူး၊ အဆင့်အတန်းနှင့် ဘွဲ့ထူးဂုဏ်ပုဒ် ၄၉ မျိုး (`scripts/common_standards.py: TITLES_AND_RANKS` ဥပမာ `သံအမတ်ကြီး/n`, `ဗိုလ်ချုပ်ကြီး/n`, `စော်ဘွားကြီး/n`, `ဒေါက်တာ/n`, `သမ္မတ/n`) နှင့် ဌာန/သမိုင်းတွင် ဂုဏ်ထူးအမည် (`လှေသင်းအတွင်းဝန်/n`, `မဟာဒါန်တိုက်ဝန်/n`, `မြဝတီမင်းကြီး/n`, `ကင်းဝန်မင်းကြီး/n`, `ယောမင်းကြီး/n`) တို့ကို `1 Token /n` အဖြစ် ထားပြီး ကိုယ်ပိုင်အမည်မှ ခွဲထုတ်ရမည် (`မြဝတီမင်းကြီး/n ဦးစ/n`, `မိုင်းပွန်/n စော်ဘွားကြီး/n စဝ်စံထွန်း/n`)။

### 2.3 Registered 15-Tag Corpus Profiles (`general`, `legal70k`, `news_unified`, `legacy_mypos_alt`)

Cross-corpus audits across 9.64M tokens (`mypos+myalt+mymedicon`, `News 70k`, `Legal 70k`, `Shan Yoma v2.15`) confirm systematic profile conventions inside Base-15, centralized in `scripts/common_standards.py` via `--profile`:
- `general`: General Burmese text (default in `decide.py`), clause-final verbal markers = `part`, purposive = `conj`, `သော်` = `conj`, `သင့်` = `part`.
- `legal70k`: Institutional legal corpus (default in `nlp_cli.py -w`), owner component standards (10 rows e.g. `ပုံစံ-က`), clause-final verbal markers = `part`, `သော်` = `part`.
- `news_unified`: News gold corpus (News SOP v3.2), `လေ့လာသုံးသပ်သူ` 1 token, `သင့်` after verb = `v`, `သော်` = `part`.
- `legacy_mypos_alt`: Historical MLC 2013 / `myPOS v3.0` conventions (`mypos+myalt+mymedicon`, Legal L1-2k), clause-final verbal `သည်/တယ်/မည်/မယ်/၏` = `ppm` (HD `ppm:fin`), purposive = `conj`, `သော်` = `conj`.

| Grammatical Construct | `unified_modern` (`general`, `legal70k`, `news_unified`) | `legacy_mypos_alt` (`mypos+myalt+mymedicon`, `Legal L1–2k`) | `myPOS-HD` & `UD v2` Projection (Unified) |
|---|---|---|---|
| Clause-final verbal `သည် / တယ် / မည် / မယ် / ၏` | `part` | `ppm` (MLC `ကြိယာဝိဘတ်` `pos_copula_ppm`) | `part:sfp` / `ppm:fin` -> `PART (Mood=Ind)` |
| Clause-chaining `V + ပြီး + V/N` | `part` (aspect/seq) | `conj` (per `Doc_010` gate) | `part:aux` (final) / `conj:sub` (chaining) |
| Comparative `NP + ထက်` | `ppm` | `conj` (or `ppm` in newer sets) | `ppm:obl` -> `ADP` |
| Purposive `[V] + ရန် / အောင်` | `conj` (`general`/`news`/`legal`) / `part` (`Shan Yoma`) | `conj` | `conj:purp` -> `SCONJ` |
| Temporal/Conditional `သော်` | `part` (`legal70k`, `news_unified`) / `conj` (`general`, Shan Yoma) | `conj` | `conj:sub` -> `SCONJ (VerbForm=Conv)` |
| Modal / Auxiliary `သင့်` after verb | `part` (`general`, `legal70k`) / `v` (`news_unified` News SOP v3.2) | `part` | `part:aux` (`general`/`legal70k`/`legacy_mypos_alt`) / `VERB` (`news_unified`) |
| Demonstrative `ဤ / ထို / ယင်း / ၎င်း + Noun` | `adj` before `N`, `pron` before `ppm`/`punc` | Mixed `adj`/`pron` | `adj:det` -> `DET` (adnominal) / `pron:dem` -> `PRON` |

> **Never confuse Base-15 profile variance with structural defects**: Tagging Myanmar letters `၏`/`၍` as `/punc`, tagging `[num/tn] ဦး` as `/n`, tagging `တပါး`/`တစ်ပါး` by spelling alone without context, or splitting person-name prefixes (`ဦး/n ကျော်ဇော/n`) are hard defects in ALL profiles.

## 3. High-Frequency Contextual POS Disambiguation Decision Trees

Never assign a single static dictionary tag to polyfunctional Burmese tokens. Evaluate the full clause and immediate syntactic frame:

| Surface Form | Possible Tags | Contextual Decision Rule | Contrasting Examples |
| --- | --- | --- | --- |
| **`သည်`** | `ppm`, `part`, `adj` | 1. After NP / Pronoun / plural-quantifier (`တို့, များ, လုံး, တိုင်း`) as subject marker -> `ppm`<br>2. Nominalizing particle after V before case marker (`ဆို/v သည်/part မှာ/ppm`) -> `part` (and `မှာ` is strictly `ppm`)<br>3. Sentence/clause-final realis marker after V -> `part`<br>4. Pre-nominal demonstrative ("this") -> `adj` / `pron` | `တရားလို/n သည်/ppm လျှောက်ထား/v သည်/part ။/punc`<br>`နိုင်ငံတော်/n ဆို/v သည်/part မှာ/ppm ...`<br>vs. `အမှုသည်/n` (lexicalized noun "litigant", 1 token) |
| **`က`** | `ppm`, `conj`, `n`, `v`, `sb` | 1. Subject or ablative ("from") marker after NP -> `ppm`<br>2. Conditional clause marker ("if", `ပါ က` / `V က`) -> `conj`<br>3. Parenthetical subclause bullet `(/punc က/sb )/punc` -> strictly `sb` (never tag non-parenthetical `က` as `sb`)<br>4. Lexical noun ("saddle") or verb ("dance") -> `n` / `v` | `ရန်ကုန်/n က/ppm လာ/v သည်/part` (`ppm`)<br>`လိုအပ်/v ပါ/part က/conj ဆောင်ရွက်/v ရ/part မည်/part` (`conj`)<br>`(/punc က/sb )/punc` (`sb`) |
| **`နှင့်` / `နဲ့`** | `conj`, `ppm`, `part` | 1. Coordinating two NPs (`NP1 နှင့် NP2`) -> `conj`<br>2. Instrumental/comitative marker ("with/by") modifying a predicate (`NP နှင့် V`, `နှင့် အညီ`, `နှင့် ပတ်သက်၍`) -> `ppm`<br>3. Sentence-final colloquial prohibitory/modal (`မပြောနဲ့`) -> `part` | `တရားလို/n နှင့်/conj တရားပြိုင်/n` (`conj`)<br>`ဥပဒေ/n နှင့်/ppm အညီ/ppm` (`ppm`) |
| **`ပေး` / `သွား` / `လာ` / `ထား` / `နေ` / `ခဲ့` / `ပြီး` / `လိုက်`** | `v`, `part` | 1. Immediately following a main verb as an aspectual/auxiliary marker (`V + ပေး/သွား/လာ/ထား/နေ/ခဲ့/ပြီး/လိုက်`) -> `part`<br>2. Standing as the main lexical predicate (preceded by NP/PPM or negation `မ`) -> `v` | `ဆောင်ရွက်/v ပေး/part သွား/part မည်/part` (`part`)<br>`ငွေ/n ပေး/v ပြီး/part ကျောင်း/n သို့/ppm သွား/v သည်/part` (`v`) |
| **`အဖြစ်`** | `ppm`, `n` | 1. Role/capacity marker ("as") or nominalized state (`သက်သေ အဖြစ်`) -> `n` or `ppm` per syntactic slot<br>2. Inflected with case/plural/possessive (`အဖြစ် ကို`, `အဖြစ် မှ`, `အဖြစ် များ`) -> `n` | `ဖြစ်ရပ်/n အဖြစ်/n မှန်/adj` (`n`) |
| **`ရာ`** | `part`, `n`, `tn`, `conj` | 1. After an action/process verb (`[V]` or `[V] + ကြ/part`) in `[V] + ရာ + တွင်/၌/မှ`, `[V] + ရာ + ရောက်/v`, `[V1] + ရာ + [V1] + ကြောင်း`, or `[V] + ရာ + [N]` -> strictly `part` (never `v` or `n`)<br>2. Denoting a physical place (နေရာ၏ `ရာ`) or object/thing (အရာဝတ္ထု၏ `ရာ`) in lexicalized nouns (`နေရာ/n`, `အရာ/n`, `ရိုက်ရာ/n`) -> `n`<br>3. Numeral "hundred" (`တ/tn ရာ/tn`, `နှစ်/tn ရာ/tn`, `သုံး/tn ရာ/tn`) -> `tn` | `ဆောင်ရွက်/v ရာ/part တွင်/ppm` (`part`)<br>`ပြန့်/v ရာ/part နယ်မြေ/n` (`part`)<br>`သုံး/tn ရာ/tn စီ/part` (`tn`) |
| **`ဟု` / `ဟူ၍` / `ဟူသော` / `ဟူသည်`** | `part` | Quotative and complementizer particles introducing or closing quoted speech, definitions, or stipulations -> strictly `part` (never `ppm`, `conj`, or `v`) | `အတည်/n ဖြစ်/v သည်/part ဟု/part မှတ်ယူ/v ရ/part မည်/part` (`part`) |
| **`ပြီး`** | `part`, `conj`, `v` | 1. Aspectual auxiliary after verb (`V + ပြီး`) -> `part`<br>2. Lexicalized sequential conjunction (`ပြီးလျှင်/conj`, `ပြီးနောက်/conj`) -> `conj`<br>3. Main verb ("to finish") -> `v` | `ဆောင်ရွက်/v ပြီး/part ဖြစ်/v သည်/part` (`part`)<br>`အတည်ပြု/v ပြီးနောက်/conj` (`conj`) |
| **`ဖြစ်စေ`** | `conj`, `v + part` | 1. Correlative disjunction (`X ဖြစ်စေ ၊ Y ဖြစ်စေ` = "whether X or Y") -> 1 token `ဖြစ်စေ/conj`<br>2. Causative verb construction (`အထောက်အကူ ဖြစ် စေ ရန်`) -> 2 tokens `ဖြစ်/v စေ/part`<br>3. Nominalized causative (`အထောက်အကူ ဖြစ် စေရေး`) -> `ဖြစ်/v စေရေး/n` (or `part` per corpus profile) | `တိုက်ရိုက်/adv ဖြစ်စေ/conj ၊/punc သွယ်ဝိုက်/v ၍/conj ဖြစ်စေ/conj`<br>vs. `အကျိုး/n ဖြစ်/v စေ/part သည်/part` |
| **`တစ်စုံတစ်ရာ` / `တစုံတရာ`** (and `-ဦး/-ယောက်/-ခု`) | `pron`, `adj` | 1. Stands alone as an NP head (followed by `ကို, က, သည်, ၏, မှ` or acting as argument) -> `pron`<br>2. Modifies an adjacent noun (`အကြောင်း တစ်စုံတစ်ရာ`, `တစ်စုံတစ်ရာ သော အကြောင်း`) -> `adj` (Never use `DET` in myPOS) | `တစ်စုံတစ်ရာ/pron ကို/ppm မ/part ပြော/v`<br>`ကိစ္စ/n တစုံတရာ/adj ပေါ်ပေါက်/v လျှင်/conj` |
| **`တစ်စိတ်တစ်ပိုင်း` / `တစ်စိတ်တစ်ဒေသ`** | `n`, `adv` | 1. Head of a noun phrase ("a portion/part", e.g., followed by `ကို, အား, သည်`) -> `n`<br>2. Adverbially modifying a verb ("partially") -> `adv` | `ပစ္စည်း/n ၏/ppm တစ်စိတ်တစ်ပိုင်း/n ကို/ppm`<br>`တစ်စိတ်တစ်ပိုင်း/adv သဘောတူ/v သည်/part` |
| **`မ`** | `part`, `n`, `adj` | 1. Pre-verbal negation (`မ သွား`, `အတည် မ ပြု`) -> separate token `မ/part`<br>2. Female gender noun in `ကျား/n -/punc မ/n ဘာဝ/n` -> `n`<br>3. Civil/main compound (`တရားမ/adj`, `ခန်းမ/n`, `ပင်မ/adj`, `သွေးကြောမကြီး/n`) -> keep merged | `တရား/n မ/part ဝင်/v သော/part` (`မ/part`)<br>`ကျား/n -/punc မ/n ဘာဝ/n` (`မ/n`) |
| **`ဒသမ` & Ordinals** | `adj`, `n` | 1. Ordinals (`ပထမ, ပဌမ, ဒုတိယ, တတိယ, စတုတ္ထ ... ဒသမ` meaning "10th") -> `adj`<br>2. Decimal point between numerals (`သုည/tn ဒသမ/n တစ်/tn ရာခိုင်နှုန်း/n`) -> `n` | `ဒုတိယ/adj အကြိမ်/n` (`adj`)<br>`သုည/tn ဒသမ/n တစ်/tn` (`n`) |
| **`အား`** | `ppm`, `n` | 1. Dative/accusative case marker after animate/recipient NP -> separate `အား/ppm`<br>2. Lexical noun meaning "strength/force/power" (`အင်အား`, `ဖိအား`, `ဓာတ်အား`, `လုပ်အား`, `အား စိုက်`) -> `n` | `တရားခံ/n အား/ppm စစ်ဆေး/v သည်/part`<br>`အန္တရာယ်/n ကင်း/v ဖိအား/n ထိန်း/v အဆို့ရှင်/n` |
| **`ရန်` / `အောင်`** | `conj`, `part`, `n` | 1. Purposive clause subordinator directly after a verb (`တည်ထောင်/v ရန်/conj`, `ငုံမိ/v အောင်/conj`) -> `conj` (`unified_modern`/`News`/`Legal`) or `part` (`Shan Yoma`); projects uniformly to `conj:purp` (`SCONJ`) in `myPOS-HD`<br>2. Noun meaning "enmity/danger" (`ရန်/n ငြိုး/n`) -> `n` | `ဖွံ့ဖြိုး/v စေ/part ရန်/conj ဆောင်ရွက်/v` |
| **`ထက်`** | `ppm`, `conj`, `n` | 1. Comparative postposition after NP (`ခန့်မှန်းချက်/n ထက်/ppm ပို/adv`, `သူတပါး/n ထက်/ppm`) -> `ppm` (legacy `myPOS` sometimes uses `conj`)<br>2. Spatial/rank noun "upper/top" -> `n` | `ယခု/adj အခြေအနေ/n ထက်/ppm ပိုမို/adv` |
| **`ဤ` / `ထို` / `ယင်း` / `၎င်း` / `ဒီ`** | `adj`, `pron`, `conj` | 1. Directly modifying a following noun (`ဤ/adj ဥပဒေ/n`, `ထို/adj မဂ္ဂဇင်း/n`, `ယင်း/adj နေရာ/n`) -> **`adj`** (`adj:det` -> UD `DET`)<br>2. Standing as NP head before `ppm`, plural `တို့/များ`, or `punc` (`ယင်း/pron တို့/part ကို/ppm`, `၎င်း/pron သည်/ppm`) -> **`pron`** (`pron:dem`)<br>3. Coordinated list separator `၎င်း ၊` -> `conj` (`News`/`Legal` legacy often force `pron` globally, so project via right-context check) | `ဤ/adj ဖွဲ့စည်းအုပ်ချုပ်ပုံ/n ကို/ppm`<br>vs. `ဤ/pron သည်/ppm` |
| **`ပဲ` / `ချေ`** | `part` | 1. Within the current clause (after last `punc`/`conj`), if negated by pre-verbal `မ/part` -> `part:neg` (`Polarity=Neg`, e.g., `မ/part သွား/v ပဲ/part`)<br>2. Without `မ/part`, colloquial `ပဲ` -> `part:foc` (emphasis/only: `တကယ်/adv ပဲ/part`); literary `ချေ` -> `part:aux` / `part:sfp` (`ဆို/v ချေ/part ၏/part`) | `မ/part ပြန်/v တော့/part ပဲ/part` (`part:neg`)<br>vs. `ကောင်း/v တာ/part ပဲ/part` (`part:foc`) |
| **`ဘွဲ့ခံ` / `ဘွဲ့ရ`** | `adj`, `v` | 1. Pre-nominal title epithet (`မဟာဇေယျသင်္ခယာ/n ဘွဲ့ခံ/adj လှေသင်းအတွင်းဝန်/n`) -> `adj`<br>2. Finite predicate (`... ဘွဲ့/n ခံ/v သည်/part`) -> split/verbal | `ဇေယသင်္ခယာ/n ဘွဲ့ရ/adj မြဝတီမင်းကြီး/n ဦးစ/n` |
| **`[V] + သူ`** | `pron` | Post-verbal / action nominal agentive/relativizer pronoun ("one who [verbs]", e.g., `လျှောက်ထား/v သူ/pron`, `ကြီးကြပ်/v သူ/pron`, `ဆက်နွှယ်/v သူ/pron များ/part`) -> strictly **`pron`** in Base-15 & `myPOS-HD v4.1`, **`PRON`** in UD (per `scripts/project_mypos_hd.py:331-339` and `common_standards.py`; harmonizing older notes that labeled it as `part` or `n` without context). Do not split lexicalized nouns (`ပြည်သူ/n`, `တောင်သူ/n`, `ကျောင်းသူ/n`). | `လျှောက်ထား/v သူ/pron`<br>vs. `ပြည်သူ/n` (1 token) |
| **`သော်`** | `conj`, `part` | Subordinating temporal/conditional clause marker ("when / if", e.g., `ရှု သော်`, `ဆောင် ပါ သော်`) -> tagged **`conj`** in `general` and `legacy_mypos_alt`; tagged **`part`** in `legal70k` and `news_unified`. Projects losslessly in `myPOS-HD v4.1` to **`conj:sub`** -> UD **`SCONJ (VerbForm=Conv)`**. Distinct from compound adversative `သော်လည်း/conj`. | `ရှု/v သော်/conj` (HD: `conj:sub`)<br>`ဆောင်/v ပါ/part သော်/conj` |
| **`သင့်`** | `part`, `v`, `pron` | 1. Modal / debitive after verb ("should/ought to", e.g., `လိုက်နာ/v သင့်`) -> **`part`** (`part:aux` -> UD `AUX`) in `general`, `legal70k`, `legacy_mypos_alt`; **`v`** (UD `VERB`) in `news_unified` (News SOP v3.2)<br>2. Root lexical verb ("to befit, be appropriate" e.g., `မ/part သင့်/v လျော်/v`, `သင့်လျော်/v`, or "be struck" `ကျည်သင့်/v`) -> **`v`** (UD `VERB`)<br>3. Formal / archaic 2sg pronoun ("you/your", e.g., `သင့်/pron ၏/ppm အကြံ/n`, `သင့်/pron စိတ်/n`, `သင့်ကို/pron`) -> **`pron`** (UD `PRON`) | `လိုက်နာ/v သင့်/part သည်/part`<br>`မ/part သင့်/v လျော်/v`<br>`သင့်/pron ၏/ppm စိတ်/n` |

## 4. `myPOS-HD (v4.1)` Hierarchical Dual-Layer Specification (Additive & Lossless)

Base-15 corpus streams (`ws.txt`, `pos.txt`, TSV `pos`) remain strictly constrained to the 15 lowercase tags (`ALLOWED_15_TAGS`). To unlock fine-grained distinctions for NER, UD v2 Treebanks, and Legal IE **with zero breaking changes**, `scripts/project_mypos_hd.py` projects Base-15 into hierarchical `base:sub` notation (`pos_hd`), an expanded flat tier (`pos_core`), and UD v2 (`upos` + `feats`):

- **100% Lossless Base-15 Recovery**: `collapse_to_mypos15(hd_tag)` = `"num"` if `hd_tag == "num:latn"` else `hd_tag.split(":")[0]`.
- **Canonical `base:sub` Sub-Tags**:
  - **Nominals**: `n` (common), `n:prop` (1-token personal names with prefix, royal titles, toponyms -> `PROPN`), `n:gen` (attested creaky-tone genitive whitelist `မြန်မာ့, နိုင်ငံ့, ပြည်သူ့, အရှင့်, ပညာ့, ဘုရာ့, ဘုရင့်, မင့်...` — **never** lexical `-့` words like `မြို့, နေ့, ဘွဲ့, အဖွဲ့`), `n:rel` (spatial/relational nouns `အတွင်း, အပေါ်, အောက်, အကြား, အနက်, ထံ`).
  - **Pronouns & Predicates**: `pron`, `pron:dem`, `pron:gen` (`သူ့, ငါ့, ကျွန်တော့်, ကိုယ့်, မည်သူ့` — never invalid `-း + -့` spellings; `သူ` projects to `pron` -> `PRON`), `v`, `v:stat` (stative quality predicates -> UD `ADJ`).
  - **Modifiers & Determiners**: `adj`, `adj:det` (`ဤ, ထို, ယင်း, အဆိုပါ, ဒီ, မည်သည့်` -> `DET`), `adj:ord` (Pali ordinals `ပထမ..ဝီသတိမ`), `adv` (bare adverbs `ချက်ချင်း, လွတ်လပ်စွာ`).
  - **Postpositions (`ppm`)**: `ppm` (bare case markers), `ppm:subj` (`သည်, က, မှာ, ဟာ`), `ppm:obj` (`ကို, အား`), `ppm:obl` (`တွင်, ၌, မှ, သို့, ဖြင့်, ကြောင့်, အတွက်, အရ, ထက်, နှင့်, နဲ့, ထံ, မို့`), `ppm:gen` (`၏, ရဲ့`), `ppm:fin` (`legacy_mypos_alt` clause-final verbal `သည်, တယ်, မည်, မယ်, ၏` -> UD `PART[Mood=Ind]`).
  - **Particles (`part`)**: `part` (bare particles), `part:neg` (only `မ` or clause-bounded `မ ... ဘူး/ဘဲ/ပဲ/နဲ့/ချေ/လင့်`), `part:aux` (`နိုင်, ရ, စေ, ခဲ့, နေ, ထား, ပြီး, ပေး, သွား, လာ, လိုက်, တော်မူ, ဘိ, လေ`), `part:clf` (after `num`/`tn` — `ဦး, ယောက်, ခု, ကြိမ်, ပါး, ချောင်း...`), `part:ord` (`မြောက်` strictly after `ORD_PRECEDING_SET`), `part:nom` (`ခြင်း, မှု, ခွင့်, ရာ, ချက်`, `သည်` before `ppm`), `part:rel` (`သော, သည့်, မည့်, တဲ့, မယ့်` — kept distinct from `nom`!), `part:sfp` (`သည်, မည်, ၏, ပြီ, တယ်, မယ်, ပါ, လေ, ချေ, တည်း, သတည်း, အံ့`), `part:quot` (`ဟု, ဟူ၍, ဟူသော, ဟူသည်`), `part:pl` (`များ, တို့` -> `Number=Plur`), `part:approx` (`ခန့်, လောက်, နီးပါး, ကျော်` — **no** `Number=Plur`), `part:quant` (`တိုင်း, စီ, လုံး`), `part:foc` (`သာ, လည်း, ပင်, မျှ, တော့, ကား, မူ`, affirmative `ပဲ`).
  - **Conjunctions, Numerals & Symbols**: `conj` (bare conjunctions), `conj:coord`, `conj:sub`, `conj:purp` (`ရန်, အောင်`), `conj:disc` (`ထို့ကြောင့်, သို့သော်, သို့ရာတွင်`), `num`, `num:latn` (`[0-9]+` -> `NUM`), `tn`, `abb` (`NOUN`/`PROPN`, `Abbr=Yes`), `fw` (`X`, `Foreign=Yes`), `int` (`INTJ`), `punc` (`PUNCT`), `sb`, `sb:enum` (`( က )`).
- **All 46 `ALLOWED_HD_TAGS` Explicitly Verified**: `abb, adj, adj:det, adj:ord, adv, conj, conj:coord, conj:disc, conj:purp, conj:sub, fw, int, n, n:gen, n:prop, n:rel, num, num:latn, part, part:approx, part:aux, part:clf, part:foc, part:neg, part:nom, part:ord, part:pl, part:quant, part:quot, part:rel, part:sfp, ppm, ppm:fin, ppm:gen, ppm:obj, ppm:obl, ppm:subj, pron, pron:dem, pron:gen, punc, sb, sb:enum, tn, v, v:stat`.

## 5. Flexible Multi-Workflow Architecture & Phase 5 Open Design Trade-Offs

### 5.1 Single Source of Truth (`scripts/common_standards.py`)
All constants, inventories, profiles, and parsing functions across the codebase are centralized in `scripts/common_standards.py`:
- `ALLOWED_15_TAGS`: The 15 canonical lowercase tags (`abb, adj, adv, conj, fw, int, n, num, part, ppm, pron, punc, sb, tn, v`).
- `PROFILES`: `("general", "legal70k", "news_unified", "legacy_mypos_alt")`.
- `PERSON_PREFIXES` (19) & `STRICT_TITLE_PREFIXES` (9).
- `TITLES_AND_RANKS` (49 titles and ranks, sorted longest-first).
- `CLASSIFIERS` (25 true nominal classifiers) & `TIME_MEASURE_NOUNS` (8 time nouns).
- `SUBSECTION_CONSONANTS` (41 Myanmar subsection letters).
- `OWNER_FIXED_TAG_SURFACES` (11 exact surfaces) & `OWNER_COMPONENT_STANDARDS_ORDERED` (14 surfaces / 10 rows).
- `RECORD_ONLY_LEADS` (8 lead patterns).
- Utility functions: `normalize_profile()`, `strip_ws()`, `parse_pos_token()`.

### 5.2 Multi-Workflow Profiles Overview
Tools (`scripts/nlp_cli.py`, `scripts/decide.py`, `scripts/project_mypos_hd.py`, `scripts/validate_nlp_corpus.py`, `scripts/corpus_chunk_and_remediate.py`, `scripts/legal70k_audit.py`) accept `--profile {general, legal70k, news_unified, legacy_mypos_alt}`:
1. **`general`** (General Burmese text): Default in `decide.py`. Clause-final markers = `part`, purposive `ရန်/အောင်` = `conj`, `သော်` = `conj`, modal `သင့်` = `part`.
2. **`legal70k`** (Institutional Legal Corpus): Default in `nlp_cli.py -w`. Strict owner component standards (10 rows), clause-final markers = `part`, `သော်` = `part`, modal `သင့်` = `part`.
3. **`news_unified`** (News Gold Corpus): News SOP v3.2. 5-syllable terms like `လေ့လာသုံးသပ်သူ` = `1 Token /n`, clause-final markers = `part`, `သော်` = `part`, modal `သင့်` after verb = `v` (`VERB`).
4. **`legacy_mypos_alt`** (MLC 2013 / myPOS v3.0 / Legal L1-2k): Clause-final verbal markers (`သည်/တယ်/မည်/မယ်/၏`) = `ppm` (`pos_copula_ppm`), `သော်` = `conj`, modal `သင့်` = `part`.

### 5.3 Codepoint Conservation vs. Opt-In `--normalize-confusables`
- **Conservation Default**: Tools preserve original source codepoints and character offsets by default (`re.sub(r"\s+", "", before) == re.sub(r"\s+", "", after)`). Word segmentation and POS tagging do not alter codepoints.
- **Opt-In Normalization**: Passing `--normalize-confusables` applies confusable normalization (e.g., `၀/ဝ`, `၇/ရ`, `၈/ဂ`, `၄/၎`, `စျ/ဈ`, `ဦ/ဦ`) before segmentation.
- **Rollback Guard**: In corpus remediation, non-whitespace character modifications trigger an automated rollback.

### 5.4 myPOS-HD v4.1 Additive Projection
- Base-15 (`mypos15`) <-> `mypos_hd` (`base:sub`, 46 tags) <-> `mypos_core` (10 expanded flat tags) <-> Universal Dependencies v2 (`upos` + `feats`).
- 100% Lossless round-tripping: `collapse_to_mypos15(hd_tag)` recovers the exact canonical Base-15 tag.

### 5.5 Phase 5 Open Design Trade-Offs
1. **Title/Rank vs Personal Name Segmentation (`မြဝတီမင်းကြီး`, `လှေသင်းအတွင်းဝန်`)**:
   - Official titles and ranks are kept as single token nouns (`မြဝတီမင်းကြီး/n`, `လှေသင်းအတွင်းဝန်/n` in `TITLES_AND_RANKS`), kept distinct from personal names (`ဦးစ/n`, `ဦးမောင်ကြီး/n`).
   - Trade-off: Further decomposing titles (e.g., `မြဝတီ/n မင်းကြီး/n`) breaks Downstream NER Title-Person boundaries (`B-PER` / `O`). Modern administrative corpora require atomic titles, whereas historical morphological analyses may prefer compositional breakdown.
2. **Reversible 3-Slot `compound_groups` Layering**:
   - Slot 1: Syllable/orthographic token sequence (`မြန် | မာ | နိုင် | ငံ | တော်`).
   - Slot 2: Canonical Base-15 syntactic word tokens (`မြန်မာ/n နိုင်ငံတော်/n`).
   - Slot 3: Multi-word expression / compound grouping annotations (`[မြန်မာနိုင်ငံတော်] = မြန်မာ/n + နိုင်ငံတော်/n`).
   - Allows syntactic parsers to consume fine-grained syntactic heads while search/NER models consume unified entity spans.
3. **Archaic vs Modern Corpus Expectations**:
   - Historical corpora (Konebaung edicts, palm-leaf literature) feature variant orthography (`တပါးသူ`, `ရွှေမင်ကြောင်း`, non-standard virama stacking, Pali loan phrases).
   - Rigid application of modern news/legal standards causes artificial over-segmentation or invalid typo flags. Profile-aware configuration (`legacy_mypos_alt` or future `archaic_epigraphic` profiles) preserves authentic phonological and orthographic structures.

