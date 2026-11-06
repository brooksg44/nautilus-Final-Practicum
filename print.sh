#!/usr/bin/env bash
# Print this project's Ladder (.ld) and FBD (.fbd) files to ./print/*.html.
# Usage: ./print.sh [--open]    (--open shows each page in the browser)
# The printers live in MyNautilus/tools; see print-project.sh there.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$HERE/../../tools/print-project.sh" "$HERE" "$@"
