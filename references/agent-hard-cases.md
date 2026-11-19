# Agent hard cases

Taken from OV Brain Memory adjudication, not from a new theory. Dates are the memory dates. If a row here conflicts with an older lexicon line, this file wins.

## Do not glue

| Glued form agents produced | Correct | Why |
| --- | --- | --- |
| `တည်ဆဲဥပဒေ` | `တည်ဆဲ ဥပဒေ` | 2026-10-19. Head plus modifier, not one dictionary headword |
| `စက်မှုဒီဇိုင်း` | `စက်မှု ဒီဇိုင်း` | same arbitration |
| `သဘောထားမှတ်ချက်` | `သဘောထား မှတ်ချက်` | same arbitration |
| `ပေါ်ပေါက်လာ` | `ပေါ်ပေါက် လာ` | directional auxiliary stays separate |
| `ဦးစီးဌာန` | `ဦးစီး ဌာန` | the office is two tokens |
| `ရန်အခါ` | `ရန် အခါ` | purpose particle boundary |
| `ဒဏ်ရာရ` | `ဒဏ်ရာ ရ` | `ရ` is the verb |
| `အသုံးပြုသူ` | `အသုံးပြု သူ` | agentive `သူ` is its own token. Gold was split 765 to 0 |
| `နေထိုင်သူ` | `နေထိုင် သူ` | same, 1008 to 0 |
| `နေထိုင်အသုံးပြုသူ` | `နေထိုင် အသုံးပြု သူ` | do not stop after a partial glue |
| `ရွှေဘုန်းတော်` | `ရွှေ ဘုန်းတော်` | `ရွှေ` is an attributive epithet modifying the royal noun `ဘုန်းတော်` |
| `သတ္တမအကြိမ်` | `သတ္တမ အကြိမ်` | ordinal adjective `သတ္တမ/adj` + frequency noun `အကြိမ်/n` (must split, parallel to `ပထမ အကြိမ်`) |
| `မြန်မာမင်း` | `မြန်မာ မင်း` | proper GPE/NORP noun `မြန်မာ/n` + king noun `မင်း/n` (matches `မြန်မာ နိုင်ငံတော်` & `မြန်မာ မင်းသား`) |
| `တနင်္လာဂြိုဟ်သက်` | `တနင်္လာ ဂြိုဟ်သက်` | planet/day noun `တနင်္လာ/n` + astrological head noun `ဂြိုဟ်သက်/n` |
| `အရှင့်သားတော်` / `အရှင့်သား တော်` | `အရှင့် သားတော်` | possessive noun `အရှင့်/n` ("His Majesty's") + fused royal kinship `သားတော်/n` (matches `အရှင့် ဘိုးတော်`) |
| `တပါးသူဌေး` | `တပါး သူဌေး` | alterity modifier `တပါး/adj` ("another") + `သူဌေး/n` (never split `တ ပါး` and never substring-match `တပါးသူ`) |
| `ထီးဆောင်းနန်း` | `ထီးဆောင်း နန်း` | sovereign-rule modifier `ထီးဆောင်း/adj` + noun `နန်း/n` (never tag `ထီးဆောင်း/v`) |
| `လျင်သော` | `လျင် သော` | verb `လျင်/v` + relativizer particle `သော/part` |
| `ရှုသော်` | `ရှု သော်` | verb `ရှု/v` + subordinating conjunction `သော်/conj` (`legal70k`/`news_unified` Base-15 ၌ `part`; `myPOS-HD` ၌ အမြဲ `conj:sub` -> `SCONJ`) |
| `ဆောင်ပါသော်` | `ဆောင် ပါ သော်` | verb `ဆောင်/v` + polite particle `ပါ/part` + conjunction `သော်/conj` (`legal70k`/`news_unified` Base-15 ၌ `part`; `myPOS-HD` ၌ အမြဲ `conj:sub` -> `SCONJ`) |
| `ဟူသောအက္ခရာ` | `ဟူသော အက္ခရာ` | relativizer particle `ဟူသော/part` + noun `အက္ခရာ/n` |
| `နိမိတ်ဩဘာ` | `နိမိတ် ဩဘာ` | synonymous rhetorical pair: noun `နိမိတ်/n` + noun `ဩဘာ/n` |
| `မြှောက်စားချီးမြှင့်` | `မြှောက်စား ချီးမြှင့်` | synonymous verb pair: verb `မြှောက်စား/v` + verb `ချီးမြှင့်/v` |
| `ချီးမြှင့်မြှောက်စား` | `ချီးမြှင့် မြှောက်စား` | synonymous verb pair: verb `ချီးမြှင့်/v` + verb `မြှောက်စား/v` |
| `ထိခိုက်နာကျင်` | `ထိခိုက် နာကျင်` | synonymous verb pair: verb `ထိခိုက်/v` + verb `နာကျင်/v` |
| `တစ်ပါးအခြား` | `တစ်ပါး အခြား` | synonymous indefinite pair: adjective `တစ်ပါး/adj` + adjective `အခြား/adj` |
| `သကျနန်းရိုးသတိုး` | `သကျ နန်းရိုး သတိုး` | dynastic glossing: noun `သကျ/n` + noun `နန်းရိုး/n` + noun `သတိုး/n` |
| `ဇမ္ဗူဒီပါလက်ယာတောင်ကျွန်း` | `ဇမ္ဗူဒီပါ လက်ယာ တောင်ကျွန်း` | three-fold bilingual glossing: noun `ဇမ္ဗူဒီပါ/n` + modifier `လက်ယာ/adj` + noun `တောင်ကျွန်း/n` |
| `မဟာဒါန်တိုက်ဝန်နေမျိုးဇေယကျော်ထင်` | `မဟာဒါန်တိုက်ဝန် နေမျိုးဇေယကျော်ထင်` | office rank `မဟာဒါန်တိုက်ဝန်/n` ("Minister of Mahādān Taik") + conferred royal title `နေမျိုးဇေယကျော်ထင်/n` |
| `သမက်တော်သြယာဓမ္မရာဇာ` | `သမက်တော် သြယာ ဓမ္မရာဇာ` | fused kinship `သမက်တော်/n` + Thai rank `သြယာ/n` (*Okya*) + name/title `ဓမ္မရာဇာ/n` (preserve archaic `သြ` codepoints) |
| `ဗုဒ္ဓကန့်လန့်ကာ` | `ဗုဒ္ဓ ကန့်လန့်ကာ` | book/essay title: proper noun `ဗုဒ္ဓ/n` + curtain noun `ကန့်လန့်ကာ/n` (parallel to `ဗုဒ္ဓ ဘာသာ`) |

