# POS Tagset & Universal Dependencies Mapping (`MLC 9-Class` <-> `myPOS 15-Tag` <-> `UD v2`)

This reference defines the exact cross-framework mapping and contextual disambiguation rules between:

1. **MLC 9 Word Classes (ဝါစင်္ဂ ၉ မျိုး)**: The Myanmar Language Commission reference grammar (`chapters/ch10` to `ch17`).
2. **Corpus `myPOS` 15-Tag Vocabulary**: The canonical lowercase 15-tag output set used in `myPOS-ver.3.0`, `Legal70k`, and `corpus_manager` (`abb`, `adj`, `adv`, `conj`, `fw`, `int`, `n`, `num`, `part`, `ppm`, `pron`, `punc`, `sb`, `tn`, `v`).
3. **Universal Dependencies (`UD v2`)**: The `UPOS` and `DEPREL` layers used in `myUDTree` and `CoNLL-U` exports.

**Important Output Rule**: Never mix tagsets in a single output stream. When producing `myPOS` / `Legal70k` annotations, emit **only** the 15 lowercase tags (`abb, adj, adv, conj, fw, int, n, num, part, ppm, pron, punc, sb, tn, v`). Do not emit UD tags like `DET`, `PROPN`, `AUX`, `ADP`, or `SCONJ` into a `myPOS` tag column.

## 1. Complete 3-Way Tagset Alignment Matrix

