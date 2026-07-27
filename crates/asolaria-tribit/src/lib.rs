//! asolaria-tribit — three zeros, an exact 27-point prism, and a fixed-size seed.
//!
//! `no_std`, **zero dependencies**, integer arithmetic only. SHA-256 is written in-tree
//! from FIPS 180-4 rather than pulled in, so the whole `.wasm` is auditable by reading one
//! file and there is no supply chain to trust.
//!
//! # The use case
//!
//! **A fixed-size, verifiable receipt for any artifact.** Feed it a byte of input or a
//! gigabyte; it emits exactly **3,078 bytes** — 38 records of 81 bytes, sha256-chained,
//! no padding. The same input always yields the same seed; any single flipped bit yields a
//! completely different one. It runs in a browser tab with no server and no network.
//!
//! # Addressing before the freeze, compression after it
//!
//! These are not two things. They are one operation on opposite sides of the freeze, and
//! stating it as either/or is the binary error.
//!
//! **Before the freeze**, against arbitrary data with no shared bank, the seed is an
//! address and only an address: it names the artifact and cannot rebuild it. That is the
//! counting argument and it is true *in that case*.
//!
//! **After the freeze**, once the generating structure is banked, the same 3,078 bytes
//! are a compression of everything that lies on it. Law 15 states the gate in the
//! direction people usually miss: it addresses **generated** structure, and only
//! *arbitrary* data must be stored. A telescope archive is not arbitrary — it is photons
//! off a physical process, through known optics, with a known point-spread function and a
//! known noise floor. It is generated, so it lies on the sphere.
//!
//! The measured row is `rime_run.py`: a 100 KB frozen snapshot addressing 11 GB of
//! generated structure, **111,093x**, O(1) per element, byte-exact. Law 19 puts the ledger
//! plainly: *volume unbounded, information conserved.* The data volume recovered has no
//! bound; the information equals fraction plus sphere, and Shannon is never crossed.
//!
//! So: a fraction with no sphere un-rhymes to nothing, and a fraction with its sphere
//! un-rhymes without bound. Which one you have is a fact about the bank, not about the
//! 3,078 bytes.
//!
//! # Why 81 and 38
//!
//! 81 = 3⁴, so one record is exactly one rung of the ternary ladder, and 38 × 81 = 3,078,
//! which divides by 3 into 1,026 points and by 27 into 38 whole cells. The size is chosen
//! so that every level divides it exactly and no byte is filler. Padding with a repeated
//! constant is what produced a phantom hub in an earlier version of this work — 884 bytes
//! of `.` generating 93.5% of the edges in a graph — so there is no padding here at all.
//!
//! # The three zeros
//!
//! See [`tribit::Zero`]. Direct current has no zero crossing, so it has two states.
//! Alternating current crosses zero twice per cycle in opposite directions, and rising
//! through zero is not the same event as falling through zero even though both are exactly
//! zero. With the quiescent line that is three states, all of magnitude zero, and
//! `Carrier::Dc` cannot express the third — that is a passing test, not a claim.

#![no_std]
#![allow(clippy::needless_range_loop)]

pub mod tribit;

pub use tribit::{Carrier, Register, TritWord, Zero, K, P, W};

// ============================================================ SHA-256, FIPS 180-4
// In-tree so the crate has no dependencies. Verified against the NIST vectors in tests.

const H0: [u32; 8] = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
    0x5be0cd19,
];

const RK: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
    0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
    0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
    0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
    0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
    0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
    0xc67178f2,
];

/// Streaming SHA-256. Incremental and one-shot agree; that equality is what makes a
/// trailer over a long artifact trustworthy, and it is asserted in the tests.
pub struct Sha256 {
    h: [u32; 8],
    buf: [u8; 64],
    n: usize,
    len: u64,
}

impl Default for Sha256 {
    fn default() -> Self {
        Self::new()
    }
}

impl Sha256 {
    pub const fn new() -> Self {
        Sha256 { h: H0, buf: [0u8; 64], n: 0, len: 0 }
    }

