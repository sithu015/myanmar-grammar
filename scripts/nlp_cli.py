#!/usr/bin/env python3
"""
tools/nlp_cli.py — Command-Line Interface for Myanmar NLP Tools.

Supports:
  - Syllable Segmentation
  - Word Segmentation & Tokenization
  - Dictionary Lookup & Frequency Inspection
  - File Batch Processing & Benchmarking
"""

import argparse
import json
import os
import sys
import time

try:
    from .syllable_breaker import SyllableBreaker
    from .word_segmenter import WordSegmenter
except ImportError:
    from syllable_breaker import SyllableBreaker
    from word_segmenter import WordSegmenter


def main():
    parser = argparse.ArgumentParser(
        description="Myanmar NLP Toolkit powered by TTKeyboard Reverse-Engineered Engine"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--syllable", type=str, help="Segment text into syllables")
    group.add_argument("-w", "--word", type=str, help="Segment text into words")
    group.add_argument("-t", "--tokenize", type=str, help="Tokenize text with spans and frequency")
    group.add_argument("-l", "--lookup", type=str, help="Lookup word in TTKeyboard dictionary")
    group.add_argument("-f", "--file", type=str, help="Process file line-by-line")
    group.add_argument("-c", "--decide", type=str, help="Segment raw text and decide myPOS tags")
    group.add_argument("--benchmark", action="store_true", help="Run throughput benchmark")

    parser.add_argument("-d", "--delimiter", type=str, default=" | ", help="Delimiter between tokens")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    syl_breaker = SyllableBreaker()
    word_seg = WordSegmenter()

    if args.syllable:
        result = syl_breaker.segment(args.syllable)
        if args.json:
            print(json.dumps({"input": args.syllable, "syllables": result}, ensure_ascii=False, indent=2))
        else:
            print(args.delimiter.join(result))

    elif args.word:
        result = word_seg.segment(args.word)
        if args.json:
            print(json.dumps({"input": args.word, "words": result}, ensure_ascii=False, indent=2))
        else:
            print(args.delimiter.join(result))

    elif args.tokenize:
        tokens = word_seg.tokenize(args.tokenize)
        print(json.dumps(tokens, ensure_ascii=False, indent=2))

    elif args.lookup:
        in_dict = word_seg.is_word(args.lookup)
        freq = word_seg.get_frequency(args.lookup)
        info = {
            "query": args.lookup,
            "in_dict": in_dict,
            "frequency": freq,
            "syllables": syl_breaker.segment(args.lookup)
        }
        print(json.dumps(info, ensure_ascii=False, indent=2))

    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    words = word_seg.segment(line)
                    print(args.delimiter.join(words))

    elif args.decide:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from decide import decide_tokens, load_table

        tokens = word_seg.segment(args.decide)
        print(json.dumps(
            {"tokens": tokens, "decisions": decide_tokens(tokens, load_table())},
            ensure_ascii=False,
            indent=2,
        ))

    elif args.benchmark:
        test_sentences = [
            "မြန်မာနိုင်ငံတော်အစိုးရနှင့်ပြည်သူလူထု",
            "ကာကွယ်ရေးဦးစီးချုပ်သည်စစ်ဆေးရေးအရာရှိချုပ်နှင့်တွေ့ဆုံခဲ့သည်",
            "ကိုယ်တိုင်ရေးအတ္ထုပ္ပတ္တိစာအုပ်ကိုဖတ်ရှုပါ",
            "အတွေ့အကြုံဖလှယ်ဆွေးနွေးပွဲတွင်ကျန်းမာရေးဝန်ထမ်းများတက်ရောက်သည်",
            "သတင်းထောက်များသတင်းရယူခွင့်ရှိသည်",
            "ကမ္ဘာ့ကျန်းမာရေးအဖွဲ့သည်ရောဂါကာကွယ်ရေးအတွက်ဆောင်ရွက်လျက်ရှိသည်",
            "စီးပွားရေးနှင့်ကူးသန်းရောင်းဝယ်ရေးဝန်ကြီးဌာန",
            "ပြည်ထောင်စုသမ္မတမြန်မာနိုင်ငံတော်ဖွဲ့စည်းပုံအခြေခံဥပဒေ"
        ]
        
        # Benchmark 300 iterations
        rounds = 300
        start = time.time()
        total_chars = 0
        for _ in range(rounds):
            for s in test_sentences:
                total_chars += len(s)
                _ = word_seg.segment(s)
        duration = time.time() - start
        
        print("=== Performance Benchmark ===")
        print(f"Total Sentences Processed: {rounds * len(test_sentences):,}")
        print(f"Total Characters Processed: {total_chars:,}")
        print(f"Total Time Taken          : {duration:.3f} seconds")
        print(f"Throughput                : {total_chars / duration:,.1f} chars/sec")
        print(f"Sentences/sec             : {(rounds * len(test_sentences)) / duration:,.1f} sentences/sec")


if __name__ == "__main__":
    main()
