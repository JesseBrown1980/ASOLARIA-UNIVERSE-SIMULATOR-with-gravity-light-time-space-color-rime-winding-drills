#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/web/tri_star_kernel.wasm"
clang --target=wasm32 -O3 -nostdlib \
  -Wl,--no-entry \
  -Wl,--export-memory \
  -Wl,--initial-memory=131072 \
  -Wl,--max-memory=131072 \
  -Wl,--export=key_buffer_ptr \
  -Wl,--export=key_capacity \
  -Wl,--export=init_from_key \
  -Wl,--export=set_star_mask \
  -Wl,--export=get_star_mask \
  -Wl,--export=set_centre_enabled \
  -Wl,--export=get_centre_enabled \
  -Wl,--export=reset_network \
  -Wl,--export=rotate_node \
  -Wl,--export=encode_trit \
  -Wl,--export=decode_trit \
  -Wl,--export=pack_27 \
  -Wl,--export=pump \
  -Wl,--export=node_value \
  -Wl,--export=node_base \
  -Wl,--export=node_star \
  -Wl,--export=node_rotation \
  -Wl,--export=node_direction \
  -Wl,--export=centre_energy \
  -Wl,--export=centre_residual \
  -Wl,--export=pumps \
  -Wl,--export=network_digest \
  -Wl,--export=closure_error \
  -Wl,--export=node_count \
  "$ROOT/src/tri_star_kernel.c" -o "$OUT"
base64 -w 76 "$OUT" > "$OUT.b64"
sha256sum "$OUT" "$OUT.b64"
