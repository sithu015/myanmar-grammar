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
    echo "==> Running NLP unit test suite..."
    python3 "$SKILL_CONFIG_DIR/scripts/test_nlp_tools.py"
    python3 "$SKILL_CONFIG_DIR/scripts/decide.py" --self-test
    python3 "$SKILL_CONFIG_DIR/scripts/project_mypos_hd.py" --self-test
    python3 "$SKILL_CONFIG_DIR/scripts/validate_nlp_corpus.py" --self-test
    python3 "$SKILL_CONFIG_DIR/scripts/nominal.py" --self-test
    echo "==> All test suites passed cleanly."
}

function check_diff() {
    echo "==> Checking diff between Config Skill and Downloads Skill..."
    DIFF_OUT=$(diff -rq -x ".git" -x ".DS_Store" -x "__pycache__" -x "*.pyc" "$SKILL_CONFIG_DIR" "$SKILL_DOWNLOADS_DIR" || true)
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
    git -C "$SKILL_DOWNLOADS_DIR" pull origin main
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
        verify_tests
        ;;
    *)
        echo "Usage: $0 {status|pull|sync [commit_message]|verify}"
        exit 1
        ;;
esac
