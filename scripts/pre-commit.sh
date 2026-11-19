#!/usr/bin/env bash
# Install with: make hooks
set -e
cd "$(git rev-parse --show-toplevel)"
make -s test
