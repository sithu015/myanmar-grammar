# Word Segmentation Rules, Precedence, Lexicon & Generalization Protocol

This reference consolidates the **Word Segmentation (ပုဒ်ဖြတ်ခြင်း)** rules, rule-precedence hierarchy, lexicon tables, boundary-shift traps, and corpus-wide generalization safeguards for Myanmar NLP.

## 1. Rule Precedence Hierarchy (Apply Strictly in This Order)

When two segmentation or tagging rules appear to conflict, resolve them using this 5-tier precedence order:

1. **Tier 1 - Orthographic & Codepoint Fidelity**: Never alter, modernize, normalize away, insert, or delete non-whitespace source characters (`join(tokens_before) == join(tokens_after)`). Keep archaic spellings (`သမတ`, `ပဌမ`, `စံနစ်`, `ဖေါ်ပြ`, `စီးပွါးရေး`, `ငှါ`, `ဓါတ်ပုံ`, `တစုံတရာ`, `၎င်း`) and OCR typos untouched in the text layer.
2. **Tier 2 - Owner Rules & Explicit Lexicon Entries**: Explicit rulings in `cheatsheet.md#corpus-rules` (the 11 fixed-tag archaic forms, the 10 component-standard rows, the `[တ/တစ် + X + တ/တစ် + Y]` matrix, and the built-in lexicon below) override general morphological heuristics.
3. **Tier 3 - Specific Morphosyntactic Constructions**:
   - The `-ရေး` attachment chain rule
   - `ဖြစ်စေ` vs. `ဖြစ် စေ` vs. `ဖြစ် စေရေး`
   - Pre-verbal negation `မ` separation (except lexicalized `မ-` idioms)
   - Productive `-သူ` agentive relative clauses (split) vs. lexicalized `-သူ` nouns (merged)
   - Personal & Ethnic Name Prefix unity (`ဦး`, `ဒေါ်`, `ကို`, `မ`, `စဝ်`, `စော`, `နော်` merged with given name as 1 token `/n`) vs. Official, Military, Feudal & Academic Title separation (`ဗိုလ်ချုပ်ကြီး`, `သံအမတ်ကြီး`, `စော်ဘွားကြီး`, `ဒေါက်တာ` split as separate `/n` token)
   - Numeral + Classifier separation and `[တ/တစ်]` reduplicated classifiers (`တစ် ဦးဦး`)
4. **Tier 4 - General Word-Class & Compound Rules**: Two-syllable verbs, four-syllable double verbs, object noun + verb separation, postpositional markers (`ppm`), and auxiliary verb chains (`part`).
5. **Tier 5 - Intra-Text Consistency & Review Quarantine**: Maintain identical segmentation for recurring terms within the same document/corpus. If a boundary or POS remains genuinely ambiguous (such as `ငွေ တစ်ရာ` vs. `ငွေ တစ် ရာ`, or unverified proper-name spans), preserve the valid existing segmentation and flag for `review` rather than guessing silently.

## 2. Specific Morphosyntactic Segmentation Rules

### 2.1 The `-ရေး` Nominalization Chain Rule

Attach `-ရေး` **only** to the single token immediately preceding it:

| Case | Pattern | Correct Segmentation | Incorrect Forms to Avoid |
| --- | --- | --- | --- |
| 1. Single verb | `[V]ရေး` | `ကျန်းမာရေး`, `ကာကွယ်ရေး`, `အုပ်ချုပ်ရေး` | `ကျန်းမာ ရေး` |
| 2. Negated verb | `မ [V]ရေး` | `မ ပြိုကွဲရေး`, `မ ပျက်စီးရေး` | `မပြိုကွဲရေး`, `မ ပြိုကွဲ ရေး` |
| 3. Double verb (4 syllables) | `[V1] [V2]ရေး` | `ဖွံ့ဖြိုး တိုးတက်ရေး`, `သယ်ယူ ပို့ဆောင်ရေး` | `ဖွံ့ဖြိုးတိုးတက်ရေး`, `ဖွံ့ဖြိုး တိုးတက် ရေး` |
| 3a. Lexicalized 4-syllable exceptions | `[V1V2]ရေး` (1 token) | `စည်းလုံးညီညွတ်ရေး`, `ငြိမ်ဝပ်ပိပြားရေး` | `စည်းလုံး ညီညွတ်ရေး` |
| 4. Verb + 1 auxiliary | `[V] [Aux]ရေး` | `ဆောင်ရွက် နိုင်ရေး`, `စိစစ် ပေးရေး`, `တိုးတက် စေရေး` | `ဆောင်ရွက်နိုင်ရေး`, `ဆောင်ရွက် နိုင် ရေး` |
| 5. Verb + multiple auxiliaries | `[V] [Aux1] [Aux2]ရေး` | `ဖွံ့ဖြိုး တိုးတက် လာ စေရေး`, `တင်ပြ နိုင် စေရေး`, `ညှိနှိုင်း ပေး နိုင်ရေး` | `လာစေရေး`, `နိုင်စေရေး`, `ပေးနိုင်ရေး` |
| 6. Copula `ဖြစ်` + `စေရေး` | `ဖြစ် စေရေး` | `အထောက်အကူ ဖြစ် စေရေး` | `ဖြစ်စေရေး`, `ဖြစ် စေ ရေး` |

### 2.2 Nominalizers: `မှု`, `ခြင်း`, `ခွင့်`, `-ချက်`, and `-သူ`