`ကျောင်းသား` is not this pattern. Do not split every word that ends in `သူ`.

## Do not split

These were confirmed dictionary headwords on 2026-10-19 or fixed forms on 2026-11-02/2026-11-18: `ခရီးသွား`, `သွားလာ`, `တိုက်နယ်`, `ဝင်ငွေ`, `ထွက်ချက်`, `ယစ်မျိုးခွန်`, `အကျိုးငွေ`, `စီရင်ဆုံးဖြတ်`, `ဦးစီးဌာနမှူး`, `တိုင်းဒေသကြီး`, `နှင့်တကွ`, `အပါအဝင်`, `နေ့စဉ်မှတ်စု`, `နွေဦးတော်လှန်ရေး`, `ဓာတ်ရကိန်း`, `ဘွဲ့မည်`, `ထီးဆောင်းမင်း` *(MLC dictionary headword; or `ထီးဆောင်း/adj မင်း/n` analytically)*, `ထီးနန်းရှင်`, `မင်းဆရာ`, `သူဆင်းရဲ`, `သကျ`, `နန်းရိုး`, `ရှာပုံတော်`, `ဇမ္ဗူဒီပါ`, `ယုံယုံကြည်ကြည်`, `တပါးသူ`, `တစ်ပါးသူ`, `သူတပါး`, `သူတစ်ပါး`, `တပါး` / `တစ်ပါး` *(when meaning "other / except", e.g., `တပါး သူဌေး`, `အခြား တစ်ပါး သော`, `မှ တစ်ပါး` — NEVER confuse with literal count `တဦး`, `တခု`, `တကောင်`)*, `သားတော်`, `မြေးတော်`, `ဘိုးတော်`, `ဘီတော်`, `သမက်တော်`, `သားသမက်တော်`, `အနွယ်တော်`, `အဆက်အနွယ်တော်`, `အမည်တော်`, `နံတော်`, `စည်းစိမ်တော်`, `သက်တော်`, `မြို့တော်`, `နိုင်ငံတော်`, `မဟာဒါန်တိုက်ဝန်`, `နေမျိုးသီရိသိင်္ခသူ`, `နေမျိုးဇေယကျော်ထင်`, `နေမျိုးကျော်ထင်`, `ဇေယသင်္ခယာ`, `ဘယကျော်သူ`, `ပိဿလောက်`, `သုဝဏ္ဏလောက်`, `သဝန်ခလောက်`, `သောင်ကျည်`, `ဆောင်ခွေ`, `လဝိုက်`, `လင်ပန်း`, `ကြေးမြင်`, `ငန်းစွန်`, `ဦးခင်မောင်ကြီး`, `ခင်မောင်ကြီး`, `ဝါးနှီး`, `တမာရွက်`, `နန်းသိမ်းပွဲ`, `ကန့်လန့်` (`adv`, never `ကန့်/n လန့်/v`), `ကန့်လန့်ကာ` (`n`, never `adv`).

