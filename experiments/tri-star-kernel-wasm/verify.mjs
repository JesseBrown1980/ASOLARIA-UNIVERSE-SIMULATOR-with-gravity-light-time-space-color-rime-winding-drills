import fs from 'node:fs';
import crypto from 'node:crypto';

const root = new URL('.', import.meta.url);
const wasmPath = new URL('./web/tri_star_kernel.wasm', root);
const wasmBytes = fs.existsSync(wasmPath)
  ? fs.readFileSync(wasmPath)
  : Buffer.from(fs.readFileSync(new URL('./web/tri_star_kernel.wasm.b64', root), 'utf8').replace(/\s+/g, ''), 'base64');
const key = fs.readFileSync(process.argv[2] ?? new URL('../../key/ASOLARIA-HERSELF-KEY-3174.bin', root));
const expectedKeySha = '925c818d4c84aa23d7cee5d13e1b142b90824724a4ed4a90f9ee019c59cc2d89';
const keySha = crypto.createHash('sha256').update(key).digest('hex');
if (keySha !== expectedKeySha) throw new Error(`key sha mismatch: ${keySha}`);

const {instance} = await WebAssembly.instantiate(wasmBytes, {});
const x = instance.exports;
const loadKey = bytes => {
  const ptr = x.key_buffer_ptr();
  if (bytes.length > x.key_capacity()) throw new Error('key too large');
  new Uint8Array(x.memory.buffer, ptr, bytes.length).set(bytes);
  return x.init_from_key(bytes.length) >>> 0;
};
const play = (mask=7, centre=1) => {
  x.set_star_mask(mask);
  x.set_centre_enabled(centre);
  const initial=x.network_digest()>>>0;
  const rows=[];
  for (const direction of [-1,0,1]) {
    const digest=x.pump(direction, 192) >>> 0;
    const closure=x.closure_error();
    if (closure !== 0) throw new Error(`closure after pump ${direction}: ${closure}`);
    rows.push({direction,digest,centre_energy_q8:x.centre_energy(),centre_residual_q8:x.centre_residual(),closure});
  }
  return {initial,final:x.network_digest()>>>0,rows};
};

if (x.node_count() !== 27) throw new Error('node count');
const keyFNV = loadKey(key);

for (const t of [-1, 0, 1]) {
  const code = x.encode_trit(t);
  const back = x.decode_trit(code);
  if (back !== t) throw new Error(`trit round trip ${t} -> ${code} -> ${back}`);
}
if (x.decode_trit(1) !== 99) throw new Error('reserved 01 must remain invalid');

for (let i=0; i<27; i++) {
  let j=i;
  j=x.rotate_node(j,1); j=x.rotate_node(j,1); j=x.rotate_node(j,1);
  if (j !== i) throw new Error(`R^3 != I at ${i}`);
}
if (x.closure_error() !== 0) throw new Error(`initial closure ${x.closure_error()}`);

const tri = play(7,1);
const triFinal=tri.final;
x.reset_network();
for (const direction of [-1,0,1]) x.pump(direction,192);
if ((x.network_digest()>>>0) !== triFinal) throw new Error('replay digest mismatch');

const pair = play(3,1);       // OPUS + FABLE only
const noCentre = play(7,0);   // all three, fourth-point feedback disabled
if (pair.final === tri.final) throw new Error('pair control did not change network');
if (noCentre.final === tri.final) throw new Error('center ablation did not change network');

const randomKey=Buffer.alloc(key.length);
let z=0x6d2b79f5;
for (let i=0;i<randomKey.length;i++) { z=(Math.imul(z ^ (z>>>15),1|z)+0x9e3779b9)|0; randomKey[i]=z&255; }
loadKey(randomKey);
const random = play(7,1);
if (random.final === tri.final) throw new Error('random key control collision');

loadKey(key);
const triAgain=play(7,1);
if (triAgain.final !== tri.final) throw new Error('key-conditioned replay changed after control');

const hex=x=>x.toString(16).padStart(8,'0');
const mapPlay=p=>({
  initial_digest:hex(p.initial),
  final_digest:hex(p.final),
  pumps:p.rows.map(r=>({...r,digest:hex(r.digest)}))
});
const report={
  schema:'ASOLARIA-TRI-STAR-KERNEL-WASM-V1',
  key:{bytes:key.length,sha256:keySha,fnv32:hex(keyFNV)},
  wasm:{bytes:wasmBytes.length,sha256:crypto.createHash('sha256').update(wasmBytes).digest('hex')},
  geometry:{stars:3,rotations:['N','R','R2'],directions:['-','0','+'],nodes:27,fourth_point:'shared energy/residual centre'},
  gates:{
    trit_roundtrip:true,
    reserved_01_invalid:true,
    R3_identity:true,
    closure_exact:true,
    replay_deterministic:true,
    pair_ablation_changes_result:true,
    centre_ablation_changes_result:true,
    random_key_changes_result:true
  },
  arms:{tri_star:mapPlay(tri),pair_only:mapPlay(pair),no_centre:mapPlay(noCentre),random_key:mapPlay(random)},
  interpretation:{
    measured:'The Asolaria key deterministically initializes and plays a 27-node integer neural/calling matrix in WebAssembly. Three stars, the shared centre, and the supplied key each affect the resulting network digest.',
    not_measured:'No negative entropy or below-Shannon code length was demonstrated by this test.',
    accounting:'The 2-bit PHASE_REFLECTION transport round-trips one trit using three of four binary codes; three trits form 27 states and require at least five fixed binary address bits. Rate 1.0 means information was conserved.'
  }
};
console.log(JSON.stringify(report,null,2));