- **Productive `မှု`, `ခြင်း`, `ခွင့်` (Separate)**: Keep separate from preceding verbs or auxiliaries:
  - `ဆောင်ရွက် မှု`, `တင်သွင်း ခြင်း`, `သုံးစွဲ ခွင့်`, `ရောင်းချ ခဲ့ ခြင်း`, `ကျေအေး နိုင် ခွင့်`
  - **Auxiliary `ခဲ့` + Nominalizer `မှု` (Strict Separation)**: အတိတ်ကာလပြ `ခဲ့/part` နှင့် နာမ်ပြု `မှု/part` တို့သည် သီးခြားပစ္စည်းများ ဖြစ်သဖြင့် `ခဲ့မှု/n` ဟု မပေါင်းရဘဲ `[Verb]/v ခဲ့/part မှု/part` ဟု အမြဲ သီးခြားစီ ခွဲထုတ်ရမည် (ဥပမာ `ဖျက်ဆီး/v ခဲ့/part မှု/part`, `ပေး/v ခဲ့/part မှု/part`, `ပေးပို့/v ခဲ့/part မှု/part`, `သတ်ဖြတ်/v ခဲ့/part မှု/part`)။
  - **Lexicalized Exceptions (Merged as 1 Token)**: `ပြစ်မှု`, `မှုခင်း`, `တရားမမှု`, `ရာဇဝတ်မှု`, `လူသတ်မှု`, `အပြုအမူ`, `ယဉ်ကျေးမှု`, `ပျော်ရွှင်မှု`, `မူပိုင်ခွင့်`, `အခွင့်အရေး`, `လုပ်ပိုင်ခွင့်`, `စီရင်ပိုင်ခွင့်`, `ပိုင်ဆိုင်ခွင့်`, `ကင်းလွတ်ခွင့်`.
- **Suffix `-ချက်` (Attached to Verb, Split After Auxiliary)**:
  - Attached directly to verb stem: `ပြဋ္ဌာန်းချက်`, `ဆုံးဖြတ်ချက်`, `သတ်မှတ်ချက်`, `ညွှန်ကြားချက်`, `တင်ပြချက်`, `ထွက်ဆိုချက်`, `စီရင်ချက်`, `စွဲချက်`.
  - Split when an auxiliary intervenes: `သတ်မှတ် ထား ချက်`, `ဖော်ပြ ပါ ချက်`.
- **Agentive `-သူ` (Productive Split vs. Lexicalized Merged)**:
  - **Productive Relative-Clause Agent (`V + သူ` -> Split)**: `လျှောက်ထား သူ`, `ကြီးကြပ် သူ`, `ကျူးလွန် သူ`, `ပိုင်ဆိုင် သူ`, `ရှိ သူ`, `ဖြစ် သူ`, `ရင်းနှီးမြှုပ်နှံ သူ`.
  - **Lexicalized Nouns & Titles (Merged as 1 Token)**: `ပြည်သူ`, `အများပြည်သူ`, `တောင်သူ`, `စားသုံးသူ`, `ကျောင်းသူ`, `ရန်သူ`, `ချစ်သူ`, `ဝယ်သူ`, `အခြားသူ`, `တခြားသူ`, `တစ်ပါးသူ`, `မသန်စွမ်းသူ`, `အုပ်ထိန်းသူ`, `ပြောရေးဆိုခွင့်ရှိသူ`, `မဟာသရေစည်သူ`.

### 2.3 Verbs, Double Verbs, and Noun + Verb Constructions

- **2-Syllable Compound Verbs (1 Token)**: `ဆောင်ရွက်`, `စစ်ဆေး`, `ဖမ်းဆီး`, `ကျူးလွန်`, `ရောင်းချ`, `ဝယ်ယူ`, `ပေးအပ်`, `လက်ခံ`, `တင်ပြ`, `တင်သွင်း`, `ထုတ်ပြန်`, `ပြဋ္ဌာန်း`, `ဆုံးဖြတ်`, `သတ်မှတ်`, `ညွှန်ကြား`, `ချမှတ်`, `စွဲဆို`, `ထားရှိ`, `ပျော်ရွှင်`, `ခြောက်လှန့်`.
- **4-Syllable Double Verbs (2 Tokens)**: `ရွေးကောက် တင်မြှောက်`, `တားဆီး ကာကွယ်`, `ပုံနှိပ် ထုတ်ဝေ`, `ဖွံ့ဖြိုး တိုးတက်`, `သယ်ယူ ပို့ဆောင်`, `စုံစမ်း စစ်ဆေး`, `ထိန်းသိမ်း စောင့်ရှောက်`.
- **Syntactic Object Noun + Verb (Separate)**: `မဲ ပေး`, `အမိန့် ချမှတ်`, `တာဝန် ယူ`, `လက်မှတ် ထိုး`, `ခွင့် ပြု`, `ဆန္ဒ ပြု`, `စာရင်း စစ်` (when verbal, e.g., `စာရင်း စစ် ခြင်း`), `တရား စွဲဆို`, `စီရင်ချက် ချမှတ်`, `သတိ ထားရှိ`, `အငြင်း ပွား`.
- **Lexicalized Noun + Verb (Merged as 1 Token)**: `အတည်ပြု`, `အရေးယူ`, `မှတ်ပုံတင်`, `အသုံးပြု`, `တာဝန်ခံ`, `အလေးထား`, `အသိအမှတ်ပြု`, `အကောင်အထည်ဖော်`, `သဘောတူ`, `အလွဲသုံးစားပြု`.

### 2.4 Reduplication (`နှစ်ကြိမ်ထပ်` - Chapter 14)