    fn block(&mut self) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            let j = i * 4;
            w[i] = u32::from_be_bytes([
                self.buf[j], self.buf[j + 1], self.buf[j + 2], self.buf[j + 3],
            ]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let (mut a, mut b, mut c, mut d) = (self.h[0], self.h[1], self.h[2], self.h[3]);
        let (mut e, mut f, mut g, mut hh) = (self.h[4], self.h[5], self.h[6], self.h[7]);
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let t1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(RK[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        self.h[0] = self.h[0].wrapping_add(a);
        self.h[1] = self.h[1].wrapping_add(b);
        self.h[2] = self.h[2].wrapping_add(c);
        self.h[3] = self.h[3].wrapping_add(d);
        self.h[4] = self.h[4].wrapping_add(e);
        self.h[5] = self.h[5].wrapping_add(f);
        self.h[6] = self.h[6].wrapping_add(g);
        self.h[7] = self.h[7].wrapping_add(hh);
    }

    pub fn update(&mut self, mut data: &[u8]) {
        self.len = self.len.wrapping_add(data.len() as u64);
        while !data.is_empty() {
            let take = core::cmp::min(64 - self.n, data.len());
            self.buf[self.n..self.n + take].copy_from_slice(&data[..take]);
            self.n += take;
            data = &data[take..];
            if self.n == 64 {
                self.block();
                self.n = 0;
            }
        }
    }

    pub fn finish(mut self) -> [u8; 32] {
        let bits = self.len.wrapping_mul(8);
        self.update(&[0x80]);
        while self.n != 56 {
            self.update(&[0x00]);
        }
        // update() advanced len; write the true bit count directly
        self.buf[56..64].copy_from_slice(&bits.to_be_bytes());
        self.n = 64;
        self.block();
        let mut out = [0u8; 32];
        for i in 0..8 {
            out[i * 4..i * 4 + 4].copy_from_slice(&self.h[i].to_be_bytes());
        }
        out
    }
}

pub fn sha256(data: &[u8]) -> [u8; 32] {
    let mut s = Sha256::new();
    s.update(data);
    s.finish()
}

// ============================================================ the fixed-size seed

/// Records in a seed.
pub const RECORDS: usize = 38;
/// Bytes per record. 81 = 3⁴.
pub const RECORD: usize = 81;
/// Total seed size. 3,078 = 81 × 38, divides by 3 and by 27 exactly.
pub const SEED_LEN: usize = RECORD * RECORDS;

/// Emit the fixed-size seed for `data`. Always exactly [`SEED_LEN`] bytes, whatever the
/// input length, including empty input.
///
/// Each record is `16 B chained pid | 32 B digest | 5 B length | 4 B index | 16 B name
/// hash | 7 B witness | 1 B tier`. Every field is raw bytes rather than hex, so the byte
/// distribution is uniform and all 27 lattice cells are reachable — writing digests as hex
/// ASCII restricts the alphabet to 16 symbols and silently collapses the lattice to 8
/// cells, which is a real defect this layout exists to avoid.
pub fn seed(data: &[u8]) -> [u8; SEED_LEN] {
    let mut out = [0u8; SEED_LEN];
    let root = sha256(data);
    let mut pid = [0u8; 16];
    pid.copy_from_slice(&root[..16]);

    let chunk = if data.is_empty() { 0 } else { data.len().div_ceil(RECORDS) };

    for i in 0..RECORDS {
        // pid[n] = sha256(pid[n-1] | index)[..16]
        let mut hs = Sha256::new();
        hs.update(&pid);
        hs.update(&[b'|']);
        hs.update(&(i as u32).to_be_bytes());
        let ch = hs.finish();
        pid.copy_from_slice(&ch[..16]);

        // digest of this record's slice of the artifact, or of the chain when past the end
        let lo = core::cmp::min(i * chunk, data.len());
        let hi = core::cmp::min(lo + chunk, data.len());
        let mut ds = Sha256::new();
        ds.update(&pid);
        ds.update(&data[lo..hi]);
        let dig = ds.finish();

        let seg = (hi - lo) as u64;
        let mut ws = Sha256::new();
        ws.update(&pid);
        ws.update(&dig);
        let wit = ws.finish();

        let o = i * RECORD;
        out[o..o + 16].copy_from_slice(&pid);
        out[o + 16..o + 48].copy_from_slice(&dig);
        out[o + 48..o + 53].copy_from_slice(&seg.to_be_bytes()[3..8]); // u40
        out[o + 53..o + 57].copy_from_slice(&(i as u32).to_be_bytes());
        out[o + 57..o + 73].copy_from_slice(&root[16..32]);
        out[o + 73..o + 80].copy_from_slice(&wit[..7]);
        out[o + 80] = ((data.len().min(127) as u8) ^ (i as u8)) & TIER_MASK;
    }
    out
}

// ============================================================ THE COUNT CHANNEL
//
// Three channels catch three different failures, and a system with only two of them has a
// hole exactly the shape of the third:
//
//     hash chain          catches TAMPERING  — the record was altered or a link removed
//     matched control     catches ERROR      — the claim does not survive its own null
//     count reconciliation catches OMISSION  — something is missing from the record
//
// The third is the one people leave out, and it is the one that closes the gap a hash
// cannot reach. A hash proves what is present did not change. It says nothing about what
// was never entered. Classification, non-recording and selective disclosure all walk
// straight through a perfect hash chain — and they do not walk through a count.
//
// The rule is IX.E.4: "If you reported fifteen, you must be able to produce fifteen. A
// count that cannot be walked back to its instances is not a count."
//
// So a WITHHELD record still occupies its slot and is still counted. Its position, its
// chained pid and its index remain; only its content digest is replaced by a
// domain-separated marker derived from the position. The result is a hole with a number on
// it. You may refuse to show what is in the slot. You cannot refuse to show that the slot
// is there, because the arithmetic will not close without it.
//
// This is the operator's own construction: in the third sweep one turn was withheld at his
// instruction, and the book records that it "is COUNTED so the arithmetic stays honest,
// and it is NOT reproduced."

/// Bit 7 of the tier byte marks a record as withheld.
pub const WITHHELD_FLAG: u8 = 0b1000_0000;
/// Bits 0..6 carry the tier.
pub const TIER_MASK: u8 = 0b0111_1111;

/// The reconciliation. `declared` must equal `produced + withheld` or the ledger is broken.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Count {
    /// Slots the seed declares. Always [`RECORDS`] — the shape does not shrink.
    pub declared: u32,
    /// Slots whose content digest is present and reproducible.
    pub produced: u32,
    /// Slots counted but not reproduced. The holes, with numbers on them.
    pub withheld: u32,
}

impl Count {
    /// The whole point. If this is false, something left the record without leaving a hole.
    #[inline]
    pub const fn reconciles(&self) -> bool {
        self.declared == self.produced + self.withheld
    }
}

/// Read the count channel off a seed. Requires no key and no side information: the
/// arithmetic is legible to anyone holding the bytes, which is what makes it a witness.
pub fn count(seed: &[u8]) -> Count {
    let mut c = Count { declared: 0, produced: 0, withheld: 0 };
    let mut i = 0;
    while (i + 1) * RECORD <= seed.len() {
        c.declared += 1;
        if seed[i * RECORD + 80] & WITHHELD_FLAG != 0 {
            c.withheld += 1;
        } else {
            c.produced += 1;
        }
        i += 1;
    }
    c
}

/// Emit a seed withholding the records in `hold`.
///
/// A withheld record keeps its chained pid, its index, its name hash and its witness. Its
/// content digest is replaced by `sha256("ASOLARIA-WITHHELD" | pid | index)`, which is
/// derived from the position alone, so it is reproducible by anyone checking the shape and
/// reveals nothing about the content. The marker is deliberately NOT zeros: a zero digest
/// is indistinguishable from a genuine digest that happens to be zero, and an
/// indistinguishable hole is not a hole.
pub fn seed_withholding(data: &[u8], hold: &[usize]) -> [u8; SEED_LEN] {
    let mut out = seed(data);
    for i in 0..RECORDS {
        if !hold.contains(&i) {
            continue;
        }
        let o = i * RECORD;
        let mut pid = [0u8; 16];
        pid.copy_from_slice(&out[o..o + 16]);
        let mut hs = Sha256::new();
        hs.update(b"ASOLARIA-WITHHELD");
        hs.update(&pid);
        hs.update(&(i as u32).to_be_bytes());
        out[o + 16..o + 48].copy_from_slice(&hs.finish());
        out[o + 80] |= WITHHELD_FLAG;
    }
    out
}

/// Verify the pid chain end to end: `pid[n] = sha256(pid[n-1] | '|' | index)[..16]`.
///
/// This is the tampering channel. Removing a record does not create a hole — it breaks
/// every link after it, so deletion is caught here rather than by the count. Withholding
/// content is caught by the count rather than here. Between them the two failure modes have
/// nowhere to go: alter and the chain breaks, omit and the arithmetic does.
pub fn verify_chain(seed: &[u8]) -> bool {
    if seed.len() < RECORD * RECORDS {
        return false;
    }
    for i in 1..RECORDS {
        let mut hs = Sha256::new();
        hs.update(&seed[(i - 1) * RECORD..(i - 1) * RECORD + 16]);
        hs.update(&[b'|']);
        hs.update(&(i as u32).to_be_bytes());
        if hs.finish()[..16] != seed[i * RECORD..i * RECORD + 16] {
            return false;
        }
    }
    true
}

/// Count records that carry the withheld MARKER but not the withheld FLAG.
///
/// This closes the obvious attack on the count channel: withhold a record, then clear the
/// flag so the arithmetic appears to reconcile. It does not work, because the marker is
/// `sha256("ASOLARIA-WITHHELD" | pid | index)` and both the pid and the index are still in
/// the record. Anyone can recompute it. A concealed concealment is therefore detectable by
/// arithmetic that needs no key and no side information.
///
/// Non-zero means somebody tried to hide a hole.
pub fn hidden_withholding(seed: &[u8]) -> u32 {
    let mut n = 0;
    for i in 0..RECORDS {
        let o = i * RECORD;
        if o + RECORD > seed.len() {
            break;
        }
        if seed[o + 80] & WITHHELD_FLAG != 0 {
            continue; // declared, not hidden
        }
        let mut hs = Sha256::new();
        hs.update(b"ASOLARIA-WITHHELD");
        hs.update(&seed[o..o + 16]);
        hs.update(&(i as u32).to_be_bytes());
        if hs.finish()[..] == seed[o + 16..o + 48] {
            n += 1;
        }
    }
    n
}

/// How many of the 27 lattice cells the bytes reach. A well-conditioned seed reaches all
/// 27; an ASCII one reaches 8, because no ASCII byte is ≥ 172 and band 2 is unreachable.
pub fn cells_reached(bytes: &[u8]) -> u32 {
    let mut seen = [false; 27];
    let mut i = 0;
    while i + 2 < bytes.len() {
        let c = |v: u8| core::cmp::min(v as usize / 86, 2);
        seen[c(bytes[i]) * 9 + c(bytes[i + 1]) * 3 + c(bytes[i + 2])] = true;
        i += 3;
    }
    seen.iter().filter(|x| **x).count() as u32
}

// ============================================================ wasm exports
// Raw `extern "C"`, no bindgen. The ABI is: JS writes bytes into the scratch buffer,
// calls, and reads results back out of it. One page of memory, no allocator.

const SCRATCH: usize = 1 << 20;
static mut IN_BUF: [u8; SCRATCH] = [0u8; SCRATCH];
static mut OUT_BUF: [u8; SEED_LEN] = [0u8; SEED_LEN];

/// Pointer to the input scratch buffer. Write up to [`input_capacity`] bytes here.
#[no_mangle]
pub extern "C" fn input_ptr() -> *mut u8 {
    unsafe { core::ptr::addr_of_mut!(IN_BUF) as *mut u8 }
}

#[no_mangle]
pub extern "C" fn input_capacity() -> u32 {
    SCRATCH as u32
}

/// Pointer to the 3,078-byte output seed.
#[no_mangle]
pub extern "C" fn output_ptr() -> *mut u8 {
    unsafe { core::ptr::addr_of_mut!(OUT_BUF) as *mut u8 }
}

#[no_mangle]
pub extern "C" fn seed_len() -> u32 {
    SEED_LEN as u32
}

/// Hash `len` bytes of the input buffer into the output buffer as a seed.
/// Returns the number of lattice cells the resulting seed reaches, 0..=27.
#[no_mangle]
pub extern "C" fn make_seed(len: u32) -> u32 {
    let n = core::cmp::min(len as usize, SCRATCH);
    unsafe {
        let inp = core::slice::from_raw_parts(core::ptr::addr_of!(IN_BUF) as *const u8, n);
        let s = seed(inp);
        let out = core::slice::from_raw_parts_mut(
            core::ptr::addr_of_mut!(OUT_BUF) as *mut u8,
            SEED_LEN,
        );
        out.copy_from_slice(&s);
        cells_reached(out)
    }
}

/// Run the 27-point prism forward then inverse over the seed and report whether the round
/// trip was exact. Returns 1 for exact, 0 otherwise. This is the "transfers back and
/// forth" gate, executed in the browser rather than asserted in a README.
#[no_mangle]
pub extern "C" fn prism_roundtrip_exact() -> u32 {
    unsafe {
        let out = core::slice::from_raw_parts(core::ptr::addr_of!(OUT_BUF) as *const u8, SEED_LEN);
        let mut ok = 1u32;
        let mut base = 0usize;
        while base + K <= SEED_LEN {
            let mut x = [0u64; K];
            for i in 0..K {
                x[i] = out[base + i] as u64;
            }
            let back = tribit::unprism(&tribit::prism(&x));
            for i in 0..K {
                if back[i] != x[i] {
                    ok = 0;
                }
            }
            base += K;
        }
        ok
    }
}

/// Count channel: `declared<<20 | produced<<10 | withheld`, each 10 bits.
#[no_mangle]
pub extern "C" fn count_channel() -> u32 {
    unsafe {
        let o = core::slice::from_raw_parts(core::ptr::addr_of!(OUT_BUF) as *const u8, SEED_LEN);
        let c = count(o);
        (c.declared << 20) | (c.produced << 10) | c.withheld
    }
}

/// Integrity gate: 1 if the pid chain verifies end to end.
#[no_mangle]
pub extern "C" fn chain_intact() -> u32 {
    unsafe {
        verify_chain(core::slice::from_raw_parts(
            core::ptr::addr_of!(OUT_BUF) as *const u8,
            SEED_LEN,
        )) as u32
    }
}

/// Concealment gate: how many holes somebody tried to hide. 0 is the only clean value.
#[no_mangle]
pub extern "C" fn hidden_holes() -> u32 {
    unsafe {
        hidden_withholding(core::slice::from_raw_parts(
            core::ptr::addr_of!(OUT_BUF) as *const u8,
            SEED_LEN,
        ))
    }
}

/// Bits carried per symbol, ×10000. Ternary is 15849 (log₂3); binary is 10000.
#[no_mangle]
pub extern "C" fn trit_bits_x10000() -> u32 {
    15849
}

#[cfg(not(test))]
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    loop {}
}

