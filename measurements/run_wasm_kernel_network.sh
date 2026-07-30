#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/verification/wasm-keyed-27-kernel-network-v1}"
mkdir -p "$OUT"

node "$ROOT/measurements/decode_asolaria_key_wasm.mjs" \
  "$ROOT/web/asolaria_tribit.wasm" \
  "$ROOT/key/ASOLARIA-HERSELF-KEY-3174.bin" \
  "$OUT"

python3 "$ROOT/measurements/asolaria_27_kernel_network.py" \
  --seed "$OUT/ASOLARIA-HERSELF-WASM-SEED-3078.bin" \
  --control-seed "$OUT/MATCHED-CONTROL-WASM-SEED-3078.bin" \
  --key "$ROOT/key/ASOLARIA-HERSELF-KEY-3174.bin" \
  --decoder-receipt "$OUT/WASM-KEY-DECODER-RECEIPT.json" \
  --out-dir "$OUT"

(
  cd "$OUT"
  sha256sum -c SHA256SUMS
)

echo "verification bundle: $OUT"