- **Reduplicated Indefinite Classifiers (Split Num + Reduplicated Clf)**:
  - `တစ် ဦးဦး`, `တ ဦးဦး`, `တစ် ခုခု`, `တ ခုခု`, `တစ် ရပ်ရပ်`, `တ ရပ်ရပ်`, `တစ် ယောက်ယောက်`, `တစ် မျိုးမျိုး`.
  - Keep the reduplicated classifier itself (`ဦးဦး`, `ခုခု`, `ရပ်ရပ်`) as one token when it follows `တစ်`/`တ` in indefinite constructions, or follow corpus-specific gold split (`ခု ခု`) when targeting pure `myPOS` training splits; in `Legal70k`, `တစ် ဦးဦး` / `တ ခုခု` is strictly 2 tokens (`Num + Reduplicated Clf`).
- **Reduplicated Adverbs (1 Token)**:
  - `မြန်မြန်`, `ဖြည်းဖြည်း`, `တဖြည်းဖြည်း`, `မှန်မှန်`, `သက်သက်သာသာ`, `စနစ်တကျ`, `အသီးသီး`, `အမျိုးမျိုး`.

### 2.5 Personal & Ethnic Name Prefixes vs. Official Titles/Ranks (အမည်ရှေ့ဆက် မခွဲခြင်း နှင့် ရာထူး/ဂုဏ်ပုဒ် ခွဲထုတ်ခြင်း စံသတ်မှတ်ချက်)

- **လူမှုရေး၊ ဆွေမျိုးတော်စပ်မှုနှင့် တိုင်းရင်းသား အမည်ရှေ့ဆက်များ (Name Prefixes - Merged as 1 Token `/n`)**:
  - မြန်မာနှင့် တိုင်းရင်းသား အမည်ရှေ့ဆက်များဖြစ်သော `ဦး`, `ဒေါ်`, `ကို`, `မ`, `စဝ်`, `စော`, `နော်`, `စလိုင်း`, `မိုင်း`, `ဒူဝါ`, `နိုင်`, `မန်း` စသည်တို့သည် လူပုဂ္ဂိုလ်၏ အမည်နှင့် တိုက်ရိုက်တွဲစပ်ထားသော Name Prefix များ ဖြစ်သည်။
  - **စည်းမျဉ်း**: အမည်ရှေ့ဆက် (Name Prefix) များကို အမည်မှ **မခွဲဘဲ (Do NOT split)** တစ်ဆက်တည်း ပေါင်းစည်းထားသော သမ္မာနာမ်/တစ်ပုဒ်တည်း (`/n`) အဖြစ် သတ်မှတ်သည်။
  - **မှန်ကန်သော ပုံစံ**:
    - `ဦးမင်းအောင်လှိုင်/n` (မခွဲရ — ❌ `ဦး/part မင်းအောင်လှိုင်/n`)
    - `ဒေါ်အောင်ဆန်းစုကြည်/n` (မခွဲရ — ❌ `ဒေါ်/part အောင်ဆန်းစုကြည်/n`)
    - `ဦးကျော်မိုးထွန်း/n` (မခွဲရ — ❌ `ဦး/part ကျော်မိုးထွန်း/n`)
    - `စဝ်စံထွန်း/n` (စဝ် = Shan honorific name prefix မခွဲရ — ❌ `စဝ်/part စံထွန်း/n`)
    - `ကိုမင်းကိုနိုင်/n`, `မသီရိစိုး/n`, `စောဘဦးကြီး/n`, `နော်စီဖိုးရာစိန်/n`, `စလိုင်းတင်မောင်ဦး/n`, `နိုင်ရွှေကျင်/n`, `ဒူဝါဇော်ရစ်/n`.

- **ရာထူး၊ အဆင့်အတန်း၊ ဘွဲ့ထူးဂုဏ်ပုဒ်၊ အုပ်ချုပ်ရေးနှင့် စစ်ဘက်ရာထူးများ (Official/Feudal/Military/Academic Titles & Ranks - Split as Separate Token `/n`)**:
  - ဥပမာ - `ဗိုလ်ချုပ်ကြီး`, `ဗိုလ်ချုပ်`, `သံအမတ်ကြီး`, `စော်ဘွားကြီး`, `သမ္မတ`, `ဝန်ကြီးချုပ်`, `ဒေါက်တာ`, `ပါမောက္ခ`, `စစ်ခေါင်းဆောင်`, `တရားသူကြီးချုပ်` စသည်တို့သည် သီးခြား အဆင့်အတန်းနှင့် တာဝန်ကို ညွှန်းဆိုသော သာမည/ဝေါဟာရ နာမ်ပုဒ်များ ဖြစ်ကြသည်။
  - **စည်းမျဉ်း**: ရာထူး၊ အဆင့်အတန်းနှင့် ဘွဲ့ထူးဂုဏ်ပုဒ်များကို အမည်ရှေ့မှ **သီးခြား ခွဲထုတ်သည် (Segment as a separate noun token `/n`)**။
  - **မှန်ကန်သော တွဲစပ်ပုံ ဥပမာများ**:
    - `မိုင်းပွန်/n စော်ဘွားကြီး/n စဝ်စံထွန်း/n` (မိုင်းပွန် = ဒေသအမည်/n၊ စော်ဘွားကြီး = ရာထူးဂုဏ်ပုဒ်/n သီးခြားခွဲ၊ စဝ်စံထွန်း = စဝ် name prefix မခွဲဘဲ တစ်ပုဒ်တည်း/n)
    - `သံအမတ်ကြီး/n ဦးကျော်မိုးထွန်း/n` (သံအမတ်ကြီး = ရာထူး/n ခွဲထုတ်၊ ဦးကျော်မိုးထွန်း = အမည်ရှေ့ဆက်မခွဲ/n)
    - `ဗိုလ်ချုပ်ကြီး/n ရဲဝင်းဦး/n` (ဗိုလ်ချုပ်ကြီး = စစ်ဘက်ရာထူး/n ခွဲထုတ်)
    - `ဒေါက်တာ/n စင်သီယာမောင်/n` (ဒေါက်တာ = ပညာရပ်ဘွဲ့/n ခွဲထုတ်)
    - `သမ္မတ/n ဦးဝင်းမြင့်/n` (သမ္မတ = နိုင်ငံရေးရာထူး/n ခွဲထုတ်)
    - `စစ်ခေါင်းဆောင်/n မင်းအောင်လှိုင်/n`

