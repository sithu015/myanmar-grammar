#!/usr/bin/env python3
"""Mine a supplementary domain lexicon from a gold POS corpus and evaluate it.

Evidence-based: only tokens that appear >= --min-freq times in gold are added.
Mining uses odd lines; evaluation uses held-out even lines (no leakage).

  python3 scripts/mine_domain_lexicon.py --gold FILE --out resources/lexicon/domain_legal.txt
  python3 scripts/mine_domain_lexicon.py --gold FILE --evaluate
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_standards import parse_pos_token
from word_segmenter import WordSegmenter

ROOT = Path(__file__).resolve().parent.parent
MM = re.compile(r"^[\u1000-\u109f]+$")
# Boundary traps documented in references/decide-first.md and owner_keep_whole.txt
TRAPS = {"အရသာ", "သူမ", "ကလေး", "တရားမ", "ယူဆောင်", "ခေတ္တရပ်", "မြန်မာနိုင်ငံ",
         "မြန်မာနိုင်ငံတော်", "တကျွန်းပို့ဒဏ်ခံ"}
FUNCTION_TAGS = {"part", "ppm", "punc", "sb", "conj"}
# Indefinite reduplications (တစ်နည်းနည်း = တစ် + နည်းနည်း) must stay 2 tokens.
REDUP = re.compile(r"^(?:တစ်|တ)(.+?)\1$")

# Patterns for multi-token clitic concatenations that should never enter the lexicon
CLITIC_PATTERNS = [
    # 1. Pronoun + Postposition (ဒီ, ဟို)
    re.compile(r"^(?:ဒီ|ဟို)(?:ကို|မှာ|တွင်|သို့|မှ|အတွက်)$"),
    # 2. Location / body noun + postposition
    re.compile(r"^(?:ဆီ|လက်|ခြေ|နှုတ်|ပါးစပ်)(?:ကို|သို့|ဖြင့်|နဲ့)$"),
    # 3. Stacked particles / postpositions
    re.compile(r"^(?:အတွက်ကြောင့်|တောင်မှ|ကိုမှ|ကပင်|မှပင်|နှင့်ပင်|နဲ့ပင်|မှသာ|တွင်သာ)$"),
    # 4. Adverb + နဲ့/နှင့်
    re.compile(r"^(.+?စွာ)(?:နဲ့|နှင့်)$"),
    # 5. Finite Verb + Aux / SFP
    re.compile(r"^(.+?)(?:ခဲ့သော|ခဲ့သည်|ရမည်|နိုင်သည်|သွားသည်|လာသည်|ဖြစ်သည်|ပါသည်|ရပါမည်|လတ္တံ့|ကြသည်|ကြသော|ကြမည်)$"),
    # 6. Verbal phrases ending in ရှိသည် / နှင့် (e.g. အစရှိသည်, သိနှင့်)
    re.compile(r"^(?:အစရှိသည်|သိနှင့်|စတင်ခဲ့သော|ဖြစ်ပွားခဲ့သော|ရောက်ရှိခဲ့သော|ထွက်ခွာရမည်)$"),
    # 7. Indefinite reduplications
    re.compile(r"^(?:တစ်|တ)(?:နေ့နေ့|ရက်ရက်|ခါခါ|ချိန်ချိန်|ဦးဦး|ခုခု|ရပ်ရပ်|ယောက်ယောက်|မျိုးမျိုး|နည်းနည်း)$"),
    # 8. Numeral (တ/တစ်) + Time measure noun (နေ့, ရက်, လ, နှစ်, နာရီ, မိနစ်, စက္ကန့်)
    re.compile(r"^(?:တစ်|တ)(?:နေ့|ရက်|လ|နှစ်|နာရီ|မိနစ်|စက္ကန့်)$"),
]


def is_toxic_clitic(w: str) -> bool:
    return any(p.match(w) for p in CLITIC_PATTERNS)


def do_not_glue() -> set[str]:
    """Glued forms listed in references/agent-hard-cases.md 'Do not glue' table."""
    p = ROOT / "references" / "agent-hard-cases.md"
    out: set[str] = set()
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `"):
            first = line.split("|")[1]
            out.update(re.findall(r"`([^`]+)`", first))
    return {w.replace(" ", "") for w in out}


BRACKET = re.compile(r"\[([^\]]*)\]/[a-z]+")
SID_PREFIX = ""
EXCLUDE_SID = ""


def gold_lines(path: Path):
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if "\t" in line:  # "<sentence-id>\t<tokens>" (harmonized master format)
                sid, line = line.split("\t", 1)
                if SID_PREFIX and not sid.startswith(SID_PREFIX):
                    continue
                if EXCLUDE_SID and sid.startswith(EXCLUDE_SID):
                    continue
            line = BRACKET.sub(lambda m: " ".join(m.group(1).split("|")), line)  # flatten [a/n|b/n]/n
            toks = [parse_pos_token(t) for t in line.split()]
            toks = [t for t in toks if t]
            if toks:
                yield i, toks


def known_words() -> set[str]:
    words = set()
    for name in ("my_MM_lexicon.txt", "my_MM_comprehensive_lexicon.txt", "owner_keep_whole.txt"):
        p = ROOT / "resources" / "lexicon" / name
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line and not line.startswith("#"):
                    words.add(line.split("\t")[0])
    return words


def mine(
    gold: Path,
    min_freq: int,
    min_len: int,
    dominance_ratio: float = 0.0,
) -> list[tuple[str, int]]:
    known = known_words()
    cnt: Counter[str] = Counter()
    sentences: list[list[str]] = []
    for i, toks in gold_lines(gold):
        if i % 2 == 0:  # even lines are held out for evaluation
            continue
        words = [w for w, _ in toks]
        sentences.append(words)
        for w, tag in toks:
            if tag in FUNCTION_TAGS or not MM.match(w) or len(w) < min_len:
                continue
            cnt[w] += 1
    glue = do_not_glue()
    candidates = {
        w for w, c in cnt.items()
        if c >= min_freq and w not in known and w not in TRAPS
        and w not in glue and not REDUP.match(w) and not is_toxic_clitic(w)
    }

    if dominance_ratio > 0.0 and candidates:
        max_cand_len = max(len(w) for w in candidates)
        split_counts: Counter[str] = Counter()
        for words in sentences:
            n = len(words)
            for j in range(n):
                curr = ""
                for k in range(j, min(j + 6, n)):
                    curr += words[k]
                    if len(curr) > max_cand_len:
                        break
                    if k > j and curr in candidates:
                        split_counts[curr] += 1
        filtered = {}
        for w in candidates:
            c = cnt[w]
            s = split_counts[w]
            ratio = c / (c + s) if (c + s) > 0 else 1.0
            if ratio >= dominance_ratio:
                filtered[w] = c
        candidates = set(filtered.keys())

    return sorted(((w, cnt[w]) for w in candidates),
                  key=lambda x: (-x[1], x[0]))


def spans(tokens: list[str]) -> set[tuple[int, int]]:
    out, pos = set(), 0
    for t in tokens:
        out.add((pos, pos + len(t)))
        pos += len(t)
    return out


def evaluate(gold: Path, extra: Path | None, limit: int, profile: str = "legal70k") -> tuple[float, float, float]:
    seg = WordSegmenter(profile=profile)
    if extra:
        seg.load_lexicon(str(extra))
    tp = fp = fn = 0
    n = 0
    for i, toks in gold_lines(gold):
        if i % 2 == 1:
            continue
        words = [w for w, _ in toks]
        pred = seg.segment("".join(words))
        g, p = spans(words), spans(pred)
        tp += len(g & p)
        fp += len(p - g)
        fn += len(g - p)
        n += 1
        if n >= limit:
            break
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return pr, rc, 2 * pr * rc / (pr + rc) if pr + rc else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--min-freq", type=int, default=5)
    ap.add_argument("--min-len", type=int, default=3, help="min codepoints")
    ap.add_argument("--dominance-ratio", type=float, default=0.0,
                    help="minimum single_count / (single_count + split_count) to filter minority glues")
    ap.add_argument("--profile", default="legal70k")
    ap.add_argument("--sid-prefix", default="", help="only sentence ids with this prefix")
    ap.add_argument("--exclude-sid-prefix", default="")
    ap.add_argument("--evaluate", action="store_true")
    ap.add_argument("--limit", type=int, default=3000)
    a = ap.parse_args()
    global SID_PREFIX, EXCLUDE_SID
    SID_PREFIX, EXCLUDE_SID = a.sid_prefix, a.exclude_sid_prefix
    if a.out:
        entries = mine(a.gold, a.min_freq, a.min_len, a.dominance_ratio)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text("# Mined from gold odd lines; domain supplement. Do not hand-edit.\n" +
                         "".join(f"{w}\t{c}\n" for w, c in entries), encoding="utf-8")
        print(f"wrote {len(entries)} entries -> {a.out}")
    if a.evaluate:
        base = evaluate(a.gold, None, a.limit, a.profile)
        print("baseline  P=%.4f R=%.4f F1=%.4f" % base)
        if a.out:
            ext = evaluate(a.gold, a.out, a.limit, a.profile)
            print("+domain   P=%.4f R=%.4f F1=%.4f" % ext)
    return 0


if __name__ == "__main__":
    sys.exit(main())