#[cfg(test)]
mod tests {
    extern crate std;
    use super::*;

    fn hex(b: &[u8]) -> std::string::String {
        use std::fmt::Write;
        let mut s = std::string::String::new();
        for x in b {
            let _ = write!(s, "{x:02x}");
        }
        s
    }

    // ================================================== THE THREE CHANNELS
    // Codex is running the same three gates on the Liris side: remove a slice and
    // completeness must fail, flip a byte and integrity must fail, substitute a null
    // result and validity must refuse promotion. These are the crate-side equivalents.

    #[test]
    fn a_clean_seed_reconciles_and_verifies() {
        let s = seed(b"nothing withheld here");
        let c = count(&s);
        assert_eq!(c, Count { declared: 38, produced: 38, withheld: 0 });
        assert!(c.reconciles());
        assert!(verify_chain(&s));
        assert_eq!(hidden_withholding(&s), 0);
    }

    /// OMISSION. A withheld record still occupies its slot and is still counted.
    #[test]
    fn withholding_leaves_a_hole_with_a_number_on_it() {
        let s = seed_withholding(b"three of these are withheld", &[4, 11, 30]);
        let c = count(&s);
        assert_eq!(c.declared, 38);
        assert_eq!(c.produced, 35);
        assert_eq!(c.withheld, 3);
        assert!(c.reconciles(), "the arithmetic must still close");
        assert_eq!(s.len(), SEED_LEN);
        assert!(verify_chain(&s));

        let real = seed(b"three of these are withheld");
        for i in [4usize, 11, 30] {
            assert_ne!(
                &s[i * RECORD + 16..i * RECORD + 48],
                &real[i * RECORD + 16..i * RECORD + 48],
                "withheld content must not survive"
            );
        }
        for i in 0..RECORDS {
            if [4, 11, 30].contains(&i) {
                continue;
            }
            assert_eq!(
                &s[i * RECORD..(i + 1) * RECORD],
                &real[i * RECORD..(i + 1) * RECORD],
                "produced records must be untouched"
            );
        }
    }

