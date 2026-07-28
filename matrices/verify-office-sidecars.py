#!/usr/bin/env python3
"""verify-office-sidecars.py -- era-aware sidecar verifier for the FABLE5 office.

Walks the office recursively. For every *.hbp / *.hbi / *.html that has a
.sha256 sidecar, verifies with era rules:

  PASS_RAW     sha256(raw bytes on disk) == sidecar hash
  PASS_ERA_LF  sha256(CRLF->LF normalized bytes) == sidecar hash
               (the known 2026-07-02 cohort bug: hash was computed over
               LF-normalized content; file content is intact)
  FAIL         neither matches

Files with no sidecar are listed as NO_SIDECAR.

Pure stdlib. No writes except stdout. Exit 0 only if zero FAIL.
Usage: python verify-office-sidecars.py [office_root]
       (default office_root = directory containing this script)
"""

import hashlib
import os
import re
import sys

DATA_EXTS = (".hbp", ".hbi", ".html")
HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_sidecar_hash(sidecar_path):
    """Return the lowercase 64-hex hash from a sidecar, or None if unparseable."""
    try:
        with open(sidecar_path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    token = text.split()[0]
    if HEX_RE.match(token):
        return token.lower()
    return None


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        print("ERROR|office root not found: %s" % root)
        return 2

    rows = []           # (status, relpath, detail)
    counts = {"PASS_RAW": 0, "PASS_ERA_LF": 0, "FAIL": 0, "NO_SIDECAR": 0}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if not name.lower().endswith(DATA_EXTS):
                continue
            fpath = os.path.join(dirpath, name)
            rel = os.path.relpath(fpath, root).replace(os.sep, "/")
            sidecar = fpath + ".sha256"
            if not os.path.isfile(sidecar):
                counts["NO_SIDECAR"] += 1
                rows.append(("NO_SIDECAR", rel, ""))
                continue
            expected = read_sidecar_hash(sidecar)
            if expected is None:
                counts["FAIL"] += 1
                rows.append(("FAIL", rel, "sidecar unparseable"))
                continue
            try:
                with open(fpath, "rb") as fh:
                    raw = fh.read()
            except OSError as exc:
                counts["FAIL"] += 1
                rows.append(("FAIL", rel, "unreadable: %s" % exc))
                continue
            h_raw = sha256_bytes(raw)
            if h_raw == expected:
                counts["PASS_RAW"] += 1
                rows.append(("PASS_RAW", rel, ""))
                continue
            h_lf = sha256_bytes(raw.replace(b"\r\n", b"\n"))
            if h_lf == expected:
                counts["PASS_ERA_LF"] += 1
                rows.append(("PASS_ERA_LF", rel, ""))
                continue
            counts["FAIL"] += 1
            rows.append(("FAIL", rel, "expected=%s raw=%s lf=%s" % (expected, h_raw, h_lf)))

    for status, rel, detail in rows:
        if detail:
            print("%s|%s|%s" % (status, rel, detail))
        else:
            print("%s|%s" % (status, rel))

    total = sum(counts.values())
    print("SUMMARY|total=%d|pass_raw=%d|pass_era_lf=%d|fail=%d|no_sidecar=%d" % (
        total, counts["PASS_RAW"], counts["PASS_ERA_LF"], counts["FAIL"], counts["NO_SIDECAR"]))
    return 0 if counts["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
