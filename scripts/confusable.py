#!/usr/bin/env python3
"""Fix lookalike Myanmar keystrokes. Context decides digit versus letter.

  python3 scripts/confusable.py --text '၂ဝ၂၄ တွင် ၀န်ကြီး သည် ၄င်း ကို'
  python3 scripts/confusable.py --self-test

Unambiguous compositions are rewritten. A digit lookalike becomes a letter
only when a letter stands next to it and no digit does. The reverse is true
for a letter lookalike. ဩ (U+1029) and ဪ (U+102A) are both real letters and
are never rewritten. A lone digit after a space, as in ပုဒ်မ ၇, stays a digit.
"""

from __future__ import annotations

import argparse
import json
import sys

# Same glyph, wrong code. The first of each pair is what the key often emits.
COMPOSE = (
    ("\u1005\u103b", "\u1008", "JHA", "စ plus medial ya is the letter ဈ"),
    ("\u1025\u102e", "\u1026", "UU", "ဥ plus ီ is the letter ဦ"),
    ("ဥပုပ်နေ့", "ဥပုသ်နေ့", "U_PO_NE", "ဥပုသ် (သ-သတ်) is the correct spelling for sabbath"),
    ("ဥပုပ်", "ဥပုသ်", "U_PO", "ဥပုသ် (သ-သတ်) is the correct spelling"),
)

# Digit form, letter form.
CONTEXT = (
    ("\u1040", "\u101d", "WA_ZERO"),
    ("\u1047", "\u101b", "RA_SEVEN"),
    ("\u1048", "\u1002", "GA_EIGHT"),
    ("\u1044", "\u104e", "IT_FOUR"),
)
DIGIT_OF = {letter: digit for digit, letter, _rule in CONTEXT}
LETTER_OF = {digit: letter for digit, letter, _rule in CONTEXT}
RULE_OF = {digit: rule for digit, _letter, rule in CONTEXT}
RULE_OF.update({letter: rule for _digit, letter, rule in CONTEXT})


def _is_digit(ch: str) -> bool:
    return bool(ch) and ("၀" <= ch <= "၉" or ch.isascii() and ch.isdigit())


def _is_letter(ch: str) -> bool:
    if not ch or _is_digit(ch):
        return False
    code = ord(ch)
    return (0x1000 <= code <= 0x102A) or (0x103F <= code <= 0x104E) or (0x1050 <= code <= 0x109F)


def correct(text: str) -> tuple[str, list[dict[str, object]]]:
    """Return the corrected text and a list of applied edits."""
    if not text:
        return text, []
    edits: list[dict[str, object]] = []
    out = text
    for src, dst, rule, note in COMPOSE:
        start = 0
        while True:
            at = out.find(src, start)
            if at < 0:
                break
            edits.append({
                "i": at, "from": src, "to": dst, "rule": rule,
                "status": "applied", "note": note,
            })
            out = out[:at] + dst + out[at + len(src):]
            start = at + len(dst)

    chars = list(out)
    for i, ch in enumerate(chars):
        if ch not in DIGIT_OF and ch not in LETTER_OF:
            continue
        left = chars[i - 1] if i else ""
        right = chars[i + 1] if i + 1 < len(chars) else ""
        digit_side = _is_digit(left) or _is_digit(right)
        letter_side = _is_letter(left) or _is_letter(right)
        if ch in LETTER_OF and letter_side and not digit_side:
            chars[i] = LETTER_OF[ch]
        elif ch in DIGIT_OF and digit_side and not letter_side:
            chars[i] = DIGIT_OF[ch]
        else:
            continue
        edits.append({
            "i": i, "from": ch, "to": chars[i], "rule": RULE_OF[ch],
            "status": "applied", "note": "neighbor is a letter" if chars[i] in DIGIT_OF else "neighbor is a digit",
        })
    return "".join(chars), edits


def self_test() -> None:
    cases = {
        "စျေး": "ဈေး",
        "ဦ": "ဦ",
        "၂ဝ၂၄": "၂၀၂၄",
        "၀န်ကြီး": "ဝန်ကြီး",
        "၄င်း": "၎င်း",
        "၁ရ": "၁၇",
        "ဂ၀၀": "၈၀၀",
        "ပုဒ်မ ၇": "ပုဒ်မ ၇",
        "ဝန်ကြီး": "ဝန်ကြီး",
        "ဈေး": "ဈေး",
        "၎င်း": "၎င်း",
        "၁၈": "၁၈",
        "ဩ": "ဩ",
        "ဪဪ": "ဪဪ",
        "ရက်": "ရက်",
    }
    for src, expected in cases.items():
        got, _edits = correct(src)
        if got != expected:
            raise AssertionError(f"{src!r} -> {got!r}, want {expected!r}")
    _got, edits = correct("၀န်")
    if not edits or edits[0]["status"] != "applied":
        raise AssertionError(edits)
    print("SELF-TEST PASSED: lookalike compositions and digit/letter context.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Correct Myanmar lookalike characters.")
    parser.add_argument("--text", help="One line to correct")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.text:
        parser.error("pass --text or --self-test")
    fixed, edits = correct(args.text)
    json.dump({"text": fixed, "edits": edits}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
