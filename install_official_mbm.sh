#!/usr/bin/env bash
set -euo pipefail
# Run in a development computer with internet BEFORE publishing to GitHub.
# Keep the upstream license and record the exact commit hash for reproducibility.
mkdir -p vendor
if [ -e vendor/MBM ]; then echo 'vendor/MBM already exists' >&2; exit 1; fi
git clone https://github.com/NSBLab/MBM.git vendor/MBM
(cd vendor/MBM && git rev-parse HEAD) > MBM_UPSTREAM_COMMIT.txt
echo 'Original toolbox checked out. Obtain matching example/template inputs separately from authors OSF link in README.'
