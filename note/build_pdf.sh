#!/usr/bin/env bash
# Render note/quant_note.html to note/quant_note.pdf with headless Edge (Chrome works the same way).
cd "$(dirname "$0")"
BROWSER="${BROWSER:-/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"
"$BROWSER" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$(cygpath -w "$PWD")\quant_note.pdf" "file:///$(cygpath -m "$PWD")/quant_note.html" 2>/dev/null
