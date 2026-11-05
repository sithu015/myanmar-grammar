# Lookalike keystrokes

Humans type the glyph they see. The codepoint underneath is often the other one. Run `scripts/confusable.py` before tagging. `segment` already does.

| What was typed | Code | Becomes | When |
| --- | --- | --- | --- |
| `စ` + `ျ` | U+1005 U+103B | `ဈ` U+1008 | always |
| `ဥ` + `ီ` | U+1025 U+102E | `ဦ` U+1026 | always |
| `၀` | U+1040 | `ဝ` U+101D | a letter is beside it and a digit is not |
| `ဝ` | U+101D | `၀` | a digit is beside it and a letter is not |
| `၇` / `ရ` | U+1047 / U+101B | the other | same neighbor test |
| `၈` / `ဂ` | U+1048 / U+1002 | the other | same neighbor test |
| `၄` / `၎` | U+1044 / U+104E | the other | same neighbor test. `၄င်း` therefore becomes `၎င်း` |

`ပုဒ်မ ၇` stays `၇`. A space is not a letter and not a digit, so a section number is not rewritten.

`ဩ` U+1029 and `ဪ` U+102A look the same in many fonts and are both real letters. Do not swap them. A row of `ဪ` is the interjection repeated, not a new word.