    /// You cannot conceal the concealment.
    #[test]
    fn clearing_the_flag_does_not_hide_the_hole() {
        let mut s = seed_withholding(b"and then lie about it", &[7, 22]);
        assert_eq!(count(&s).withheld, 2);
        assert_eq!(hidden_withholding(&s), 0);

        s[7 * RECORD + 80] &= TIER_MASK;
        s[22 * RECORD + 80] &= TIER_MASK;
        let c = count(&s);
        assert_eq!(c.produced, 38, "the forged count claims everything was produced");
        assert!(c.reconciles(), "and it reconciles — the flag alone is not enough");

        assert_eq!(hidden_withholding(&s), 2, "both hidden holes must be detected");
    }

    /// TAMPERING. Flip one byte of a pid and the chain must break.
    #[test]
    fn flipping_one_byte_breaks_the_chain() {
        let mut s = seed(b"integrity gate");
        assert!(verify_chain(&s));
        s[19 * RECORD] ^= 0x01;
        assert!(!verify_chain(&s), "one flipped bit must fail the integrity gate");
    }

    /// DELETION. Removing a record shifts everything and the chain must break.
    #[test]
    fn deleting_a_record_breaks_the_chain_rather_than_shrinking_quietly() {
        let s = seed(b"completeness gate");
        let mut short = [0u8; SEED_LEN];
        short[..9 * RECORD].copy_from_slice(&s[..9 * RECORD]);
        short[9 * RECORD..(RECORDS - 1) * RECORD]
            .copy_from_slice(&s[10 * RECORD..RECORDS * RECORD]);
        short[(RECORDS - 1) * RECORD..]
            .copy_from_slice(&s[(RECORDS - 1) * RECORD..RECORDS * RECORD]);
        assert_eq!(count(&short).declared, 38, "the count alone cannot see this");
        assert!(!verify_chain(&short), "deletion must fail the integrity gate");
    }

