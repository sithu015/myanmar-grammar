#!/usr/bin/env python3
"""
tools/syllable_breaker.py — Myanmar Syllable Segmentation Engine.

Based on ThanLwinSoft / myOpenware TTKeyboard MyanmarParser pair-table rules.
Enforces orthographic integrity and valid character cluster boundaries.
"""

import sys
import os

# Import official parser
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.dirname(current_dir))
try:
    from myparser import MyParser
except ImportError:
    try:
        from .myparser import MyParser
    except ImportError:
        from ..myparser import MyParser


class SyllableBreaker:
    def __init__(self):
        self._parser = MyParser()

    def segment(self, text: str) -> list[str]:
        """Break Myanmar text into a list of syllables."""
        if not text:
            return []
        
        syllables = []
        length = len(text)
        offset = 0
        
        while offset < length:
            break_type, next_offset = self._parser.get_next_syllable(text, length, offset)
            if next_offset <= offset:
                # Fallback to advance by 1 char to avoid infinite loop on unexpected input
                next_offset = offset + 1
            syl = text[offset:next_offset]
            if syl:
                syllables.append(syl)
            offset = next_offset
            if break_type == self._parser.MY_PAIR_EOL:
                break
                
        return syllables

    def segment_with_delimiter(self, text: str, delimiter: str = " ") -> str:
        """Return text segmented with delimiter between syllables."""
        return delimiter.join(self.segment(text))

    def get_spans(self, text: str) -> list[tuple[int, int, str]]:
        """Return list of (start_idx, end_idx, syllable) tuples."""
        spans = []
        length = len(text)
        offset = 0
        
        while offset < length:
            break_type, next_offset = self._parser.get_next_syllable(text, length, offset)
            if next_offset <= offset:
                next_offset = offset + 1
            syl = text[offset:next_offset]
            if syl:
                spans.append((offset, next_offset, syl))
            offset = next_offset
            if break_type == self._parser.MY_PAIR_EOL:
                break
                
        return spans


# Convenience singleton
_default_breaker = None

def break_syllables(text: str, delimiter: str = " ") -> str:
    global _default_breaker
    if _default_breaker is None:
        _default_breaker = SyllableBreaker()
    return _default_breaker.segment_with_delimiter(text, delimiter)

def get_syllables(text: str) -> list[str]:
    global _default_breaker
    if _default_breaker is None:
        _default_breaker = SyllableBreaker()
    return _default_breaker.segment(text)


if __name__ == "__main__":
    sample = sys.argv[1] if len(sys.argv) > 1 else "မြန်မာနိုင်ငံတော်အစိုးရနှင့်ပြည်သူလူထု"
    breaker = SyllableBreaker()
    result = breaker.segment(sample)
    print("Input :", sample)
    print("Syllables:", result)
    print("Joined   :", breaker.segment_with_delimiter(sample, delimiter=" / "))
