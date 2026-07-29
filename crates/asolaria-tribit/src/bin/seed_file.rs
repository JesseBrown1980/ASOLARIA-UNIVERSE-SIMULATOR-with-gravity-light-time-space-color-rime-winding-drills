//! Native, fail-closed file front-end for the 3,078-byte Asolaria seed.
//!
//! The browser ABI has a deliberate 1 MiB scratch buffer. Large artifacts must not pass
//! through that ABI because `make_seed` clamps its input length. This binary reads the
//! complete file and calls the same audited library function without truncation.

use asolaria_tribit::{cells_reached, seed, SEED_LEN};
use std::env;
use std::fs;
use std::io::{self, Write};
use std::path::Path;

fn hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        out.push(DIGITS[(b >> 4) as usize] as char);
        out.push(DIGITS[(b & 0x0f) as usize] as char);
    }
    out
}

fn run() -> Result<(), String> {
    let mut args = env::args_os();
    let exe = args.next().unwrap_or_default();
    let input = args.next().ok_or_else(|| {
        format!(
            "usage: {} <complete-input-file> <seed-output-file>",
            Path::new(&exe).display()
        )
    })?;
    let output = args.next().ok_or_else(|| {
        format!(
            "usage: {} <complete-input-file> <seed-output-file>",
            Path::new(&exe).display()
        )
    })?;
    if args.next().is_some() {
        return Err("too many arguments".into());
    }

    let bytes =
        fs::read(&input).map_err(|e| format!("read {}: {e}", Path::new(&input).display()))?;
    let receipt = seed(&bytes);
    if receipt.len() != SEED_LEN {
        return Err(format!(
            "internal seed length mismatch: {} != {SEED_LEN}",
            receipt.len()
        ));
    }

    fs::write(&output, receipt)
        .map_err(|e| format!("write {}: {e}", Path::new(&output).display()))?;
    let reread =
        fs::read(&output).map_err(|e| format!("re-read {}: {e}", Path::new(&output).display()))?;
    if reread.as_slice() != receipt {
        return Err("seed re-read differs from emitted bytes".into());
    }

    let input_sha = asolaria_tribit::sha256(&bytes);
    let seed_sha = asolaria_tribit::sha256(&receipt);
    println!(
        "SEEDFILE|input_bytes={}|input_sha256={}|seed_bytes={}|seed_sha256={}|cells={}|complete_input=1|json=0",
        bytes.len(),
        hex(&input_sha),
        receipt.len(),
        hex(&seed_sha),
        cells_reached(&receipt)
    );
    Ok(())
}

fn main() {
    if let Err(message) = run() {
        let _ = writeln!(io::stderr(), "SEEDFILEERR|message={message}|json=0");
        std::process::exit(1);
    }
}