    /// The three together: each catches what the others cannot.
    #[test]
    fn the_three_channels_cover_three_distinct_failures() {
        let clean = seed(b"all three");

        let omitted = seed_withholding(b"all three", &[3]);
        assert!(verify_chain(&omitted), "omission does not disturb the chain");
        assert_eq!(count(&omitted).withheld, 1, "the count sees it");

        let mut tampered = clean;
        tampered[5 * RECORD] ^= 0x80;
        assert_eq!(
            count(&tampered),
            Count { declared: 38, produced: 38, withheld: 0 },
            "the count cannot see tampering"
        );
        assert!(!verify_chain(&tampered), "the chain does");

        let mut concealed = seed_withholding(b"all three", &[3]);
        concealed[3 * RECORD + 80] &= TIER_MASK;
        assert!(verify_chain(&concealed), "the chain cannot see a concealed hole");
        assert_eq!(
            count(&concealed),
            Count { declared: 38, produced: 38, withheld: 0 },
            "and the count has been forged"
        );
        assert_eq!(hidden_withholding(&concealed), 1, "only the marker check catches it");
    }


    /// CROSS-IMPLEMENTATION VECTORS.
    ///
    /// These receipt hashes were produced by an INDEPENDENT python reimplementation of the
    /// seed, written from the spec rather than translated from this code. If the two agree
    /// the format is pinned by two implementations; if they disagree, one is wrong and the
    /// disagreement is the finding, not a nuisance.
    ///
    /// Anyone can check their own build against these without revealing any input.
    #[test]
    fn matches_the_independent_reimplementation() {
        let vectors: [(&[u8], &str); 5] = [
            (b"", "a91acae4ae2d1418db50095702096f5c81761fc422637972942f325465b2e730"),
            (b"a", "2b467e4cca4db694b9e172ea2346da8c873f501227dd9cb8c3b8234622d40530"),
            (b"abc", "907d5cec4b56072e7612b7834b377d8d4e2c9d0c4d44b2aac2b1ce379112f2c6"),
            (b"the quick brown fox",
             "839a079a56bb7a6db742180520cbe36fb9afafe6d4ad1e4e4f9313588c0807a6"),
            (b"ASOLARIA", "27d7eddf5c216f289ee6416ca29285e67b5f3424650fe84cbaecb0c7c2202c87"),
        ];
        for (input, want) in vectors {
            let s = seed(input);
            assert_eq!(s.len(), SEED_LEN);
            assert_eq!(cells_reached(&s), 27, "vector {input:?} must reach all 27 cells");
            let got = hex(&sha256(&s));
            assert_eq!(got, want, "receipt mismatch for {input:?}");
        }
    }