- **အခြား သဒ္ဒါနှင့် ပုဒ်ဖြတ် စံနှုန်းများ (Corpus Harmonization)**:
  - **လအမည်နှင့် အမျိုးအစားပြနာမ် 'လ' ခွဲခြားခြင်း (Month + Category Noun Split)**: လအမည်နှင့် အမျိုးအစားပြနာမ် 'လ' (ဥပမာ - `ဇွန်/n လ/n`၊ `မေ/n လ/n`၊ `မတ်/n လ/n`၊ `ဇူလိုင်/n လ/n`၊ `အောက်တိုဘာ/n လ/n`) အား `[Month]/n` နှင့် `လ/n` ဟူ၍ **သီးခြား ခွဲထုတ်သည် (Split as 2 separate noun tokens)**။ ဤစံနှုန်းသည် `မြို့`၊ `ရွာ`၊ `ရပ်ကွက်`၊ `လမ်း`၊ `ပြည်နယ်`၊ `နိုင်ငံ` ကဲ့သို့သော အမျိုးအစားပြနာမ်များကို အမည်မှ ခွဲထုတ်သတ်မှတ်သည့် analytic morphology စံနှုန်းနှင့် ညီညွတ်စေရန် ဖြစ်သည်။ နေ့စွဲဖော်ပြချက်တွင် လအမည် သီးသန့်သုံးသောအခါ (ဥပမာ `ဇွန် ၁၄ ရက်`၊ `၁၀ ဇွန် ၂၀၂၆`) `ဇွန်/n` အဖြစ် သီးခြားရပ်တည်သည်။
  - **အခိုင်အမာ ပေါင်းစပ်နာမ်နှင့် မွေးစားစကားလုံးများ (Lexicalized & Loan Compounds - Merged as 1 Token `/n`)**: `ပရိုမိုကုဒ်/n`, `ကူပွန်ကုဒ်/n`, `လျှော့ဈေး/n`, `လူစာရင်း/n` (squad roster / headcount), `အမည်စာရင်း/n` တို့သည် အခိုင်အမာ ပေါင်းစပ်ပြီးသော ဝေါဟာရများ ဖြစ်သဖြင့် မခွဲဘဲ တစ်ပုဒ်တည်း (`/n`) အဖြစ် သတ်မှတ်သည်။
  - **အမူအရာပြ ကြိယာဝိသေသန ခွဲထုတ်ခြင်း (Verbal Adverbial Split)**: `ဝိုင်းဝန်း/adv ခုတ်/v` (အဘိဓာန်ဝင် ပေါင်းစပ်ကြိယာ မဟုတ်ဘဲ မည်သည့်ကြိယာနှင့်မဆို လွတ်လပ်စွာ တွဲဖက်နိုင်သော အမူအရာပြ adverb + verb ဖြစ်၍ ခွဲထုတ်ရမည်)။
  - **ကြိယာနောက်လိုက် နာမ်စား "သူ" (Post-verbal Relativizer Pronoun)**: `[Verb] + သူ/pron` (ဥပမာ `ဆက်နွှယ်/v သူ/pron များ/part`၊ `သေဆုံး/v သူ/pron`)။
  - **သင်္ချာ + ရက် + ဆက် (Numeral-Measure Adverbial Construction)**: `[num] ရက်/n ဆက်/adv` (ဥပမာ `၂/num ရက်/n ဆက်/adv`)။
  - **မျိုးပြပစ္စည်း "ဦး" နှင့် နာမည်ရှေ့ဆက် "ဦး" ကွဲပြားမှု**: သင်္ချာ/ဂဏန်းနောက်မှ လူမျိုးပြပစ္စည်း `ဦး` (ဥပမာ `၁/num ဦး/part`၊ `တစ်/tn ဦး/part`၊ `၃/num ဦး/part`) သည် `part` အဖြစ် ဆက်လက်တည်ရှိပြီး၊ နာမည်ရှေ့ဆက် `ဦးမင်းအောင်လှိုင်/n` နှင့် မရောထွေးရပါ။

## 3. Built-In Protected Lexicon Lists

### 3.1 High-Frequency Over-Split Protected Words (Never Split)

`သဖြင့်`, `အထူးသဖြင့်`, `မိန်းကလေး`, `ယောက်ျားလေး`, `အစ်ကို`, `အစ်မ`, `အနား`, `ကဗျာ`, `အဖို့` / `အဘို့`, `ဆရာတော်`, `မင်းကြီး`, `နှလုံးသား`, `သုသာန်`, `မေစ္ဆရိယ`, `စေတသိက်`, `ဒေါသ`, `မေတ္တာ`, `ပြဿနာ`, `အန္တရာယ်`, `ရေကူးကန်`, `ကစားကွင်း`, `ကစားပြိုင်ပွဲကွင်း` (with size modifier `ကြီး` kept separate: `ကစားပြိုင်ပွဲကွင်း ကြီး`).

