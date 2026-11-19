# Lookalike keystrokes

# Lookalike keystrokes & Confusable Disambiguation

Humans type the glyph they see. The codepoint underneath is often the other one.

## Architectural Standard: Codepoint Conservation vs. Opt-In Normalization

- **Default Behavior (Codepoint Conservation)**: By default, pipeline tools (`scripts/nlp_cli.py`, `scripts/word_segmenter.py`, `scripts/corpus_chunk_and_remediate.py`) **strictly preserve original source codepoints and character offsets** (`re.sub(r"\s+", "", before) == re.sub(r"\s+", "", after)`). Segmentation and POS tagging never silently rewrite characters or substitute codepoints without explicit user consent.
- **Opt-In Normalization (`--normalize-confusables`)**: To remediate keystroke mistakes before segmentation, users must pass the opt-in flag `--normalize-confusables` (e.g., `python3 scripts/nlp_cli.py -w "စာသား" --normalize-confusables`). In Python code: `WordSegmenter(normalize_confusables=True)`.
- **Character-Conservation Rollback Guard**: In corpus remediation (`corpus_chunk_and_remediate.py`), any rule or transform that causes non-whitespace codepoint distortion without an explicit remediation ledger triggers an automated rollback to protect gold data fidelity.

## Visual Lookalike Mapping Table

| What was typed | Code | Becomes | When |
| --- | --- | --- | --- |
| `စ` + `ျ` | U+1005 U+103B | `ဈ` U+1008 | always (ligature decomposition fix) |
| `ဥ` + `ီ` | U+1025 U+102E | `ဦ` U+1026 | always (independent vowel combination) |
| `၀` | U+1040 (Digit Zero) | `ဝ` U+101D (Letter Wa) | a letter is beside it and a digit is not |
| `ဝ` | U+101D (Letter Wa) | `၀` U+1040 (Digit Zero) | a digit is beside it and a letter is not |
| `၇` / `ရ` | U+1047 / U+101B | the other | same neighbor test (Digit Seven vs Letter Ra) |
| `၈` / `ဂ` | U+1048 / U+1002 | the other | same neighbor test (Digit Eight vs Letter Ga) |
| `၄` / `၎` | U+1044 / U+104E | the other | same neighbor test. `၄င်း` therefore becomes `၎င်း` |

`ပုဒ်မ ၇` stays `၇`. A space is not a letter and not a digit, so a section number is not rewritten.

`ဩ` U+1029 and `ဪ` U+102A look the same in many fonts and are both real letters. Do not swap them. A row of `ဪ` is the interjection repeated, not a new word.

## High-Frequency Homograph Disambiguation: `သင့်`

`သင့်` is a critical three-way homograph in Burmese text that must be disambiguated by syntax:

1. **Root / Lexical Verb (`v` -> UD `VERB`)**:
   - Meaning: "to befit, be appropriate" (e.g., `မ/part သင့်/v`, `မသင့်မလျော်`, `သင့်လျော်/v`) or "to touch, be struck by" (`ကျည်သင့်/v`).
   - Trigger: Preceding negation `မ/part`, following `လျော်`, or functioning as clause predicate.
2. **Post-Verbal Auxiliary / Modal Particle (`part` / `v` -> UD `AUX` / `VERB`)**:
   - Meaning: debitive obligation ("should, ought to", e.g., `လိုက်နာ/v သင့်/part`).
   - Profile behavior: Tagged `part` (`part:aux` -> `AUX`) in `general`, `legal70k`, and `legacy_mypos_alt`; tagged `v` (UD `VERB`) in `news_unified` per News SOP v3.2.
3. **Second-Person Pronoun (`pron` -> UD `PRON`)**:
   - Meaning: formal / literary 2sg "you / your" (e.g., `သင့်/pron ၏/ppm အကြံ/n`, `သင့်/pron စိတ်/n`, `သင့်ကို/pron`).
   - Trigger: Occurring in nominal/argument position before nouns, postpositions, or case markers.
