#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const [wasmPath, keyPath, outDir] = process.argv.slice(2);
if (!wasmPath || !keyPath || !outDir) {
  console.error('usage: node decode_asolaria_key_wasm.mjs <wasm> <key> <out-dir>');
  process.exit(2);
}
fs.mkdirSync(outDir, { recursive: true });
const wasmBytes = fs.readFileSync(wasmPath);
const key = fs.readFileSync(keyPath);
const expectedKey = '925c818d4c84aa23d7cee5d13e1b142b90824724a4ed4a90f9ee019c59cc2d89';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
if (sha(key) !== expectedKey) {
  throw new Error(`Asolaria key hash mismatch: got ${sha(key)}, expected ${expectedKey}`);
}
const { instance } = await WebAssembly.instantiate(wasmBytes, {});
const e = instance.exports;

function decode(input) {
  const cap = e.input_capacity();
  if (input.length > cap) throw new Error(`input ${input.length} exceeds capacity ${cap}`);
  const mem = new Uint8Array(e.memory.buffer);
  mem.fill(0, e.input_ptr(), e.input_ptr() + cap);
  mem.set(input, e.input_ptr());
  const cells = e.make_seed(input.length);
  const len = e.seed_len();
  const seed = Buffer.from(new Uint8Array(e.memory.buffer, e.output_ptr(), len));
  const packed = e.count_channel();
  const declared = packed >>> 20;
  const produced = (packed >>> 10) & 1023;
  const withheld = packed & 1023;
  return {
    seed,
    receipt: {
      input_bytes: input.length,
      input_sha256: sha(input),
      seed_bytes: len,
      seed_sha256: sha(seed),
      lattice_cells: cells,
      prism_roundtrip_exact: Boolean(e.prism_roundtrip_exact()),
      trit_bits: e.trit_bits_x10000() / 10000,
      count_channel: { declared, produced, withheld, reconciles: declared === produced + withheld },
      chain_intact: Boolean(e.chain_intact()),
      hidden_holes: e.hidden_holes(),
    }
  };
}

function deterministicControl(n) {
  const chunks = [];
  let counter = 0;
  while (Buffer.concat(chunks).length < n) {
    const h = crypto.createHash('sha256')
      .update('ASOLARIA-KERNEL-NETWORK-MATCHED-CONTROL-V1')
      .update(Buffer.from(String(counter++)))
      .digest();
    chunks.push(h);
  }
  return Buffer.concat(chunks).subarray(0, n);
}

const full = decode(key);
const controlInput = deterministicControl(key.length);
const control = decode(controlInput);

for (const [name, r] of [['asolaria', full], ['matched-control', control]]) {
  if (r.receipt.lattice_cells !== 27) throw new Error(`${name}: expected 27 cells`);
  if (!r.receipt.prism_roundtrip_exact) throw new Error(`${name}: prism drift`);
  if (!r.receipt.count_channel.reconciles || !r.receipt.chain_intact || r.receipt.hidden_holes !== 0) {
    throw new Error(`${name}: receipt integrity gate failed`);
  }
}

fs.writeFileSync(path.join(outDir, 'ASOLARIA-HERSELF-WASM-SEED-3078.bin'), full.seed);
fs.writeFileSync(path.join(outDir, 'MATCHED-CONTROL-WASM-SEED-3078.bin'), control.seed);
const receipt = {
  schema: 'ASOLARIA-WASM-KEY-DECODE-V1',
  runtime: process.version,
  wasm_bytes: wasmBytes.length,
  wasm_sha256: sha(wasmBytes),
  key_expected_sha256: expectedKey,
  asolaria: full.receipt,
  matched_control: control.receipt,
  gate: 'PASS'
};
fs.writeFileSync(path.join(outDir, 'WASM-KEY-DECODER-RECEIPT.json'), JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify(receipt, null, 2));
