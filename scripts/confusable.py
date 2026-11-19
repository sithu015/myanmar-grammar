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
    ("\u103a\u1037", "\u1037\u103a", "DOT_ASAT", "canonical Unicode order is dot-below (U+1037) before asat (U+103A)"),
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


def _is_myanmar_digit(ch: str) -> bool:
    return bool(ch) and "၀" <= ch <= "၉"


def _is_digit(ch: str) -> bool:
    return bool(ch) and ("၀" <= ch <= "၉" or (ch.isascii() and ch.isdigit()))


def _is_letter(ch: str) -> bool:
    if not ch or _is_digit(ch):
        return False
    code = ord(ch)
    return (
        (0x1000 <= code <= 0x102A)
        or code == 0x103F
        or (0x104C <= code <= 0x104F)
        or (0x1050 <= code <= 0x108F)
        or (0x109A <= code <= 0x109D)
    )


def _is_combining_letter_anchor(ch: str) -> bool:
    if not ch:
        return False
    code = ord(ch)
    return (0x102B <= code <= 0x103E) or (0x1056 <= code <= 0x1059)


def correct_with_spans(text: str) -> tuple[str, list[dict[str, object]], list[tuple[int, int]]]:
    """Return (corrected_text, edits, span_map) mapping each corrected char to original (start, end)."""
    if not text:
        return text, [], []
    edits: list[dict[str, object]] = []
    out = text
    spans: list[tuple[int, int]] = [(i, i + 1) for i in range(len(text))]

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
            src_len = len(src)
            dst_len = len(dst)
            if dst_len == src_len:
                new_spans = spans[at : at + src_len]
            else:
                orig_s = spans[at][0]
                orig_e = spans[at + src_len - 1][1]
                new_spans = [(orig_s, orig_e)] * dst_len
            spans = spans[:at] + new_spans + spans[at + src_len :]
            out = out[:at] + dst + out[at + src_len :]
            start = at + dst_len

    chars = list(out)
    n = len(chars)
    changed = True
    while changed:
        changed = False
        for i, ch in enumerate(chars):
            if ch not in DIGIT_OF and ch not in LETTER_OF:
                continue
            left = chars[i - 1] if i else ""
            right = chars[i + 1] if i + 1 < n else ""
            digit_left = _is_digit(left) or (
                left in (".", ",") and i >= 2 and _is_myanmar_digit(chars[i - 2])
            )
            digit_right = _is_digit(right) or (
                right in (".", ",") and i + 2 < n and _is_myanmar_digit(chars[i + 2])
            )
            digit_side = digit_left or digit_right

            if ch in DIGIT_OF:
                k_left = i - 1
                while k_left >= 0 and chars[k_left] in DIGIT_OF:
                    k_left -= 1
                k_right = i + 1
                while k_right < n and chars[k_right] in DIGIT_OF:
                    k_right += 1
                unambig_left = k_left >= 0 and _is_letter(chars[k_left])
                unambig_right = k_right < n and (
                    _is_letter(chars[k_right]) or _is_combining_letter_anchor(chars[k_right])
                )
                letter_side = unambig_left or unambig_right
            else:
                letter_side = (
                    _is_letter(left)
                    or _is_letter(right)
                    or _is_combining_letter_anchor(right)
                )

            if ch in LETTER_OF and letter_side and not digit_side:
                new_ch = LETTER_OF[ch]
            elif ch in DIGIT_OF and digit_side and not letter_side:
                new_ch = DIGIT_OF[ch]
            else:
                continue

            if new_ch != ch:
                chars[i] = new_ch
                changed = True
                edits.append({
                    "i": i, "from": ch, "to": new_ch, "rule": RULE_OF[ch],
                    "status": "applied",
                    "note": "neighbor is a letter" if new_ch in DIGIT_OF else "neighbor is a digit",
                })
    return "".join(chars), edits, spans


def correct(text: str) -> tuple[str, list[dict[str, object]]]:
    """Return the corrected text and a list of applied edits."""
    fixed, edits, _spans = correct_with_spans(text)
    return fixed, edits


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
        "ပုဒ်မ ၇။": "ပုဒ်မ ၇။",
        "ပုဒ်မ ၈၊": "ပုဒ်မ ၈၊",
        "အခန်း ၀။": "အခန်း ၀။",
        "၁ဝ။": "၁၀။",
        "၇။": "၇။",
        "၈၊": "၈၊",
        "၀။": "၀။",
        "။၇": "။၇",
        "၊၈": "၊၈",
        "။၀": "။၀",
        "႑ဝ": "႑ဝ",
        "႑၇": "႑၇",
        "႞ဝ": "႞ဝ",
        "႞၇": "႞၇",
        "႞၀": "႞၀",
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