`ဦးစီးဌာနမှူး` stays one token even though `ဦးစီးဌာန` splits. `ခရီးသွား` stays one token even though `ပေါ်ပေါက် လာ` splits. Royal honorific `-တော်` stays fused to kinship/attributes (`သားတော်`, `ဘိုးတော်`, `ဘီတော်`, `အနွယ်တော်`, `အမည်တော်`, `စည်းစိမ်တော်`, `သက်တော်`), while possessive `အရှင့်` (`အရှင့်/n သားတော်/n`) and pre-nominal epithet `ရွှေ` (`ရွှေ/adj ဘုန်းတော်/n`) stay separate. Astrological formula `ဓာတ်ရကိန်း` stays fused as one compound noun `/n`, while `[Day/Planet] ဂြိုဟ်သက်` splits (`တနင်္လာ/n ဂြိုဟ်သက်/n`). Ordinals (`သတ္တမ/adj အကြိမ်/n`) and proper modifiers (`မြန်မာ/n မင်း/n`) always split. Broken Pali stem `သကျ` (Śākya) must be rejoined.

## Tags agents got wrong

| Surface | Tag | Frame |
| --- | --- | --- |
| `( ဂ )` and any single subsection letter in parentheses | `sb` | same rule as `( က )`. A name or a Latin word in parentheses is not `sb` |
| `စီစဉ် နေ` | `နေ/part` | aspect after the verb. `ပြီး` is still review: it was `conj` on one news line |
| `ဒဏ်ရာ ရ` | `ရ/v` | not an auxiliary |
| `အပါအဝင်` | `ppm` | one token |
| `နှင့်တကွ` | `conj` | one token. Corpus 908 merged, 0 split |
| `နေ့စဉ်` | `adj` | the column name `နေ့စဉ်မှတ်စု` is a separate noun |
| `နောက်ဆုံး` | `adj` | |
| `မိုး ဇလ` | `abb abb` | weather-office pair. `မိုး` alone can be the noun rain |
| `၇ နာရီ` | `နာရီ/n` | time noun, not a classifier particle |
| `သော်` after verb | `conj` / `part` | subordinating temporal/conditional conjunction (`general`/`legacy_mypos_alt`/Shan Yoma ၌ `conj`, `legal70k`/`news_unified` ၌ `part`; `myPOS-HD v4.1` ၌ `conj:sub` -> `SCONJ`) |
| `သော` after verb | `part` | attributive relativizer particle (`လျင်/v သော/part`) |
| `ဟူသော` before noun | `part` | relativizer particle (`ဟူသော/part အက္ခရာ/n`) |
| `ရွှေ` before `ဘုန်းတော်` | `adj` | attributive epithet modifier (`ရွှေ/adj ဘုန်းတော်/n`) |
| `ထီးဆောင်း` before `နန်း` / `မင်း` | `adj` | sovereign-rule modifier (`ထီးဆောင်း/adj နန်း/n`; never `ထီးဆောင်း/v`) |
| `တပါး` / `တစ်ပါး` meaning "other" | `adj` / `ppm` | `တပါး/adj သူဌေး/n`, `အခြား/adj တစ်ပါး/adj သော/part`, `မှ/ppm တစ်ပါး/ppm` (NOT `တ/tn ပါး/part`!) |
| `တပါးသူ` / `တစ်ပါးသူ` | `n` | fused lexicalized noun ("another person / others"; never split `တ ပါး သူ`) |
| `သူတပါး` / `သူတစ်ပါး` | `n` | fused MLC headword ("another person / others", `သူတပါး/n ထက်/ppm`; never split `သူ/pron တ/tn ပါး/part`) |
| `ဓာတ်ရကိန်း` | `n` | fused astrological configuration compound noun |
| `သတ္တမ` | `adj` | ordinal number adjective (`သတ္တမ/adj အကြိမ်/n`) |
| `ကြား` | review | `ppm` "between" or `v` "hear" |
| `ကြောင့်` `ဖို့` | `ppm` | news closed class |
| `တဲ့` `တယ်` `မယ်` `ပြီ` | `part` | news closed class |

