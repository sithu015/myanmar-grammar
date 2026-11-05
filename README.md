# myanmar-grammar

မြန်မာသဒ္ဒါနှင့် NLP skill။ MLC 2013 ဝါစင်္ဂ၊ myPOS 15-tag၊ Legal70k ပုဒ်ဖြတ်စံနှင့် ဆုံးဖြတ်ချက်ကိရိယာများ ပါသည်။

စတင်ဖတ်ရန် [SKILL.md](SKILL.md)။ Tag မဆုံးဖြတ်မီ `scripts/decide.py` ကို အရင်သုံးပါ။ Corpus ဖိုင်ထဲတွင် myPOS tag ၁၅ လုံးသာ ထားပါ။ `DET` နှင့် `PROPN` မထည့်ပါနှင့်။

```bash
python3 scripts/decide.py --self-test
python3 scripts/nominal.py --self-test
python3 scripts/test_nlp_tools.py -q
```