| `myPOS` Tag (15-Tag Set) | MLC 9-Class Equivalent (ဝါစင်္ဂ ၉ မျိုး) | `UD v2` UPOS Mapping (`mya-pos-v1`) | Primary Syntactic / Dependency Roles (`DEPREL`) | Examples (`word/tag`) |
| --- | --- | --- | --- | --- |
| **`n`** | နာမ် (သာမညနာမ်၊ သမ္မာနာမ်၊ စုပေါင်းနာမ်၊ ဒြပ်ရှိ/ဒြပ်မဲ့နာမ်) (Ch 10) | `NOUN` (or `PROPN` for proper names in UD) | `nsubj`, `obj`, `obl`, `nmod`, `compound`, `appos`, `root` (nominal predicate) | `ကျောင်း/n`, `ရန်ကုန်/n`, `လွတ်လပ်ရေး/n`, `တကျွန်းပို့ဒဏ်/n` |
| **`pron`** | နာမ်စား (ပုဂ္ဂလ၊ အညွှန်း၊ အမေး၊ သင်္ချာနာမ်စား) (Ch 11) | `PRON` | `nsubj`, `obj`, `obl`, `nmod:poss` | `ကျွန်တော်/pron`, `သူ/pron`, `၎င်း/pron`, `အဲဒါ/pron`, `တစ်စုံတစ်ရာ/pron` (nominal use) |
| **`v`** | ကြိယာ (ကံလို၊ ကံမလို၊ ဖြစ်ခြင်းပြ၊ ရှိခြင်းပြ) (Ch 13) | `VERB` (or `ADJ` for stative roots in UD; see Section 2.1) | `root`, `acl`, `advcl`, `ccomp`, `xcomp`, `compound:svc` | `ဆောင်ရွက်/v`, `စစ်ဆေး/v`, `ဖြစ်/v`, `ရှိ/v`, `လိုက်နာ/v` |
| **`adj`** | နာမဝိသေသန (ဂုဏ်ရည်ပြ၊ အညွှန်း၊ အရေအတွက်ပြ) (Ch 12) | `ADJ` (or `DET` for demonstratives in pure UD; never use `DET` in myPOS) | `amod`, `acl` | `ရဲရင့်/adj`, `အဆိုပါ/adj`, `အချင်းဖြစ်/adj`, `တမျိုးတည်း/adj`, `တဦးတည်းပိုင်/adj`, `တချက်လွှတ်/adj` |
| **`adv`** | ကြိယာဝိသေသန (အမူအရာ၊ အချိန်၊ ပမာဏပြ) (Ch 14) | `ADV` | `advmod` | `လွတ်လပ်စွာ/adv`, `ချက်ချင်း/adv`, `တပြိုင်နက်/adv`, `တခါတရံ/adv`, `တဖက်သတ်/adv`, `တဆက်တည်း/adv` |
| **`ppm`** | ဝိဘတ် (နာမ်ဝိဘတ် ၇ မျိုး နှင့် ကြိယာဝိဘတ်) (Ch 15) | `ADP` | `case` (when attached to nominal head), `mark` | `သည်/ppm`, `က/ppm`, `ကို/ppm`, `အား/ppm`, `တွင်/ppm`, `၌/ppm`, `မှ/ppm`, `သို့/ppm`, `ဖြင့်/ppm`, `၏/ppm` |
| **`part`** | ပစ္စည်း (နာမ်ပစ္စည်း၊ ကြိယာပစ္စည်း၊ မျိုးပြပစ္စည်း၊ အငြင်းပြ `မ`) (Ch 16) | `PART` (or `AUX` for modal/aspect auxiliaries in UD) | `aux`, `mark`, `advmod` (negation `မ`), `clf`, `case` | `များ/part`, `တို့/part`, `မ/part`, `ခဲ့/part`, `နိုင်/part`, `စေ/part`, `သော/part`, `သည့်/part`, `မှု/part`, `ခြင်း/part`, `ဦး/part` |
| **`conj`** | သမ္ဗန္ဓ (ပုဒ်ချင်းဆက်၊ ဝါကျဆက်) (Ch 16) | `CCONJ` (coordinating) / `SCONJ` (subordinating in UD) | `cc`, `mark` | `နှင့်/conj`, `သို့မဟုတ်/conj`, `သော်လည်း/conj`, `သောကြောင့်/conj`, `သဖြင့်/conj`, `၍/conj`, `ဖြစ်စေ/conj` |
| **`num`** | ကိန်းဂဏန်းအက္ခရာ (သင်္ချာနာမ်/နာမဝိသေသန - ဂဏန်းသင်္ကေတ) (Ch 11, 12) | `NUM` | `nummod` | `၁/num`, `၂/num`, `၁၀၀/num`, `၁,၀၀၀/num`, `၁၉၆၆/num` |
| **`tn`** | စာလုံးဖြင့်ရေးသော ကိန်းဂဏန်း (Textual Number) (Ch 11, 12) | `NUM` | `nummod` | `တစ်/tn`, `နှစ်/tn`, `သုံး/tn`, `ငါးဆယ်/tn`, `တစ်ထောင်/tn`, `နှစ်သိန်း/tn` |
| **`int`** | အာမေဍိတ် (Ch 17) | `X` (`INTJ` in standard UD) | `discourse` | `အမလေး/int`, `ဪ/int`, `ဟယ်/int` |
| **`punc`** | ပုဒ်ဖြတ်ပုဒ်ရပ်သင်္ကေတ (Ch 20) | `PUNCT` | `punct` | `၊/punc`, `။/punc`, `(/punc`, `)/punc`, `“/punc`, `”/punc` |
| **`abb`** | အတိုကောက် စကားလုံး (Abbreviation) | `X` (`NOUN`/`PROPN` in UD) | `nsubj`, `obl`, `compound`, `appos` | `အထက/abb`, `လ.ဝ/abb`, `ကုလ/abb`, `ပုဒ်မခွဲ/n` (full words are `n`, only true abbreviations are `abb`) |
| **`fw`** | နိုင်ငံခြားစကားလုံး (Foreign Word / Script) | `X` (`PROPN`/`SYM` in UD) | `flat:foreign`, `appos`, `compound` | `Myanmar/fw`, `BBC/fw`, `Google/fw`, `1/fw`, `2/fw` (ASCII digits in fw convention) |
| **`sb`** | သင်္ကေတ (Symbol) | `X` (`SYM` in UD) | `dep`, `cc`, `punct` | `%/sb`, `$/sb`, `+/sb`, `=/sb`, `#/sb`, `&/sb`, `@/sb` |

## 2. Framework Alignment & Structural Harmonization Rules

### 2.1 Stative / Descriptive Roots (`myPOS: v` <-> `UD: ADJ`)