### 3.2 Legal, Administrative, Technical & Resource Loanwords (1 Token)

- **Legal & Administrative**: `ဥပဒေ`, `ပုဒ်မ`, `ပုဒ်မခွဲ`, `နည်းဥပဒေ`, `အက်ဥပဒေ`, `တည်ဆဲဥပဒေ`, `ပဋိညာဉ်`, `အာမခံ`, `သက်သေခံ`, `ဒီကရီ`, `ဇာရီ`, `သမ္မာန်စာ`, `ဝရမ်း`, `အယူခံ`, `အယူခံလွှာ`, `ကော်မတီ` / `ကော်မီတီ`, `ကော်မရှင်`, `ကောင်စီ`, `ဒီမိုကရေစီ`, `ဖက်ဒရယ်`, `ပါလီမန်`, `ပင်စင်` / `ပင်ရှင်`, `ဘတ်ဂျက်`, `ကုမ္ပဏီ`, `ကော်ပိုရေးရှင်း`, `လိုင်စင်`, `ပါမစ်`, `ဂရန်`, `ရွေးကောက်ပွဲ`, `မဲဆန္ဒနယ်မြေ`, `မဲဆန္ဒနယ်`, `မဲဆန္ဒရှင်`, `ထောင်ဒဏ်`, `ငွေဒဏ်`, `သေဒဏ်`, `ပြစ်ဒဏ်`, `တကျွန်းပို့ဒဏ်`, `တရားလို`, `တရားခံ`, `တရားပြိုင်`, `အမှုသည်`, `တရားမ`, `အချင်းဖြစ်`, `တရားရုံး`, `ခုံရုံး`, `စွဲချက်`, `စီရင်ချက်`.
- **Official Titles**: `တရားလွှတ်တော်ချုပ်`, `ဝန်ကြီးချုပ်`, `ရှေ့နေချုပ်`, `စာရင်းစစ်ချုပ်`, `ကာကွယ်ရေးဦးစီးချုပ်`, `ဦးစီးချုပ်`, `ညွှန်ကြားရေးမှူးချုပ်`, `ညွှန်ကြားရေးမှူး`, `အမြဲတမ်းအတွင်းဝန်`, `အတွင်းရေးမှူးချုပ်`, `ဥက္ကဋ္ဌ`, `တရားသူကြီးချုပ်`, `တရားသူကြီး`, `တပ်ရင်းမှူး`, `မြို့နယ်မှူး`, `ရဲမှူးချုပ်`, `ပါမောက္ခချုပ်`, `အုပ်ချုပ်ရေးမှူး`.
- **Technical, Medical & Resources**: `ကွန်ပျူတာ`, `အင်တာနက်`, `တယ်လီဖုန်း`, `ရေဒီယို`, `နည်းပညာ`, `အင်ဂျင်နီယာ`, `ဓာတုဗေဒ`, `ရူပဗေဒ`, `ဇီဝဗေဒ`, `ကီလိုမီတာ`, `စင်တီမီတာ`, `မီတာ`, `လီတာ`, `ဂရမ်`, `တန်ချိန်`, `ဒေါ်လာ`, `ပါရာစီတမော`, `ပါရာစီတမေ့`, `ပဋိဇီဝဆေးဝါး`, `ဆီးချိုရောဂါ`, `သွေးတိုးရောဂါ`, `ဂရက်နိုက်`, `ကျောက်စိမ်း`, `ပတ္တမြား`, `နီလာ`, `ပုလဲ`, `ကြေးနီ`, `ခဲမဖြူ`, `အဖြိုက်နက်`, `သံရိုင်း`, `ကျောက်မီးသွေး`, `ရေနံ`, `သဘာဝဓာတ်ငွေ့`, `ဓာတ်သတ္တု` / `ဓါတ်သတ္တု`, `သတ္တုရိုင်း`, `ထုံးကျောက်`, `သလင်းကျောက်`.
- **3- and 4-Syllable Idiomatic Compounds (1 Token)**: `အရည်အချင်း`, `အချက်အလက်`, `အစီအစဉ်`, `အတွေ့အကြုံ`, `အလိုအလျောက်`, `အဆက်အသွယ်`, `အထောက်အထား`, `အထောက်အကူ`, `အခြေအနေ`, `အခွင့်အရေး`, `အပြန်အလှန်`, `အဆောက်အအုံ`, `အပြုအမူ`, `အထင်အရှား` / `အထင်းအရှား`, `မသင့်မလျော်`, `မသန်မစွမ်း`, `မတော်တဆ`, `မတရား`, `နာမကျန်း`, `မတိုင်မီ`, `စာပေးစာယူ`, `ငွေရေးကြေးရေး`, `လတ်တလော`, `စနစ်တကျ`, `စည်းလုံးညီညွတ်ရေး`, `ငြိမ်ဝပ်ပိပြားရေး`.

## 4. Complete Boundary-Shift Trap Matrix

Always scan segmented output for false compounds created by accidental boundary shifts:

