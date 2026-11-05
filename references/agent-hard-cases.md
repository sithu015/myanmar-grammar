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

`ကျောင်းသား` is not this pattern. Do not split every word that ends in `သူ`.

## Do not split

These were confirmed dictionary headwords on 2026-10-19 or fixed forms on 2026-11-02: `ခရီးသွား`, `သွားလာ`, `တိုက်နယ်`, `ဝင်ငွေ`, `ထွက်ချက်`, `ယစ်မျိုးခွန်`, `အကျိုးငွေ`, `စီရင်ဆုံးဖြတ်`, `ဦးစီးဌာနမှူး`, `တိုင်းဒေသကြီး`, `နှင့်တကွ`, `အပါအဝင်`, `နေ့စဉ်မှတ်စု`, `နွေဦးတော်လှန်ရေး`.

`ဦးစီးဌာနမှူး` stays one token even though `ဦးစီးဌာန` splits. `ခရီးသွား` stays one token even though `ပေါ်ပေါက် လာ` splits.

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
| every `သင့်` is `part` | `သွား သင့်` is `part`; `မ သင့်` is `v` |
| every `အား` is `ppm` | `အား ရှိ` / `အား စိုက်` is `n` |
| every `နောက်ဆုံး` is `adj` | review: `adj` before a noun, `adv` before a verb |
| `ရ` left open after a verb | `ဆောင်ရွက် ရ` is `part`; `ဒဏ်ရာ ရ` and `မ ရ` stay `v` |
| `နှစ် ရာ` left `နှစ်` open | `tn`. `နှစ် ကြာ` is still the noun `n` |

Still not closed, on purpose: `နှင့်` between two nouns, `က` as subject versus "if", `ကြား`, `ကား`, `စစ်`, `ဝါ`, and `များ သည်` when "many" is the predicate rather than the plural. An unknown verb before `သည်` can still be tagged `ppm`. Add that verb to the list in `scripts/decide.py` instead of widening the rule.

## Compounds are not clitic chains

`ကော်မရှင်သည်၎င်း` and `ကျင့်ထုံးကိုသော်၎င်း` are a noun plus `သည်/ကို သော် ၎င်း`, not one literary compound. Peel that chain. `မက္ကဆီကို`, `အမေရိက`, `သီရိလင်္ကာ`, `မင်းကိုနိုင်`, and `အမှုသည်` contain a function-looking syllable and still stay one token.

## What this does not do

Pali repairs such as `အနုညာ + တစီရင်` change characters. Do not apply them. A very long unsegmented string is a raw-text error, not a reason to invent a new compound.