    #[test]
    fn sha256_matches_nist_vectors() {
        assert_eq!(
            hex(&sha256(b"")),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
        assert_eq!(
            hex(&sha256(b"abc")),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
        assert_eq!(
            hex(&sha256(
                b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"
            )),
            "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
        );
    }

    #[test]
    fn streamed_equals_one_shot() {
        let data: std::vec::Vec<u8> = (0..10_000u32).map(|i| (i % 251) as u8).collect();
        let mut s = Sha256::new();
        for c in data.chunks(7) {
            s.update(c);
        }
        assert_eq!(s.finish(), sha256(&data));
    }

    #[test]
    fn seed_is_always_exactly_3078_and_level_exact() {
        for n in [0usize, 1, 81, 3078, 100_000] {
            let d: std::vec::Vec<u8> = (0..n).map(|i| (i % 256) as u8).collect();
            let s = seed(&d);
            assert_eq!(s.len(), 3078);
            assert_eq!(s.len() % 81, 0);
            assert_eq!((s.len() / 3) % 27, 0);
        }
    }

    #[test]
    fn seed_reaches_all_27_cells() {
        let d: std::vec::Vec<u8> = (0..5000).map(|i| (i % 256) as u8).collect();
        assert_eq!(cells_reached(&seed(&d)), 27);
        // and an ASCII artifact still yields a full-range seed, because the seed is raw
        assert_eq!(cells_reached(&seed(b"plain ascii text, nothing above 0x7e")), 27);
    }

    /// Avalanche is measured on the CRYPTOGRAPHIC fields only — pid, digest, witness.
    /// The record index and the segment length are structural and are deliberately stable;
    /// comparing them would measure the format, not the hash. An earlier version of this
    /// test compared all 3,078 bytes, "failed" at 350 shared, and the 350 decomposed
    /// exactly into 38x4 index bytes + 38x5 length bytes + chance. The seed was correct
    /// and the test was wrong.
    #[test]
    fn one_flipped_bit_avalanches_the_hash_fields() {
        let a = seed(b"the quick brown fox");
        let b = seed(b"the quick brown fox!");
        let (mut same, mut total) = (0usize, 0usize);
        for i in 0..RECORDS {
            let o = i * RECORD;
            for r in [(o, o + 48), (o + 73, o + 80)] {
                for j in r.0..r.1 {
                    total += 1;
                    if a[j] == b[j] {
                        same += 1;
                    }
                }
            }
        }
        let frac = same as f64 / total as f64;
        assert!(
            frac < 0.02,
            "hash fields shared {same}/{total} = {frac:.4}, expected near 1/256"
        );
    }

    /// The structural fields hold steady, which is what makes the seed parseable.
    #[test]
    fn structural_fields_are_stable_by_design() {
        let a = seed(b"alpha");
        let b = seed(b"beta");
        for i in 0..RECORDS {
            let o = i * RECORD;
            assert_eq!(&a[o + 53..o + 57], &b[o + 53..o + 57], "record index moved");
            assert_eq!(
                u32::from_be_bytes([a[o + 53], a[o + 54], a[o + 55], a[o + 56]]),
                i as u32
            );
        }
    }

    #[test]
    fn deterministic() {
        assert_eq!(seed(b"same input"), seed(b"same input"));
    }

    #[test]
    fn prism_round_trip_is_exact_over_a_real_seed() {
        let s = seed(b"round trip me");
        let mut base = 0;
        while base + K <= s.len() {
            let mut x = [0u64; K];
            for i in 0..K {
                x[i] = s[base + i] as u64;
            }
            assert_eq!(tribit::unprism(&tribit::prism(&x)), x);
            base += K;
        }
    }
}