| Trap (Wrong Segmentation) | Correct Segmentation | Linguistic Reason |
| --- | --- | --- |
| `အများ ကလေး စား ထိုက်` | `အများ က လေးစား ထိုက်` | `က` is subject marker (`ppm`); `လေးစား` ("respect") is the verb, not `ကလေး` ("child") |
| `စစ်ဆေး ခြင်း ခံ ရ သူမ ဟုတ် ဘဲ` | `စစ်ဆေး ခြင်း ခံ ရ သူ မ ဟုတ် ဘဲ` | `သူ` is agentive particle (`part`); `မ` is negation (`part`), not pronoun `သူမ` ("she") |
| `သက်ဆိုင်ရာ ဥပဒေ အရသာ` | `သက်ဆိုင်ရာ ဥပဒေ အရ သာ` | `အရ` ("according to") + restrictive particle `သာ` ("only"), not noun `အရသာ` ("taste") |
| `လွှတ်တော် အစည်းအဝေးခန်း မ` | `လွှတ်တော် အစည်းအဝေး ခန်းမ` | `ခန်းမ` ("hall") is a noun, not negation `မ` |
| `ဗုဒ္ဓ ဘာသာသာ သ နာ` | `ဗုဒ္ဓ ဘာသာ သာသနာ` | `ဘာသာ/n သာသနာ/n` (Owner Component Row 7) |
| `မီးငြှိမ်း သတ် ရေး` | `မီး ငြှိမ်းသတ်ရေး` | `မီး` (object noun) + `ငြှိမ်းသတ်ရေး` (`[V]ရေး`) |
| `အမှု စီရင်ချက်ချ မှတ် သည့်` | `အမှု စီရင်ချက် ချမှတ် သည့်` | `စီရင်ချက်` (noun) + `ချမှတ်` (2-syllable verb) |
| `သတိမထား ရှိ ဘဲ` | `သတိ မ ထားရှိ ဘဲ` | `သတိ` + negation `မ` + verb `ထားရှိ` |
| `ဦး ရေအနက်` | `ဦးရေ အနက်` | `ဦးရေ` ("headcount") + `အနက်` ("among") |
| `တာဝန် ယူဆောင် ရွက်` | `တာဝန် ယူ ဆောင်ရွက်` | `တာဝန် ယူ` + `ဆောင်ရွက်` (not `ယူဆောင်` "bring") |
| `ခေတ္တရပ် စောင့် နေ စဉ်` | `ခေတ္တ ရပ် စောင့် နေ စဉ်` | `ခေတ္တ` ("briefly") + `ရပ်` ("stop"), not `ခေတ္တရပ်` |
| `ကိစ္စတစုံ တရာ` / `တစုံ တရာသော` | `ကိစ္စ တစုံတရာ` / `တစုံတရာ သော` | `တစုံတရာ` is a 1-token 4-syllable idiom |
| `တကျွန်း ပို့ ဒဏ်ခံ နေ` | `တကျွန်းပို့ဒဏ် ခံ နေ` | `တကျွန်းပို့ဒဏ်/n` is a 1-token legal penalty noun (do not alter `တကျွန်း အပို့ ခံ`) |
| `အန္တရာယ် ကင်းဖိအား ထိန်း` | `အန္တရာယ် ကင်း ဖိအား ထိန်း` | `ကင်း` predicates `အန္တရာယ်` ("hazard-free"); `ဖိအား` ("pressure") is separate |
| `ကစား ပြိုင်ပွဲ ကွင်းကြီး` | `ကစားပြိုင်ပွဲကွင်း ကြီး` | `ကစားပြိုင်ပွဲကွင်း` (compound head) + `ကြီး` (size postmodifier) |
| `သမ္မတအား` / `တဦးအား` | `သမ္မတ အား` / `တဦး အား` | `အား` is dative/accusative `ppm` (do not split lexical nouns like `ဖိအား`, `ဓာတ်အား`, `အင်အား`) |

## 5. Edit-to-Rule Corpus Generalization Protocol (Preventing Blast-Radius Regressions)

When generalizing a single human/owner segmentation or POS fix across a corpus, never run blind global regex replacements (for example, generalizing `ကရင် နီနယ် -> ကရင်နီ နယ်` into a wildcard rule `[State] + *နယ်` would corrupt 4,307 valid occurrences of `ကချင် ပြည်နယ်`, `မွန် ပြည်နယ်`, etc.):

1. **Classify Evidence Tier**:
   - **Tier A (Corpus-Internal Inconsistency)**: Both split and fused forms exist in the corpus (e.g., `ဖြစ် စေ` vs. `ဖြစ်စေ`). Requires an explicit contextual frame rule, never a blanket merge/split.
   - **Tier B (External Lexical / Gold Evidence)**: Dictionary or gold standard attests one form (`လုပ်ငန်း`), while the segmenter emitted `လုပ် ငန်း`.
   - **Tier C (Owner / Human Authority)**: Specific lexical or domain ruling (`ကရင်နီ နယ်`, `လောကပါလ`, or the 10 Owner Component Rows). Apply at **S1 exact complete-word scope**, never as an unguarded substring or suffix wildcard.
2. **Simulate Blast Radius Before Applying**:
   - Compute `fixes` (target errors corrected), `already_right` (valid instances proven untouched), and `blocks` (counterexamples where another rule conflicts).
   - Refuse any generalized rule where `blocks > 0` unless an explicit exception list is attached.
3. **Assert Non-Whitespace Character Conservation**:
   - Run `scripts/validate_nlp_corpus.py` on every modified line to verify that `re.sub(r"\s+", "", before) == re.sub(r"\s+", "", after)` and that all emitted POS tags belong to the 15-tag vocabulary.

## 6. Indefinite Multiplier Compounds (`-ပေါင်းများစွာ`) and Counting Compounds (`[Noun]ပေါင်း + Numeral`)

