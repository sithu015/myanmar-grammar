# Decide first

Tag and segment from the tables. Do not open the long guides until a row says `review`.

```bash
python3 scripts/decide.py --tokens 'တရားလို သည် လျှောက်ထား သည် ။'
python3 scripts/decide.py --text 'တရားလိုသည်လျှောက်ထားသည်။'
python3 scripts/decide.py --word ကား
python3 scripts/nlp_cli.py -c 'တရားလိုသည်လျှောက်ထားသည်။'
```

## How to read the JSON

| status | What you do |
| --- | --- |
| `closed` | Use `tag`. It is a myPOS 15 tag. Do not reopen the chapter. |
| `open` | Content word. Leave it. Do not invent `ppm`, `part`, or a UD tag. |
| `review` | The `readings` array is the whole legal set. Pick the one whose `note` matches this frame. If none matches, stop and mark review. |
| `catalog` | `--word` lookup. Same readings, no sentence frame yet. |

`resources/decisions/homographs.tsv` is the rule table. First matching `when` wins. A `reading` row never fires by itself. `resources/lexicon/owner_keep_whole.txt` is the one-token vocabulary the segmenter rejoins. Do not add `အရသာ`, `သူမ`, `ကလေး`, `တရားမ`, or `ယူဆောင်` to that file: those concatenations are boundary traps.

Owner fixed forms (`တပြိုင်နက်/adv`, `တကျွန်းပို့ဒဏ်/n`, and the other nine) are `always` rows. `သည်` after `ဆို` is `part`, clause-final `သည်` is `part`, medial `သည်` is `ppm`. `DET`, `AUX`, `SCONJ`, and `PROPN` are not output tags.

A postposition or particle with no word on its left stays `review`. Read `left` and `right` in the JSON before you name its function. `နှင့်` is `part` after `မ` plus a verb, `part` for prior action, `ppm` before a verb, and `conj` between two other words. `၏` after a verb at the end of the clause is realis `part`, not the genitive.

A token ending in `သည်၎င်း`, `ကို၎င်း`, or `ကိုသော်၎င်း` is not a compound. Peel that chain. `မက္ကဆီကို`, `အမေရိက`, `သီရိလင်္ကာ`, `မင်းကိုနိုင်`, and `အမှုသည်` stay one token. Head plus modifier still splits. The adjudicated list is in [Agent hard cases](agent-hard-cases.md).
