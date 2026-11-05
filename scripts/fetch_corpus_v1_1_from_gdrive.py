#!/usr/bin/env python3
"""
Optional downloader for Myanmar News Corpus Release v1.1.

Do not run this unless the user explicitly asks to download that corpus.
It shells out to the `gdrive` CLI. The Extreme SSD path below is the
author's machine and is not a portable default.

Usage:
  # Download and extract the full corpus (146 MB):
  python3 fetch_corpus_v1_1_from_gdrive.py --target-dir ./myanmar_news_corpus_release_v1.1

  # Download only NER Entity Catalog (42,210 entities):
  python3 fetch_corpus_v1_1_from_gdrive.py --download-catalog --out ./ner_entity_catalog.json.gz

  # Download only Grounded Parallel Sentences (173k sentences):
  python3 fetch_corpus_v1_1_from_gdrive.py --download-sentences --out ./parallel_sentences_5d.jsonl.gz

  # Check availability on Drive:
  python3 fetch_corpus_v1_1_from_gdrive.py --status
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

# Authoritative Google Drive File & Folder IDs
GDRIVE_IDS = {
    "release_archive_tar_gz": "1P8yVDC0RfNCuVwmW_mjvPxpay_dOl4VR",  # 146 MB
    "release_folder_root": "1u6T5Nd1scat7i1FxxoXvpEfLJRhUTyQd",     # Folder
    "ner_entity_catalog": "1XSUni58ff7Rn1__W9o54M8Hq4ZclgQbE",      # mappings/ner_entity_catalog.json.gz
    "parallel_sentences_5d": "1-w6dAB_MIHBOkUf_kD30R99FD4TErfFy",   # sentences/parallel_sentences_5d.jsonl.gz
    "ner_taxonomy": "1exgkmF_W5R2hO46CtFSSaqUbe6pQcOS2",            # metadata/ner_taxonomy.json
    "inventory_postpositions": "1tEPITiOUnfKFnQD7AikGfONCuWjX_kY_", # audit_and_reports/INVENTORY_POSTPOSITIONS.md
    "inventory_compounds": "1XU8Tomj8OxNQbh1dOhqx52fUBwyx8dfv",     # audit_and_reports/INVENTORY_COMPOUND_SUFFIXES.md
    "ner_comprehensive_audit": "1Y9Uqwjb7D2nOaEmLNfELfbbF2sCupRyD", # audit_and_reports/NER_COMPREHENSIVE_AUDIT_REPORT.md
}

EXTERNAL_SSD_PATH = Path("/Volumes/Extreme SSD/projects_document/myanmar_news_corpus_release_v1.1")


def run_gdrive(cmd_args: list[str]) -> str:
    res = subprocess.run(["gdrive"] + cmd_args, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"gdrive command failed: {' '.join(cmd_args)}\nError: {res.stderr}")
    return res.stdout.strip()


def check_status() -> None:
    print("=" * 70)
    print("Myanmar News Corpus (Release v1.1) Storage Availability Status")
    print("=" * 70)
    # 1. External SSD check
    if EXTERNAL_SSD_PATH.is_dir():
        print(f"• External SSD : CONNECTED & AVAILABLE at '{EXTERNAL_SSD_PATH}'")
    else:
        print("• External SSD : DISCONNECTED / UNMOUNTED")

    # 2. Google Drive check
    try:
        info = run_gdrive(["readonly", "info", GDRIVE_IDS["release_archive_tar_gz"]])
        print("• Google Drive : CONNECTED & READY")
        print(f"  - Full Archive Tarball ID: {GDRIVE_IDS['release_archive_tar_gz']} (146 MB)")
        print(f"  - Full Folder Root ID    : {GDRIVE_IDS['release_folder_root']}")
        print(f"  - Entity Catalog (42k) ID: {GDRIVE_IDS['ner_entity_catalog']}")
        print(f"  - Sentences (173k) ID    : {GDRIVE_IDS['parallel_sentences_5d']}")
    except Exception as e:
        print(f"• Google Drive : Error connecting to gdrive CLI: {e}")
    print("=" * 70)


def download_file(file_id: str, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading file (ID: {file_id}) to '{out_path}'...")
    run_gdrive(["readonly", "download", file_id, "--out", str(out_path)])
    print(f"Successfully downloaded: {out_path} ({out_path.stat().st_size / (1024*1024):.2f} MB)")
    return out_path


def fetch_full_corpus(target_dir: Path) -> None:
    if target_dir.is_dir() and any(target_dir.iterdir()):
        print(f"Target directory '{target_dir}' already exists and is not empty.")
        confirm = input("Overwrite / extract into this directory? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    tmp_tar = Path(f"/tmp/release_v1_1_{os.getpid()}.tar.gz")
    try:
        download_file(GDRIVE_IDS["release_archive_tar_gz"], tmp_tar)
        print(f"Extracting archive to '{target_dir.parent}'...")
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tmp_tar, "r:gz") as tar:
            tar.extractall(path=target_dir.parent)
        print(f"Extraction complete! Release v1.1 is ready at '{target_dir}'.")
    finally:
        if tmp_tar.exists():
            tmp_tar.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Myanmar News Corpus Release v1.1 from Google Drive.")
    parser.add_argument("--status", action="store_true", help="Check local SSD and Google Drive status")
    parser.add_argument("--target-dir", type=Path, help="Target directory to extract full corpus to")
    parser.add_argument("--download-catalog", action="store_true", help="Download 42,210 entity catalog")
    parser.add_argument("--download-sentences", action="store_true", help="Download 173k parallel sentences with NER")
    parser.add_argument("--out", type=Path, help="Output destination path for single-file downloads")
    args = parser.parse_args()

    if args.status or len(sys.argv) == 1:
        check_status()
        return 0

    if args.download_catalog:
        dest = args.out or Path("./ner_entity_catalog.json.gz")
        download_file(GDRIVE_IDS["ner_entity_catalog"], dest)
        return 0

    if args.download_sentences:
        dest = args.out or Path("./parallel_sentences_5d.jsonl.gz")
        download_file(GDRIVE_IDS["parallel_sentences_5d"], dest)
        return 0

    if args.target_dir:
        fetch_full_corpus(args.target_dir)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