### 6.1 Indefinite Multipliers (`-ပေါင်းများစွာ`)
- **Linguistic Category**: Indefinite Quantifier / Multiplier Compound (မရေတွက်နိုင်သော ပမာဏပြ ပေါင်းစပ်စကားလုံး).
- **Segmentation Rule**: Must ALWAYS be unified as a single token (`1 Token`).
  - `ရာပေါင်းများစွာ`
  - `ထောင်ပေါင်းများစွာ`
  - `သန်းပေါင်းများစွာ`
  - `ဘီလီယံပေါင်းများစွာ`
  - `နှစ်ပေါင်းများစွာ`
  - `လပေါင်းများစွာ`
  - `ရက်ပေါင်းများစွာ`
  - `ဒါဇင်ပေါင်းများစွာ`
  - `ရာစုနှစ်ပေါင်းများစွာ`
- **Negative Invariants**:
  - ❌ `သန်းပေါင်း/n များစွာ/adv` (Do NOT split into 2 tokens)
  - ❌ `သန်းပေါင်း/n များ/part စွာ/part` (Do NOT shatter `များစွာ` into `များ` and `စွာ`)
  - ❌ `လူထောင်/n ပေါင်း/v များစွာ/adv` (Do NOT fuse preceding noun to counting unit or tag `ပေါင်း` as verb)
  - ❌ `လူ/n ထောင်/num ပေါင်း/part များစွာ/adv` (Do NOT shatter into 4 pieces)
- **POS Classification Decision Tree**:
  1. If modifying a verb, describing temporal duration or elapsed time -> **`adv`**  
     *(e.g., `နှစ်ပေါင်းများစွာ/adv ရှင်သန်နိုင်သည်`၊ `လပေါင်းများစွာ/adv စမ်းသပ်ထားသည်`၊ `ရာစုနှစ်ပေါင်းများစွာ/adv က သမိုင်း`)*
  2. If quantifying a following noun or preceded by an entity -> **`adj`**  
     *(e.g., `ဒါဇင်ပေါင်းများစွာ/adj နိုင်ငံများ`၊ `သန်းပေါင်းများစွာ/adj သော လူဦးရေ`၊ `လူ/n ထောင်ပေါင်းများစွာ/adj`)*
  3. If functioning as the head noun / subject taking case markers (`သည်`, `ကို`, `က`) or standalone subject -> **`n`**  
     *(e.g., `ပျားကောင်ရေ သန်းပေါင်းများစွာ/n သည်`၊ `ထောင်ပေါင်းများစွာ/n လျှပ်စစ်မီး ပြတ်တောက်`)*

### 6.2 Counting Compounds (`[Noun]ပေါင်း + Numeral`)
- **Linguistic Category**: Collective/Totalizer Compound Noun (စုပေါင်းနာမ်).
- **Segmentation Rule**: Suffix `ပေါင်း` attached to a countable noun preceding a numeric digit or number word must be unified into a compound noun `[Noun]ပေါင်း/n`.
  - `ရက်ပေါင်း/n ၁၀၀/num`
  - `နှစ်ပေါင်း/n ၁၂၅/num`
  - `လူပေါင်း/n ၃၅၀/num`
  - `အဖွဲ့အစည်းပေါင်း/n ၁၀၀/num`
  - `နိုင်ငံပေါင်း/n ၃၉/num`
  - `ပစ်မှတ်ပေါင်း/n ၈၀/num`
  - `တိုက်ပွဲပေါင်း/n ၁၀၀/num`
  - `အမှုပေါင်း/n ၅၀၀/num`
- **Negative Invariants**:
  - ❌ `အဖွဲ့အစည်း/n ပေါင်း/n ၁၀၀/num` (Do NOT split `ပေါင်း` as standalone `n`)
  - ❌ `နိုင်ငံ/n ပေါင်း/part ၃၉/num` (Do NOT split `ပေါင်း` as standalone `part`)
  - ❌ `တိုက်ပွဲ/n ပေါင်း/part ၁၀၀/num` (Do NOT split `ပေါင်း` as standalone `part`)

## 7. Multiword Foreign Entity Policy & Conjunction Exception (NER)

### 7.1 Multiword Foreign Country Exception
- **Rule**: While native Myanmar entity spans generally exclude coordinating conjunctions (`နှင့်`, `သို့မဟုတ်`) and clitic particles (`များ`, `တို့`, `သည်`), officially designated multiword foreign country proper names that contain internal conjunctions are retained as single coherent multiword entity spans.
- **Canonical Example**:
  - `ထရီနီဒက် နှင့် တိုဘာဂို` [Trinidad and Tobago] -> `ထရီနီဒက်/B-GPE နှင့်/I-GPE တိုဘာဂို/I-GPE`
- **Exemption Scope**: This exemption applies strictly to officially recognized sovereign country and territory names with fixed lexical conjunctions. It does NOT permit conjunction absorption for conjoined distinct entities (e.g., `အမေရိကန် နှင့် အီရန်` must be split across `နှင့်/O`).

## 8. Legal Citation Subsection Markers (`sb`)

- **Rule**: Alphabetic subsection markers enclosed in parentheses within legal statutory citations (e.g. `ပုဒ်မ ၅၁ ( ဂ ) ဖြင့်`) must be tagged with the dedicated subsection / sentence-beginning marker tag **`sb`**, matching standard section numbering conventions.
- **Canonical Examples**:
  - `( က )` -> `(/punc က/sb )/punc`
  - `( ခ )` -> `(/punc ခ/sb )/punc`
  - `( ဂ )` -> `(/punc ဂ/sb )/punc`
- **Negative Invariants**:
  - ❌ `ဂ/n` (Do NOT tag subsection letter as common noun)
  - ❌ `ဂ/part` (Do NOT tag subsection letter as grammatical particle)

## 9. Temporal Month Expressions (`[Month]/n လ/n`)

