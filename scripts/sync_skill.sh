#!/usr/bin/env bash
# ==============================================================================
# myanmar-grammar Synchronization & GitHub Integration Script
#
# Keeps the following three locations in permanent lockstep:
# 1. ~/.gemini/config/skills/myanmar-grammar (symlink -> ~/.agents/skills/myanmar-grammar)
# 2. ~/Downloads/myanmar-grammar
# 3. https://github.com/sithu015/myanmar-grammar (origin/main)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SKILL_CONFIG_DIR="$HOME/.agents/skills/myanmar-grammar"
SKILL_DOWNLOADS_DIR="$HOME/Downloads/myanmar-grammar"
REMOTE_REPO="git@github.com:sithu015/myanmar-grammar.git"

ACTION="${1:-status}"

function print_header() {
    echo "=================================================================="
    echo "  myanmar-grammar Synchronization Utility"
    echo "  Action: $ACTION"
    echo "=================================================================="
}

function verify_tests() {
    local target_dir="${1:-$REPO_DIR}"
    echo "==> Running NLP unit test suite and self-tests in $target_dir..."
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/test_nlp_tools.py" -v
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/confusable.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/decide.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/project_mypos_hd.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/nominal.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/register.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/verb_pair.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/validate_nlp_corpus.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/corpus_chunk_and_remediate.py" --self-test
    PYTHONDONTWRITEBYTECODE=1 python3 -B "$target_dir/scripts/legal70k_audit.py" --self-test
    echo "==> All 10 test suites passed cleanly."
}

function check_diff() {
    echo "==> Checking diff between Config Skill and Downloads Skill..."
    DIFF_OUT=$(diff -rq -x ".git" -x ".DS_Store" -x "__pycache__" -x "*.pyc" -x "*.zip" "$SKILL_CONFIG_DIR" "$SKILL_DOWNLOADS_DIR" || true)
    if [ -z "$DIFF_OUT" ]; then
        echo "✓ Zero differences between Config Skill and Downloads Skill."
    else
        echo "⚠ Differences detected:"
        echo "$DIFF_OUT"
    fi
}

function do_status() {
    print_header
    echo "==> Config Skill Git Status ($SKILL_CONFIG_DIR):"
    git -C "$SKILL_CONFIG_DIR" status -s
    echo "==> Downloads Skill Git Status ($SKILL_DOWNLOADS_DIR):"
    git -C "$SKILL_DOWNLOADS_DIR" status -s
    check_diff
}

function do_pull() {
    print_header
    echo "==> Pulling latest changes from GitHub origin/main to Config Skill..."
    git -C "$SKILL_CONFIG_DIR" pull origin main
    echo "==> Pulling latest changes from GitHub origin/main to Downloads Skill..."
    git -C "$SKILL_DOWNLOADS_DIR" pull origin main
    check_diff
    verify_tests
    echo "✓ Both locations are fully up to date with origin/main."
}

function do_sync() {
    print_header
    MSG="${2:-Synchronize Myanmar Grammar skill and rules}"

    # Bidirectional propagation of uncommitted working tree changes
    if [ -n "$(git -C "$SKILL_DOWNLOADS_DIR" status -s)" ] && [ -z "$(git -C "$SKILL_CONFIG_DIR" status -s)" ]; then
        echo "==> Propagating changes from Downloads Skill to Config Skill..."
        rsync -av --exclude=".git" --exclude="__pycache__" --exclude="*.pyc" --exclude="*.zip" "$SKILL_DOWNLOADS_DIR/" "$SKILL_CONFIG_DIR/"
    elif [ -n "$(git -C "$SKILL_CONFIG_DIR" status -s)" ] && [ -z "$(git -C "$SKILL_DOWNLOADS_DIR" status -s)" ]; then
        echo "==> Propagating changes from Config Skill to Downloads Skill..."
        rsync -av --exclude=".git" --exclude="__pycache__" --exclude="*.pyc" --exclude="*.zip" "$SKILL_CONFIG_DIR/" "$SKILL_DOWNLOADS_DIR/"
    fi

    echo "==> Staging and committing in Config Skill..."
    git -C "$SKILL_CONFIG_DIR" add .
    if ! git -C "$SKILL_CONFIG_DIR" diff-index --quiet HEAD --; then
        git -C "$SKILL_CONFIG_DIR" commit -m "$MSG"
        echo "==> Pushing to GitHub origin main..."
        git -C "$SKILL_CONFIG_DIR" push origin main
    else
        echo "Config Skill has no changes to commit."
    fi

    echo "==> Updating Downloads Skill..."
    git -C "$SKILL_DOWNLOADS_DIR" fetch origin main
    git -C "$SKILL_DOWNLOADS_DIR" reset --hard origin/main
    check_diff
    verify_tests
    echo "✓ Both locations and GitHub are 100% synchronized."
}

case "$ACTION" in
    status)
        do_status
        ;;
    pull)
        do_pull
        ;;
    push|sync)
        do_sync "$@"
        ;;
    verify)
        print_header
        check_diff
        verify_tests "$REPO_DIR"
        ;;
    *)
        echo "Usage: $0 {status|pull|sync [commit_message]|verify}"
        exit 1
        ;;
esac