In Burmese morphosyntax, descriptive/quality roots (`လွယ်ကူ`, `ခက်ခဲ`, `လှပ`, `ရဲရင့်`, `ကြီးမား`, `ကောင်းမွန်`) can take verbal endings directly (`လွယ်ကူ သည်`) or adjectival relativizers (`လွယ်ကူ သော`).

- **In `myPOS` (`mya-pos-v1` Doc_016)**: Predicative/verbal occurrences and morphosyntactic stative verbs are tagged `v` (e.g., `လွယ်ကူ/v သည်/ppm`), whereas pre-nominal modifier roots or dedicated adjectival forms are tagged `adj`.
- **In `myUDTree` (`UD v2`)**: Quality words are mapped semantically to `ADJ`.
- **Cross-Project Rule**: Do not blindly re-tag an entire corpus from `v` to `adj` or vice versa; use the alignment mapping `myPOS:v[stative] <-> UD:ADJ[quality]` when converting between formats.

### 2.2 Numeral Tag Split (`num` vs. `tn`)

- **`num`**: Myanmar script digits (`၀-၉`, e.g., `၁/num`, `၂၅/num`, `၁,၀၀၀/num`).
- **`tn`**: Numerals spelled out in Myanmar letters (`တစ်/tn`, `နှစ်/tn`, `သုံး/tn`, `ဆယ်/tn`, `တစ်ရာ/tn`, `တစ်ထောင်/tn`, `တစ်သိန်း/tn`).
- **Disambiguation Trap**:
  - `နှစ်`: Tagged `tn` when meaning "two" (`နှစ်/tn ဦး/part`, `နှစ်/tn ကြိမ်/part`), but tagged `n` when meaning "year" (`၁၉၆၆/num ခုနှစ်/n`, `သုံး/tn နှစ်/n ကြာ/v`).
  - `သုံး`: Tagged `tn` when meaning "three" (`သုံး/tn ခု/part`), but tagged `v` when meaning "to use/spend" (`သုံး/v စွဲ/v`, `ငွေ/n သုံး/v သည်/ppm`).
  - `ဦး`: 
    - သင်္ချာ/ဂဏန်းနောက်မှ လူမျိုးပြပစ္စည်း (Person classifier after numerals, e.g., `တစ်/tn ဦး/part`, `၃/num ဦး/part`) ဖြစ်ပါက `part` အဖြစ် tag လုပ်သည်။ ဘယ်သောအခါမျှ `tn` ဟု မ tag ရ။
    - လူအမည်ရှေ့ဆက် (Personal name prefix, e.g., `ဦးမင်းအောင်လှိုင်/n`, `ဦးကျော်မိုးထွန်း/n`) ဖြစ်ပါက အမည်မှ မခွဲထုတ်ဘဲ တစ်ဆက်တည်း ပေါင်းစည်း၍ နာမ် (`/n`) အဖြစ် သတ်မှတ်သည်။ (သီးခြား `ဦး/part` ဟု မခွဲရ)။
    - ထို့အတူ တိုင်းရင်းသားနှင့် အခြားအမည်ရှေ့ဆက်များ (`ဒေါ်အောင်ဆန်းစုကြည်/n`, `ကိုမင်းကိုနိုင်/n`, `မသီရိစိုး/n`, `စဝ်စံထွန်း/n`, `စောဘဦးကြီး/n`, `နော်စီဖိုးရာစိန်/n`) ကိုလည်း အမည်နှင့် တစ်ဆက်တည်း ပေါင်းစည်းထားသော သမ္မာနာမ် (`/n`) အဖြစ် သတ်မှတ်သည်။
    - သို့သော် ရာထူး၊ အဆင့်အတန်းနှင့် ဘွဲ့ထူးဂုဏ်ပုဒ်များ (`သံအမတ်ကြီး/n`, `ဗိုလ်ချုပ်ကြီး/n`, `စော်ဘွားကြီး/n`, `ဒေါက်တာ/n`, `သမ္မတ/n`) ကိုမူ သီးခြား နာမ်ပုဒ် (`/n`) အဖြစ် ခွဲထုတ်ရမည်။ (ဥပမာ- `မိုင်းပွန်/n စော်ဘွားကြီး/n စဝ်စံထွန်း/n`, `သံအမတ်ကြီး/n ဦးကျော်မိုးထွန်း/n`)။

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