- **Rule**: Month proper names followed by the category noun `လ` ("month") must strictly be segmented as two separate tokens: `[Month]/n လ/n`, consistent with place and administrative category nouns (`မြို့`, `ရွာ`, `ရပ်ကွက်`, `လမ်း`, `ပြည်နယ်`, `နိုင်ငံ`).
- **Canonical Examples**:
  - `ဇွန်/n လ/n` (never `ဇွန်လ/n`)
  - `မေ/n လ/n` (never `မေလ/n`)
  - `မတ်/n လ/n` (never `မတ်လ/n`)
  - `ဇူလိုင်/n လ/n` (never `ဇူလိုင်လ/n`)

## 10. Traditional Myanmar Calendar, Lunar Months, Lunar Phases & Observance Days (မြန်မာ့ရိုးရာ ပြက္ခဒိန်၊ လအဆင့်နှင့် ဥပုသ်နေ့များ)

### 10.1 Era & Year Expressions (`ကောဇာ သက္ကရာဇ် [Year] ခုနှစ်`)
- **Rule**: Distinct cultural and temporal era markers (`ကောဇာ`, `သက္ကရာဇ်`, `သာသနာ`, `မဟာ`) are segmented as individual noun tokens (`/n`) before numeric year values:
  - `ကောဇာ/n သက္ကရာဇ်/n ၁၃၈၈/num ခုနှစ်/n` (NER: `ကောဇာ/B-DATE သက္ကရာဇ်/I-DATE ၁၃၈၈/I-DATE ခုနှစ်/I-DATE`)
  - `သာသနာ/n သက္ကရာဇ်/n ၂၅၆၈/num ခုနှစ်/n`
- **Negative Invariants**:
  - ❌ `ကောဇာသက္ကရာဇ်/n` (Do NOT merge into 1 token; preserve modifier + head noun structure)
  - ❌ `ခု/part နှစ်/n` (Do NOT split `ခုနှစ်` into 2 tokens)

### 10.2 Twelve Myanmar Lunar Months (`၁၂ လရာသီ လအမည်များ`)
- **Inventory**: `တန်ခူး`, `ကဆုန်`, `နယုန်`, `ဝါဆို`, `ဝါခေါင်`, `တော်သလင်း`, `သီတင်းကျွတ်`, `တန်ဆောင်မုန်း`, `နတ်တော်`, `ပြာသို`, `တပို့တွဲ`, `တပေါင်း`.
- **Segmentation & Tagging Policy**:
  - **Standalone Month**: `တန်ဆောင်မုန်း/n`, `နတ်တော်/n`
  - **With Category Noun `လ`**: `တန်ဆောင်မုန်း/n လ/n`, `နတ်တော်/n လ/n` (follows Section 9 `[Month]/n လ/n` split)
  - **Combined with Lunar Phase (`လဆန်း` / `လဆုတ်`)**:
    - `တန်ဆောင်မုန်းလဆန်း` -> `တန်ဆောင်မုန်း/n လဆန်း/n`
    - `တန်ဆောင်မုန်းလဆုတ်` -> `တန်ဆောင်မုန်း/n လဆုတ်/n`
    - `နတ်တော်လဆန်း` -> `နတ်တော်/n လဆန်း/n`
    - *(Note: `လ` belongs to the lunar phase noun `လဆန်း` / `လဆုတ်`, do NOT split as `တန်ဆောင်မုန်းလ ဆန်း`)*.

### 10.3 Lunar Phases (`လဆန်း၊ လဆုတ်၊ လပြည့်၊ လပြည့်ကျော်၊ လကွယ်`)
- **Rules**:
  - `လဆန်း` (Waxing moon): `လဆန်း/n` -> `တန်ဆောင်မုန်း/n လဆန်း/n ၈/num ရက်/n`
  - `လဆုတ်` (Waning moon): `လဆုတ်/n` -> `တန်ဆောင်မုန်း/n လဆုတ်/n ၁/num ရက်/n`
  - `လပြည့်` (Full moon): `လပြည့်/n` -> `တန်ဆောင်မုန်း/n လပြည့်/n နေ့/n`
  - `လပြည့်ကျော်` (Day after full moon / waning day): `လပြည့်ကျော်/n` -> `တန်ဆောင်မုန်း/n လပြည့်ကျော်/n ၁/num ရက်/n`
  - `လကွယ်` (New moon): `လကွယ်/n` -> `နတ်တော်/n လကွယ်/n နေ့/n`
- **Negative Invariants**:
  - ❌ `လပြည့်/n ကျော်/part` (Do NOT split `လပြည့်ကျော်` into 2 tokens)
  - ❌ `လ/n ဆန်း/v`, `လ/n ဆုတ်/v` (Do NOT analyze moon phases as verb phrases in temporal contexts)

### 10.4 Observance Days & Sabbath (`အဖိတ်နေ့၊ ဥပုသ်နေ့`)
- **Rules**:
  - `အဖိတ်နေ့` (Eve of Sabbath): `အဖိတ်နေ့/n` (or `အဖိတ်/n နေ့/n`) -> NER: `B-DATE`
  - `ဥပုသ်နေ့` (Sabbath Day / Uposatha): `ဥပုသ်နေ့/n` (or `ဥပုသ်/n နေ့/n`) -> NER: `B-DATE`
- **Confusable / Typo Note**:
  - User typing `ဥပုပ်` or `ဥပုပ်နေ့` is a common phonological confusable for `ဥပုသ်` / `ဥပုသ်နေ့` (Pali *Uposatha*). On corpus lines, observe `RECORD_ONLY_NOT_APPLIED`.

