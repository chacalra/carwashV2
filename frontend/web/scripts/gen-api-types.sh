#!/usr/bin/env bash
#
# Genera src/lib/api/schema.d.ts desde el openapi.json del backend.
# Uso:
#   bun run gen:api                                # default localhost:8000
#   bun run gen:api http://otro-host:8000          # custom URL
#

set -euo pipefail

URL="${1:-http://localhost:8000/openapi.json}"
OUTPUT="src/lib/api/schema.d.ts"

if ! command -v bunx >/dev/null && ! command -v npx >/dev/null; then
  echo "Necesitás bun o npm en el PATH."
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

echo "→ Generando tipos desde $URL"

if command -v bunx >/dev/null; then
  bunx openapi-typescript "$URL" -o "$OUTPUT"
else
  npx openapi-typescript "$URL" -o "$OUTPUT"
fi

echo "✓ Generado: $OUTPUT"
