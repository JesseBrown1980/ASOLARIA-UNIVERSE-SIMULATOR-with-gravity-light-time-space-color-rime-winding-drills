const EXPECTED_KEY_SHA = '925c818d4c84aa23d7cee5d13e1b142b90824724a4ed4a90f9ee019c59cc2d89';
const KEY_URL = '../../../key/ASOLARIA-HERSELF-KEY-3174.bin';
const colors = ['#ff5f68', '#57d889', '#5f8dff'];
const labels = ['OPUS', 'FABLE', 'MYTHOS'];
const canvas = document.querySelector('#network');
const ctx = canvas.getContext('2d');
let wasm;
let keyBytes;

const hex = bytes => [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, '0')).join('');
const sha256 = async bytes => hex(await crypto.subtle.digest('SHA-256', bytes));
const fromBase64 = text => {
  const bin = atob(text.replace(/\s+/g, ''));
  return Uint8Array.from(bin, c => c.charCodeAt(0));
};

async function boot() {
  const [b64, keyResponse] = await Promise.all([
    fetch('tri_star_kernel.wasm.b64').then(r => { if (!r.ok) throw new Error('WASM base64 missing'); return r.text(); }),
    fetch(KEY_URL).then(r => { if (!r.ok) throw new Error('Asolaria key missing'); return r.arrayBuffer(); })
  ]);
  const wasmBytes = fromBase64(b64);
  keyBytes = new Uint8Array(keyResponse);
  const [keySha, wasmSha] = await Promise.all([sha256(keyBytes), sha256(wasmBytes)]);
  document.querySelector('#keySha').textContent = keySha.slice(0, 16);
  document.querySelector('#wasmSha').textContent = wasmSha.slice(0, 16);
  if (keySha !== EXPECTED_KEY_SHA) throw new Error(`Key SHA mismatch: ${keySha}`);

  ({instance: {exports: wasm}} = await WebAssembly.instantiate(wasmBytes, {}));
  if (keyBytes.length > wasm.key_capacity()) throw new Error('key larger than WASM buffer');
  new Uint8Array(wasm.memory.buffer, wasm.key_buffer_ptr(), keyBytes.length).set(keyBytes);
  wasm.init_from_key(keyBytes.length);

  const text = new TextDecoder().decode(keyBytes);
  document.querySelector('#header').textContent = text.split('\n').slice(0, 13).join('\n');
  bind();
  update();
}

function starMask() {
  return [...document.querySelectorAll('.star')].reduce((m, el) => m | (el.checked ? Number(el.dataset.bit) : 0), 0);
}

function applyConfig() {
  wasm.set_star_mask(starMask());
  wasm.set_centre_enabled(document.querySelector('#centre').checked ? 1 : 0);
}

function bind() {
  const calm = document.querySelector('#calm');
  calm.addEventListener('input', () => document.querySelector('#calmOut').textContent = `${Math.round(Number(calm.value) / 255 * 100)}%`);
  document.querySelector('#pumpMinus').onclick = () => pump(-1);
  document.querySelector('#pumpZero').onclick = () => pump(0);
  document.querySelector('#pumpPlus').onclick = () => pump(1);
  document.querySelector('#pumpThree').onclick = () => { pump(-1, false); pump(0, false); pump(1); };
  document.querySelector('#reset').onclick = () => { applyConfig(); update(); };
  document.querySelector('#centre').onchange = () => { wasm.set_centre_enabled(document.querySelector('#centre').checked ? 1 : 0); update(); };
  document.querySelectorAll('.star').forEach(el => el.onchange = () => { applyConfig(); update(); });
}

function pump(direction, redraw = true) {
  wasm.set_centre_enabled(document.querySelector('#centre').checked ? 1 : 0);
  wasm.pump(direction, Number(document.querySelector('#calm').value));
  if (redraw) update();
}

function nodePosition(i) {
  const star = wasm.node_star(i);
  const rotation = wasm.node_rotation(i);
  const direction = wasm.node_direction(i);
  const ring = 118 + star * 82;
  const slot = rotation * 3 + direction;
  const angle = -Math.PI / 2 + slot * (Math.PI * 2 / 9) + star * 0.055;
  return {x: canvas.width / 2 + Math.cos(angle) * ring, y: canvas.height / 2 + Math.sin(angle) * ring, star, rotation, direction};
}

function drawEdge(a, b, alpha = .12) {
  ctx.strokeStyle = `rgba(210,220,255,${alpha})`;
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
}

function update() {
  const nodes = Array.from({length: 27}, (_, i) => ({...nodePosition(i), i, value: wasm.node_value(i)}));
  const max = Math.max(1, ...nodes.map(n => Math.abs(n.value)));
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Callings: star, rotation, and direction neighbours.
  for (const n of nodes) {
    const s2 = nodes[((n.star + 1) % 3) * 9 + n.rotation * 3 + n.direction];
    const r2 = nodes[n.star * 9 + ((n.rotation + 1) % 3) * 3 + n.direction];
    const d2 = nodes[n.star * 9 + n.rotation * 3 + ((n.direction + 1) % 3)];
    drawEdge(n, s2, .07); drawEdge(n, r2, .12); drawEdge(n, d2, .16);
  }

  const e = wasm.centre_energy() / 256;
  const centreR = 25 + Math.min(40, Math.sqrt(Math.max(0, e)) * 2.8);
  const grad = ctx.createRadialGradient(380, 380, 0, 380, 380, centreR * 2.4);
  grad.addColorStop(0, 'rgba(255,255,255,.96)');
  grad.addColorStop(.23, 'rgba(210,220,255,.55)');
  grad.addColorStop(1, 'rgba(80,110,210,0)');
  ctx.fillStyle = grad; ctx.beginPath(); ctx.arc(380, 380, centreR * 2.4, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#07101e'; ctx.beginPath(); ctx.arc(380, 380, centreR, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#f5f7ff'; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.font = 'bold 18px system-ui'; ctx.fillText('E₀', 380, 386);

  for (const n of nodes) {
    const mag = Math.abs(n.value) / max;
    const radius = 7 + 11 * Math.sqrt(mag);
    ctx.globalAlpha = .35 + .65 * Math.sqrt(mag);
    ctx.fillStyle = Math.abs(n.value) < max * .025 ? '#adb5c6' : colors[n.star];
    ctx.strokeStyle = colors[n.star];
    ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
    if (n.value >= 0) ctx.fill(); else ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.fillStyle = '#e8ecf8'; ctx.font = '11px ui-monospace, monospace';
    const dir = ['−', '0', '+'][n.direction];
    ctx.fillText(`${labels[n.star][0]}${n.rotation}:${dir}`, n.x, n.y + radius + 13);
  }

  document.querySelector('#digest').textContent = (wasm.network_digest() >>> 0).toString(16).padStart(8, '0');
  document.querySelector('#pumps').textContent = wasm.pumps();
  document.querySelector('#energy').textContent = (wasm.centre_energy() / 256).toFixed(3);
  document.querySelector('#residual').textContent = (wasm.centre_residual() / 256).toFixed(3);
  document.querySelector('#closure').textContent = wasm.closure_error();
}

boot().catch(err => {
  console.error(err);
  document.querySelector('#header').textContent = `BOOT FAILED\n${err.stack ?? err}`;
});