## NER

Do not mark these as names. They are ordinary words with a plural or a verb: `ရန်သူများ`, `မြင့်တက်ခဲ့သည်`, `နိုင်ငံများ`, `မြို့ကြီးများ`.

One exception keeps the postposition inside the name: `ထရီနီဒက် နှင့် တိုဘာဂို` is `B-GPE I-GPE I-GPE`. Do not strip that `နှင့်`. Every other postposition stays outside the entity.

## POS closes that were wrong

These fired as `closed` and have been narrowed. Do not put the wide rule back.

| Wrong close | Correct now |
| --- | --- |
| any `သည်` before `မှာ`/`ကို` is `part` | `part` only after a verb, or before `ဟု`. `တရားလို သည် မှာ` stays `ppm` |
| any medial `သည်` after a verb is `ppm` | after a listed verb it is `part` |
| every `မ` before a word is `part` | `part` only before a verb or quality word. `မ သီရိ` stays review |
| every `ကို` is `ppm` | `ppm` only after a word. Sentence-initial `ကို` stays review |
| every `သင့်` is `part` | `သွား သင့်` is `part` (`general`, `legal70k`, `legacy_mypos_alt`) or `v` (`news_unified` / News SOP v3.2); `မ သင့်` is `v`; literary 2sg pronoun ("you/your", `သင့် စာအုပ်`) is `pron` |
| every `အား` is `ppm` | `အား ရှိ` / `အား စိုက်` is `n` |
| every `နောက်ဆုံး` is `adj` | review: `adj` before a noun, `adv` before a verb |
| `ရ` left open after a verb | `ဆောင်ရွက် ရ` is `part`; `ဒဏ်ရာ ရ` and `မ ရ` stay `v` |
| `နှစ် ရာ` left `နှစ်` open | `tn`. `နှစ် ကြာ` is still the noun `n` |

Still not closed, on purpose: `နှင့်` between two nouns, `က` as subject versus "if", `ကြား`, `ကား`, `စစ်`, `ဝါ`, and `များ သည်` when "many" is the predicate rather than the plural. An unknown verb before `သည်` can still be tagged `ppm`. Add that verb to the list in `scripts/decide.py` instead of widening the rule.

## Compounds are not clitic chains

`ကော်မရှင်သည်၎င်း` and `ကျင့်ထုံးကိုသော်၎င်း` are a noun plus `သည်/ကို သော် ၎င်း`, not one literary compound. Peel that chain. `မက္ကဆီကို`, `အမေရိက`, `သီရိလင်္ကာ`, `မင်းကိုနိုင်`, and `အမှုသည်` contain a function-looking syllable and still stay one token.

## What this does not do

Pali repairs such as `အနုညာ + တစီရင်` change characters. Do not apply them. A very long unsegmented string is a raw-text error, not a reason to invent a new compound.
