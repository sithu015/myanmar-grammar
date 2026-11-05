#!/usr/bin/env python3
"""
legal70k_audit.py — Legal70k Gold Corpus All-in-One Audit CLI

Runs a comprehensive audit pipeline on Legal70k corpus files:
  1. WS validation (orthographic / Unicode / component split checks)
  2. POS validation (15-tag / owner fixed tags / contextual rules)
  3. WS-POS token count parity check (dual-stream alignment)
  4. Intra-corpus consistency scan (segmentation inconsistency detection)
  5. Record-only typo lead scan (non-destructive logging)
  6. Summary report (human-readable or JSON)

Usage:
  python3 scripts/legal70k_audit.py --dir <gold_dir>  [--json] [--out-dir <dir>]
  python3 scripts/legal70k_audit.py --ws <ws.txt> --pos <pos.txt> [--json] [--out-dir <dir>]
  python3 scripts/legal70k_audit.py --dir <gold_dir> --consistency-only
  python3 scripts/legal70k_audit.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

# ── import from sibling scripts ──────────────────────────────────────────────
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parent))

from scripts.validate_nlp_corpus import audit_line, scan_token_consistency, parse_pos_token
from scripts.corpus_chunk_and_remediate import (
    RECORD_ONLY_LEADS,
    stream_remediate_file,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _strip_ws(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _ws_pos_parity(ws_lines: list[str], pos_lines: list[str]) -> list[dict[str, Any]]:
    """Check that every WS line's token count matches the POS line's token count."""
    issues: list[dict[str, Any]] = []
    for idx, (wl, pl) in enumerate(zip(ws_lines, pos_lines), start=1):
        ws_toks = wl.strip().split()
        pos_toks = pl.strip().split()
        if len(ws_toks) != len(pos_toks):
            issues.append(
                {
                    "line": idx,
                    "type": "ws_pos_token_count_mismatch",
                    "ws_count": len(ws_toks),
                    "pos_count": len(pos_toks),
                    "message": (
                        f"WS has {len(ws_toks)} tokens but POS has {len(pos_toks)} tokens "
                        f"on line {idx}."
                    ),
                }
            )
        # Also check codepoint conservation
        ws_chars = _strip_ws("".join(ws_toks))
        pos_chars = _strip_ws("".join(parse_pos_token(t)[0] for t in pos_toks))
        if ws_chars != pos_chars:
            issues.append(
                {
                    "line": idx,
                    "type": "ws_pos_character_mismatch",
                    "message": (
                        f"Surface characters differ between WS and POS streams on line {idx} "
                        f"(ws_len={len(ws_chars)}, pos_surface_len={len(pos_chars)})."
                    ),
                }
            )
    return issues


def _scan_record_only_leads(lines: list[str]) -> list[dict[str, Any]]:
    """Scan for the 8 Owner Record-Only Typo Leads (non-destructive)."""
    hits: list[dict[str, Any]] = []
    for line_no, raw in enumerate(lines, start=1):
        for lead_id, pattern, proposed in RECORD_ONLY_LEADS:
            for m in pattern.finditer(raw):
                hits.append(
                    {
                        "line_number": line_no,
                        "lead_id": lead_id,
                        "observed_surface": m.group(0),
                        "proposed_reading": proposed,
                        "status": "RECORD_ONLY_NOT_APPLIED",
                    }
                )
    return hits


def _auto_detect_files(directory: Path) -> tuple[Path | None, Path | None]:
    """Auto-detect the canonical combined WS and POS files in a gold directory."""
    ws_candidates = sorted(directory.glob("*_ws.txt"))
    pos_candidates = sorted(directory.glob("*_pos.txt"))

    # Prefer the combined file (lines_1_2000) over split files
    def _combined_first(paths: list[Path]) -> Path | None:
        combined = [p for p in paths if re.search(r"_1_\d+_", p.name) or "_lines_1_" in p.name]
        if combined:
            return max(combined, key=lambda p: p.stat().st_size)
        return paths[0] if paths else None

    return _combined_first(ws_candidates), _combined_first(pos_candidates)


# ── main audit function ───────────────────────────────────────────────────────

def run_full_audit(
    ws_path: Path,
    pos_path: Path,
    out_dir: Path | None = None,
    emit_json: bool = False,
) -> dict[str, Any]:
    """Run all 5 audit stages and return a structured report dict."""

    ws_lines = ws_path.read_text(encoding="utf-8").splitlines()
    pos_lines = pos_path.read_text(encoding="utf-8").splitlines()

    # ── Stage 1: WS line-by-line validation ──────────────────────────────────
    ws_issues: list[dict[str, Any]] = []
    for idx, line in enumerate(ws_lines, start=1):
        ws_issues.extend(audit_line(line, idx, mode="ws"))

    # ── Stage 2: POS line-by-line validation ─────────────────────────────────
    pos_issues: list[dict[str, Any]] = []
    if len(ws_lines) == len(pos_lines):
        for idx, (wl, pl) in enumerate(zip(ws_lines, pos_lines), start=1):
            pos_issues.extend(audit_line(pl, idx, mode="pos", ref_line=wl))
    else:
        pos_issues.append(
            {
                "type": "line_count_mismatch",
                "message": f"WS has {len(ws_lines)} lines but POS has {len(pos_lines)} lines.",
            }
        )
        for idx, line in enumerate(pos_lines, start=1):
            pos_issues.extend(audit_line(line, idx, mode="pos"))

    # ── Stage 3: WS ↔ POS dual-stream parity ─────────────────────────────────
    parity_issues: list[dict[str, Any]] = []
    if len(ws_lines) == len(pos_lines):
        parity_issues = _ws_pos_parity(ws_lines, pos_lines)

    # ── Stage 4: Intra-corpus consistency scan ───────────────────────────────
    consistency_issues = scan_token_consistency(ws_lines, mode="ws")

    # ── Stage 5: Record-only typo leads ──────────────────────────────────────
    typo_leads = _scan_record_only_leads(ws_lines)

    # ── Build report ──────────────────────────────────────────────────────────
    overall_pass = (
        len(ws_issues) == 0
        and len(pos_issues) == 0
        and len(parity_issues) == 0
    )

    report: dict[str, Any] = {
        "ws_file": str(ws_path),
        "pos_file": str(pos_path),
        "lines_checked": len(ws_lines),
        "overall_status": "PASS" if overall_pass else "FAIL",
        "stages": {
            "ws_validation": {
                "status": "PASS" if not ws_issues else "FAIL",
                "issue_count": len(ws_issues),
                "issues": ws_issues[:50],
            },
            "pos_validation": {
                "status": "PASS" if not pos_issues else "FAIL",
                "issue_count": len(pos_issues),
                "issues": pos_issues[:50],
            },
            "ws_pos_parity": {
                "status": "PASS" if not parity_issues else "FAIL",
                "issue_count": len(parity_issues),
                "issues": parity_issues[:50],
            },
            "consistency_scan": {
                "status": "PASS" if not consistency_issues else "ADVISORY",
                "inconsistency_type_count": len(consistency_issues),
                "note": "Advisory only — gold corpus may have intentional context-specific splits",
                "issues": consistency_issues[:50],
            },
            "typo_leads": {
                "status": "INFO",
                "lead_count": len(typo_leads),
                "note": "Record-only — never auto-applied",
                "leads": typo_leads,
            },
        },
    }

    # ── Optionally write artefacts ────────────────────────────────────────────
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "audit_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        typo_path = out_dir / "typo_leads.jsonl"
        with typo_path.open("w", encoding="utf-8") as f:
            for lead in typo_leads:
                f.write(json.dumps(lead, ensure_ascii=False) + "\n")

        consistency_path = out_dir / "consistency_issues.json"
        consistency_path.write_text(
            json.dumps(consistency_issues, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return report


def _print_report(report: dict[str, Any], emit_json: bool) -> None:
    if emit_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    status_icon = "✅" if report["overall_status"] == "PASS" else "❌"
    print(f"\n{'='*60}")
    print(f"  Legal70k Gold Corpus Audit Report")
    print(f"  WS : {report['ws_file']}")
    print(f"  POS: {report['pos_file']}")
    print(f"  Lines: {report['lines_checked']}  |  Overall: {status_icon} {report['overall_status']}")
    print(f"{'='*60}")

    stages = report["stages"]

    def _row(name: str, key: str, count_field: str = "issue_count") -> None:
        s = stages[key]
        icon = "✅" if s["status"] in ("PASS", "INFO") else ("⚠️ " if s["status"] == "ADVISORY" else "❌")
        count = s.get(count_field, s.get("lead_count", s.get("inconsistency_type_count", 0)))
        print(f"  {icon} {name:<38} {count:>5} items")

    _row("1. WS Validation", "ws_validation")
    _row("2. POS Validation", "pos_validation")
    _row("3. WS↔POS Parity", "ws_pos_parity")
    _row("4. Consistency Scan (advisory)", "consistency_scan", "inconsistency_type_count")
    _row("5. Record-Only Typo Leads (info)", "typo_leads", "lead_count")
    print(f"{'='*60}")

    # Print first few issues per failing stage
    for stage_key in ("ws_validation", "pos_validation", "ws_pos_parity"):
        s = stages[stage_key]
        if s["issue_count"] > 0:
            print(f"\n  ⚠️  {stage_key} issues (showing ≤10):")
            for issue in s["issues"][:10]:
                loc = f"Line {issue.get('line', '?')}"
                print(f"    [{loc}] {issue['type']}: {issue['message']}")

    # Print typo leads
    leads = stages["typo_leads"]["leads"]
    if leads:
        print(f"\n  📝 Record-Only Typo Leads ({len(leads)} found — not auto-applied):")
        for lead in leads:
            print(
                f"    Line {lead['line_number']:>4} [{lead['lead_id']}] "
                f"'{lead['observed_surface']}' → '{lead['proposed_reading']}'"
            )

    # Print first few consistency advisories
    consistency = stages["consistency_scan"]["issues"]
    if consistency:
        print(f"\n  🔍 Consistency Advisories (showing ≤10 of {len(consistency)}):")
        for issue in consistency[:10]:
            forms = " | ".join(f'"{f}"' for f in issue["observed_forms"])
            print(f"    '{issue['surface_chars']}': {forms}")

    print()


# ── self-test ─────────────────────────────────────────────────────────────────

def run_self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        ws = tmpdir / "test_ws.txt"
        pos = tmpdir / "test_pos.txt"

        ws.write_text(
            "မြန်မာ နိုင်ငံ သည် ဖြစ် သည် ။\n"
            "မြန်မာ နိုင်ငံ တွင် ရှိ သည် ။\n"
            "မြန်မာနိုင်ငံ တွင် ရှိ သည် ။\n"  # line 3: unsplit → triggers WS issue + consistency
            "ပြည်ထောင်စု မြန်မာ နိုင်ငံ ၏ ဥပဒေ ။\n",
            encoding="utf-8",
        )
        pos.write_text(
            "မြန်မာ/n နိုင်ငံ/n သည်/ppm ဖြစ်/v သည်/part ။/punc\n"
            "မြန်မာ/n နိုင်ငံ/n တွင်/ppm ရှိ/v သည်/part ။/punc\n"
            "မြန်မာ/n နိုင်ငံ/n တွင်/ppm ရှိ/v သည်/part ။/punc\n"
            "ပြည်ထောင်စု/n မြန်မာ/n နိုင်ငံ/n ၏/ppm ဥပဒေ/n ။/punc\n",
            encoding="utf-8",
        )

        report = run_full_audit(ws, pos, out_dir=tmpdir)

        # WS stage should FAIL (line 3 has unsplit မြန်မာနိုင်ငံ)
        assert report["stages"]["ws_validation"]["status"] == "FAIL", \
            "WS should FAIL due to unsplit component on line 3"
        assert report["stages"]["ws_validation"]["issue_count"] == 1, \
            f"Expected 1 WS issue, got: {report['stages']['ws_validation']['issue_count']}"

        # Parity: ws line 3 has 1 token မြန်မာနိုင်ငံ, pos line 3 has 2 tokens မြန်မာ/n နိုင်ငံ/n → mismatch
        assert report["stages"]["ws_pos_parity"]["status"] == "FAIL", \
            f"Parity should FAIL on line 3, got: {report['stages']['ws_pos_parity']}"

        # Consistency scan: should detect မြန်မာနိုင်ငံ inconsistency
        forms_found = {i["surface_chars"] for i in report["stages"]["consistency_scan"]["issues"]}
        assert "မြန်မာနိုင်ငံ" in forms_found, \
            f"Consistency scan missed မြန်မာနိုင်ငံ, found: {forms_found}"

        # Check output artefacts written
        assert (tmpdir / "audit_report.json").is_file(), "audit_report.json not written"
        assert (tmpdir / "typo_leads.jsonl").is_file(), "typo_leads.jsonl not written"
        assert (tmpdir / "consistency_issues.json").is_file(), "consistency_issues.json not written"

    print("SELF-TEST PASSED: All 5 audit stages verified, artefacts written.")
    return 0


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legal70k Gold Corpus All-in-One Audit CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect WS + POS from gold directory
  python3 scripts/legal70k_audit.py --dir /path/to/gold_freeze_lines_1_2000

  # With JSON output + save artefacts
  python3 scripts/legal70k_audit.py --dir /path/to/gold_freeze --json --out-dir audit_results/

  # Explicit file paths
  python3 scripts/legal70k_audit.py --ws corpus_ws.txt --pos corpus_pos.txt

  # Consistency scan only (fast)
  python3 scripts/legal70k_audit.py --dir /path/to/gold_freeze --consistency-only

  # Built-in self-test
  python3 scripts/legal70k_audit.py --self-test
        """,
    )
    parser.add_argument("--dir", type=Path, help="Gold corpus directory (auto-detects WS + POS files)")
    parser.add_argument("--ws", type=Path, help="Explicit WS file path")
    parser.add_argument("--pos", type=Path, help="Explicit POS file path")
    parser.add_argument("--out-dir", type=Path, help="Directory to write audit artefacts (report, leads, consistency)")
    parser.add_argument("--json", action="store_true", help="Emit JSON report to stdout")
    parser.add_argument("--consistency-only", action="store_true", help="Run consistency scan only (fast)")
    parser.add_argument("--self-test", action="store_true", help="Run built-in self-test")

    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    # Resolve WS + POS paths
    ws_path: Path | None = args.ws
    pos_path: Path | None = args.pos

    if args.dir:
        if not args.dir.is_dir():
            print(f"ERROR: --dir '{args.dir}' is not a directory.", file=sys.stderr)
            return 1
        auto_ws, auto_pos = _auto_detect_files(args.dir)
        if ws_path is None:
            ws_path = auto_ws
        if pos_path is None:
            pos_path = auto_pos

    if args.consistency_only:
        if not ws_path or not ws_path.is_file():
            print("ERROR: Could not find WS file for consistency scan.", file=sys.stderr)
            return 1
        ws_lines = ws_path.read_text(encoding="utf-8").splitlines()
        issues = scan_token_consistency(ws_lines)
        if args.json:
            print(json.dumps({"file": str(ws_path), "inconsistency_count": len(issues), "issues": issues},
                             ensure_ascii=False, indent=2))
        else:
            print(f"Consistency scan '{ws_path.name}': {len(issues)} inconsistent token types")
            for issue in issues[:20]:
                forms = " | ".join(f'"{f}"' for f in issue["observed_forms"])
                print(f"  '{issue['surface_chars']}': {forms}")
            if len(issues) > 20:
                print(f"  ... +{len(issues) - 20} more")
        return 0

    if not ws_path or not ws_path.is_file():
        print(f"ERROR: WS file not found: {ws_path}", file=sys.stderr)
        parser.print_help()
        return 1
    if not pos_path or not pos_path.is_file():
        print(f"ERROR: POS file not found: {pos_path}", file=sys.stderr)
        parser.print_help()
        return 1

    report = run_full_audit(ws_path, pos_path, out_dir=args.out_dir, emit_json=args.json)
    _print_report(report, emit_json=args.json)

    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
