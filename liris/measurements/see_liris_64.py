#!/usr/bin/env python3
"""Project LIRIS-owned bytes into an exact 64 x 64 x 64 colour matrix.

This is the LIRIS half of the cross-seat 64-cube experiment.  It deliberately
keeps three different statements separate:

* the input bytes and their SHA-256 digests are the authority surface;
* the 64^3 histogram and GGUF tensors are deterministic projections;
* the GPU image is a view of those tensors, never a replacement for them.

Every source starts on a fresh byte triple.  Concatenating two files before
forming triples would invent up to one RGB point at every boundary.

The four semantic ternary axes are also measured independently from RGB:

    position = time*27 + colour*9 + energy*3 + space

where each 81-byte record contains all 3^4 positions exactly once.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import math
import os
import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np


N = 64
VOXELS = N**3
ALIGN = 32
READ_BLOCK = 3 * 1024 * 1024

GGML_I16 = 25
GGML_I32 = 26
GGML_I64 = 27

V_UINT32 = 4
V_STRING = 8
V_ARRAY = 9
V_UINT64 = 10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def row(kind: str, **fields: object) -> str:
    return "|".join([kind, *(f"{key}={value}" for key, value in fields.items()), "json=0"])


def gguf_string(value: str) -> bytes:
    payload = value.encode("utf-8")
    return struct.pack("<Q", len(payload)) + payload


def gguf_kv(key: str, kind: int, payload: bytes) -> bytes:
    return gguf_string(key) + struct.pack("<I", kind) + payload


@dataclass(frozen=True)
class Source:
    path: Path
    size: int
    sha256: str


@dataclass
class Projection:
    cube: np.ndarray
    source_shells: np.ndarray
    semantic_sum: np.ndarray
    semantic_count: np.ndarray
    triples: int
    dropped_tail_bytes: int
    complete_records81: int


def collect_sources(items: list[Path]) -> list[Source]:
    paths: set[Path] = set()
    for item in items:
        resolved = item.resolve()
        if resolved.is_file():
            paths.add(resolved)
        elif resolved.is_dir():
            paths.update(path.resolve() for path in resolved.rglob("*") if path.is_file())
        else:
            raise FileNotFoundError(item)
    if not paths:
        raise ValueError("no source files")
    return [
        Source(path, path.stat().st_size, sha256_file(path))
        for path in sorted(paths, key=lambda value: value.as_posix().lower())
    ]


def byte_trits(values: np.ndarray) -> np.ndarray:
    """Three byte bands used by the existing 3,078-byte adversarial gate.

    The upper state starts at 172, matching the already-published defect test.
    """

    return np.where(values < 86, 0, np.where(values < 172, 1, 2)).astype(np.uint8)


def project(sources: list[Source]) -> Projection:
    cube = np.zeros((N, N, N), dtype=np.int64)
    source_shells = np.zeros(4, dtype=np.int64)
    semantic_sum = np.zeros((3, 3, 3, 3), dtype=np.int64)
    semantic_count = np.zeros((3, 3, 3, 3), dtype=np.int64)
    triples = 0
    dropped = 0
    records81 = 0

    for source in sources:
        # RGB triples: boundary reset is intentional and measured.
        remainder = b""
        with source.path.open("rb") as stream:
            while block := stream.read(READ_BLOCK):
                payload = remainder + block
                complete = len(payload) // 3 * 3
                if complete:
                    values = np.frombuffer(payload[:complete], dtype=np.uint8).reshape(-1, 3)
                    quantized = values >> 2
                    flat = (
                        quantized[:, 0].astype(np.int64) * (N * N)
                        + quantized[:, 1].astype(np.int64) * N
                        + quantized[:, 2].astype(np.int64)
                    )
                    cube += np.bincount(flat, minlength=VOXELS).reshape(N, N, N)

                    trits = byte_trits(values)
                    shell = (trits != 1).sum(axis=1)
                    source_shells += np.bincount(shell, minlength=4)
                    triples += len(values)
                remainder = payload[complete:]
        dropped += len(remainder)

        # Semantic 81: each source also starts a fresh record.
        remainder81 = b""
        position = np.arange(81, dtype=np.int64)
        state = np.stack(
            (
                position // 27,
                (position // 9) % 3,
                (position // 3) % 3,
                position % 3,
            ),
            axis=1,
        )
        with source.path.open("rb") as stream:
            while block := stream.read(READ_BLOCK):
                payload = remainder81 + block
                complete = len(payload) // 81 * 81
                if complete:
                    records = np.frombuffer(payload[:complete], dtype=np.uint8).reshape(-1, 81)
                    sums = records.sum(axis=0, dtype=np.int64)
                    count = records.shape[0]
                    semantic_sum[
                        state[:, 0], state[:, 1], state[:, 2], state[:, 3]
                    ] += sums
                    semantic_count[
                        state[:, 0], state[:, 1], state[:, 2], state[:, 3]
                    ] += count
                    records81 += count
                remainder81 = payload[complete:]

    return Projection(
        cube,
        source_shells,
        semantic_sum,
        semantic_count,
        triples,
        dropped,
        records81,
    )


def instrument_masks() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Match the already-published Acer/Mythos 64-cube instrument exactly.

    64 cannot divide into three equal integer-width bands.  The direct-comparison
    instrument uses q//22, capped at 2: widths 22, 22, 20.  The exact byte-trit
    census remains separately available in Projection.source_shells.
    """

    axis = np.minimum(np.arange(N) // 22, 2)
    t0, t1, t2 = np.meshgrid(axis, axis, axis, indexing="ij")
    shell = (t0 != 1).astype(np.int8) + (t1 != 1) + (t2 != 1)
    solid = (shell == 0) | (shell == 3)
    translucent = (shell == 1) | (shell == 2)
    return shell, solid, translucent


def radial_spectrum(plane: np.ndarray, bins: int = 32) -> np.ndarray:
    values = np.log1p(plane.astype(np.float64))
    values -= values.mean()
    power = np.abs(np.fft.fftshift(np.fft.fft2(values))) ** 2
    height, width = power.shape
    yy, xx = np.mgrid[0:height, 0:width]
    radius = np.sqrt((yy - height / 2.0) ** 2 + (xx - width / 2.0) ** 2)
    labels = np.minimum((radius / radius.max() * bins).astype(np.int64), bins - 1)
    total = np.bincount(labels.ravel(), weights=power.ravel(), minlength=bins)
    count = np.bincount(labels.ravel(), minlength=bins)
    spectrum = total / np.maximum(count, 1)
    norm = spectrum.sum()
    return spectrum / norm if norm else spectrum


def pearson(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64).ravel()
    b = np.asarray(right, dtype=np.float64).ravel()
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64).ravel()
    b = np.asarray(right, dtype=np.float64).ravel()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denom) if denom else float("nan")


def log_u16(values: np.ndarray) -> np.ndarray:
    scaled = np.log1p(values.astype(np.float64))
    maximum = scaled.max()
    if maximum:
        scaled *= 32767.0 / maximum
    return np.rint(scaled).astype(np.int16)


def tensor_bytes(array: np.ndarray, ggml_type: int) -> tuple[np.ndarray, bytes]:
    dtype = {GGML_I16: np.int16, GGML_I32: np.int32, GGML_I64: np.int64}[ggml_type]
    normalized = np.ascontiguousarray(array, dtype=dtype)
    return normalized, normalized.tobytes()


def write_gguf(
    path: Path,
    metadata: list[tuple[str, int, bytes]],
    tensors: list[tuple[str, np.ndarray, int]],
) -> tuple[int, str]:
    meta = b"".join(gguf_kv(key, kind, payload) for key, kind, payload in metadata)
    data = bytearray()
    descriptors = bytearray()

    for name, array, kind in tensors:
        normalized, payload = tensor_bytes(array, kind)
        data.extend(b"\0" * ((-len(data)) % ALIGN))
        offset = len(data)
        # GGUF ne[0] is the fastest-changing dimension; NumPy's last axis is fastest.
        dimensions = tuple(reversed(normalized.shape))
        descriptors.extend(gguf_string(name))
        descriptors.extend(struct.pack("<I", len(dimensions)))
        for dimension in dimensions:
            descriptors.extend(struct.pack("<Q", int(dimension)))
        descriptors.extend(struct.pack("<I", kind))
        descriptors.extend(struct.pack("<Q", offset))
        data.extend(payload)

    header = (
        struct.pack("<4sIQQ", b"GGUF", 3, len(tensors), len(metadata))
        + meta
        + bytes(descriptors)
    )
    header += b"\0" * ((-len(header)) % ALIGN)
    blob = header + bytes(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="ascii", newline="\n"
    )
    return len(blob), digest


def metadata_base(
    name: str,
    sources: list[Source],
    projection: Projection,
    centre: tuple[int, int, int],
    centre_mass: int,
    model_label: str,
) -> list[tuple[str, int, bytes]]:
    source_manifest = "\n".join(
        f"{source.path.as_posix()}|{source.size}|{source.sha256}" for source in sources
    ).encode("utf-8")
    return [
        ("general.architecture", V_STRING, gguf_string("asolaria-liris-matrix64")),
        ("general.name", V_STRING, gguf_string(name)),
        ("general.description", V_STRING, gguf_string("LIRIS byte-exact 64^3 projection")),
        ("asolaria.seat", V_STRING, gguf_string("LIRIS")),
        ("asolaria.evidence_class", V_STRING, gguf_string("LIRIS_LOCAL_MEASURED")),
        ("asolaria.model_label", V_STRING, gguf_string(model_label)),
        (
            "asolaria.model_boundary",
            V_STRING,
            gguf_string("public_self_seed_and_artifact_projection_not_model_weights"),
        ),
        ("asolaria.cube", V_UINT32, struct.pack("<I", N)),
        ("asolaria.source_count", V_UINT32, struct.pack("<I", len(sources))),
        (
            "asolaria.source_bytes",
            V_UINT64,
            struct.pack("<Q", sum(source.size for source in sources)),
        ),
        ("asolaria.source_manifest_sha256", V_STRING, gguf_string(hashlib.sha256(source_manifest).hexdigest())),
        ("asolaria.triples", V_UINT64, struct.pack("<Q", projection.triples)),
        ("asolaria.records81", V_UINT64, struct.pack("<Q", projection.complete_records81)),
        (
            "asolaria.largest_centre",
            V_ARRAY,
            struct.pack("<IQ", V_UINT32, 3)
            + b"".join(struct.pack("<I", value) for value in centre),
        ),
        ("asolaria.largest_centre_mass", V_UINT64, struct.pack("<Q", centre_mass)),
        (
            "asolaria.semantic_axes",
            V_ARRAY,
            struct.pack("<IQ", V_STRING, 4)
            + b"".join(gguf_string(value) for value in ("time", "colour", "energy", "space")),
        ),
        (
            "asolaria.energy_states",
            V_ARRAY,
            struct.pack("<IQ", V_STRING, 3)
            + b"".join(gguf_string(value) for value in ("light", "dc", "ac")),
        ),
        ("asolaria.tensor_signedness", V_STRING, gguf_string("I64 counts; I16 log views")),
    ]


def html_document(
    title: str,
    cube: np.ndarray,
    centre: tuple[int, int, int],
    stats: str,
) -> str:
    encoded = base64.b64encode(log_u16(cube).astype("<i2").tobytes()).decode("ascii")
    return f"""<!doctype html>
<meta charset="utf-8">
<title>{title}</title>
<style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#030611;color:#eaf4ff;
font:16px ui-monospace,Consolas,monospace}}canvas{{width:100%;height:100%;display:block}}
#hud{{position:fixed;left:22px;top:18px;padding:14px 16px;background:#030611c8;
border:1px solid #ffffff2b;white-space:pre;line-height:1.4;pointer-events:none}}
</style>
<canvas id="c"></canvas><div id="hud">LIRIS · loading exact 64³ projection</div>
<script>
const N=64, centre=[{centre[0]},{centre[1]},{centre[2]}];
const raw=Uint8Array.from(atob("{encoded}"),c=>c.charCodeAt(0));
const values=new Int16Array(raw.buffer);
const canvas=document.querySelector("#c");
const gl=canvas.getContext("webgl2",{{antialias:true,alpha:false,preserveDrawingBuffer:true}});
if(!gl) throw Error("WebGL2 unavailable");
const dbg=gl.getExtension("WEBGL_debug_renderer_info");
const renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
const points=[];
let max=1;
for(let i=0;i<values.length;i++) if(values[i]>max) max=values[i];
for(let r=0;r<N;r++)for(let g=0;g<N;g++)for(let b=0;b<N;b++){{
  const v=values[(r*N+g)*N+b]; if(v<=0)continue;
  const x=(r-31.5)/31.5,y=(g-31.5)/31.5,z=(b-31.5)/31.5;
  const sx=x*Math.sqrt(Math.max(0,1-y*y/2-z*z/2+y*y*z*z/3));
  const sy=y*Math.sqrt(Math.max(0,1-z*z/2-x*x/2+z*z*x*x/3));
  const sz=z*Math.sqrt(Math.max(0,1-x*x/2-y*y/2+x*x*y*y/3));
  points.push(sx,sy,sz,r/63,g/63,b/63,Math.sqrt(v/max));
}}
const vs=`#version 300 es
precision highp float;layout(location=0)in vec3 p;layout(location=1)in vec3 col;
layout(location=2)in float mass;uniform mat4 mvp;out vec4 c;
void main(){{gl_Position=mvp*vec4(p,1);gl_PointSize=1.5+5.5*mass;
c=vec4(mix(vec3(.08,.12,.18),col,.35+.65*mass),.22+.70*mass);}}`;
const fs=`#version 300 es
precision highp float;in vec4 c;out vec4 o;
void main(){{vec2 q=gl_PointCoord-.5;if(dot(q,q)>.25)discard;o=c;}}`;
function sh(t,s){{let x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);
if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}}
const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));
gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);gl.useProgram(pr);
const buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);
gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(points),gl.STATIC_DRAW);
const stride=7*4;gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,stride,0);
gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,3,gl.FLOAT,false,stride,12);
gl.enableVertexAttribArray(2);gl.vertexAttribPointer(2,1,gl.FLOAT,false,stride,24);
gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);gl.enable(gl.DEPTH_TEST);
const U=gl.getUniformLocation(pr,"mvp");
function mul(a,b){{let o=new Float32Array(16);for(let r=0;r<4;r++)for(let c=0;c<4;c++)
for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o}}
function rotY(a){{let c=Math.cos(a),s=Math.sin(a);return new Float32Array([c,0,-s,0,0,1,0,0,s,0,c,0,0,0,0,1])}}
function rotX(a){{let c=Math.cos(a),s=Math.sin(a);return new Float32Array([1,0,0,0,0,c,-s,0,0,s,c,0,0,0,0,1])}}
function perspective(aspect){{let f=1/Math.tan(.48),n=.1,far=10;return new Float32Array(
[f/aspect,0,0,0,0,f,0,0,0,0,(far+n)/(n-far),-1,0,0,2*far*n/(n-far),0])}}
function frame(ms){{let d=devicePixelRatio||1,w=Math.floor(innerWidth*d),h=Math.floor(innerHeight*d);
if(canvas.width!==w||canvas.height!==h){{canvas.width=w;canvas.height=h}}gl.viewport(0,0,w,h);
gl.clearColor(.008,.016,.045,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
let model=mul(rotY(ms*.00017),rotX(-.43+Math.sin(ms*.00011)*.15));
model[14]=-3.25;gl.uniformMatrix4fv(U,false,mul(perspective(w/h),model));
gl.drawArrays(gl.POINTS,0,points.length/7);requestAnimationFrame(frame)}}requestAnimationFrame(frame);
document.querySelector("#hud").textContent=`{title}\\n{stats}\\ncentre {centre}\\nGPU ${{renderer}}\\npoints ${{points.length/7}} · live spherical rotation`;
</script>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--name", default="ASOLARIA-LIRIS-CODEX-SEED-64")
    parser.add_argument("--model-label", default="gpt-5.6-sol")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    sources = collect_sources(args.input)
    projection = project(sources)
    cube = projection.cube
    shell, solid, translucent = instrument_masks()

    centre_candidates = np.where(shell == 0, cube, -1)
    centre = tuple(int(value) for value in np.unravel_index(int(np.argmax(centre_candidates)), cube.shape))
    centre_mass = int(cube[centre])
    occupied = int((cube > 0).sum())
    solid_mass = int(cube[solid].sum())
    translucent_mass = int(cube[translucent].sum())
    total_mass = int(cube.sum())

    axis = np.arange(N)
    rr, gg, bb = np.meshgrid(axis, axis, axis, indexing="ij")
    distance = np.sqrt(
        (rr - centre[0]) ** 2 + (gg - centre[1]) ** 2 + (bb - centre[2]) ** 2
    )
    radial = np.floor(distance).astype(np.int64)
    colours = ("RED", "GREEN", "BLUE")
    radial_rows: list[tuple[int, int, float, float, float, str, float]] = []
    for radius in range(32):
        mask = radial == radius
        mass = int(cube[mask].sum())
        if mass == 0:
            continue
        weights = cube[mask].astype(np.float64)
        means = (
            float((rr[mask] * weights).sum() / mass),
            float((gg[mask] * weights).sum() / mass),
            float((bb[mask] * weights).sum() / mass),
        )
        lead = colours[int(np.argmax(means))]
        solid_fraction = float(cube[mask & solid].sum() / mass)
        radial_rows.append((radius, mass, *means, lead, solid_fraction))

    planes = {
        "XY": cube.sum(axis=2),
        "YZ": cube.sum(axis=0),
        "ZX": cube.sum(axis=1).T,
    }
    spectra = {name: radial_spectrum(value) for name, value in planes.items()}

    base_metadata = metadata_base(
        args.name,
        sources,
        projection,
        centre,
        centre_mass,
        args.model_label,
    )
    outputs: list[tuple[str, Path, int, str]] = []
    cube_path = args.output_dir / f"{args.name}-CUBE.gguf"
    cube_bytes, cube_sha = write_gguf(
        cube_path,
        base_metadata
        + [
            ("asolaria.instrument_trit_widths", V_STRING, gguf_string("22,22,20")),
            ("asolaria.source_trit_thresholds", V_STRING, gguf_string("86,172")),
        ],
        [
            ("cube64_counts", cube, GGML_I64),
            ("solid_third_counts", np.where(solid, cube, 0), GGML_I64),
            (
                "translucent_two_thirds_counts",
                np.where(translucent, cube, 0),
                GGML_I64,
            ),
            ("cube64_log", log_u16(cube), GGML_I16),
            ("semantic81_sum", projection.semantic_sum, GGML_I64),
            ("semantic81_count", projection.semantic_count, GGML_I64),
        ],
    )
    outputs.append(("CUBE", cube_path, cube_bytes, cube_sha))

    for look, plane in planes.items():
        path = args.output_dir / f"{args.name}-{look}.gguf"
        size, digest = write_gguf(
            path,
            base_metadata
            + [
                ("asolaria.look", V_STRING, gguf_string(look)),
                ("asolaria.look_mass", V_UINT64, struct.pack("<Q", int(plane.sum()))),
            ],
            [
                (f"look_{look}_counts", plane, GGML_I64),
                (f"look_{look}_log", log_u16(plane), GGML_I16),
                (f"look_{look}_spectrum_q31", np.rint(spectra[look] * (2**31 - 1)), GGML_I32),
            ],
        )
        outputs.append((look, path, size, digest))

    receipt_rows = [
        row(
            "SEE64HDR",
            schema="ASOLARIA-LIRIS-SEE-SELF-64-V1",
            class_="LIRIS_LOCAL_MEASURED",
            seat="LIRIS",
            model_label=args.model_label,
            model_weights=0,
            sources=len(sources),
            source_bytes=sum(source.size for source in sources),
        ).replace("class_=", "class="),
    ]
    for index, source in enumerate(sources):
        receipt_rows.append(
            row(
                "SOURCE",
                index=index,
                path=source.path.as_posix(),
                bytes=source.size,
                sha256=source.sha256,
            )
        )
    receipt_rows.extend(
        [
            row(
                "CUBE",
                n=N,
                voxels=VOXELS,
                occupied=occupied,
                mass=total_mass,
                triples=projection.triples,
                dropped_tail_bytes=projection.dropped_tail_bytes,
            ),
            row(
                "SPLIT_INSTRUMENT",
                widths="22,22,20",
                solid_mass=solid_mass,
                translucent_mass=translucent_mass,
                solid_fraction=f"{solid_mass / total_mass:.9f}",
                translucent_fraction=f"{translucent_mass / total_mass:.9f}",
            ),
            row(
                "SPLIT_SOURCE_TRITS",
                thresholds="86,172",
                centre=int(projection.source_shells[0]),
                face=int(projection.source_shells[1]),
                edge=int(projection.source_shells[2]),
                corner=int(projection.source_shells[3]),
            ),
            row(
                "CENTRE",
                r=centre[0],
                g=centre[1],
                b=centre[2],
                mass=centre_mass,
                byte_range=f"{centre[0]*4}-{centre[0]*4+3},{centre[1]*4}-{centre[1]*4+3},{centre[2]*4}-{centre[2]*4+3}",
                lower_hex=f"{centre[0]*4:02X}{centre[1]*4:02X}{centre[2]*4:02X}",
            ),
        ]
    )
    for radius, mass, red, green, blue, lead, solid_fraction in radial_rows[:16]:
        receipt_rows.append(
            row(
                "RADIAL",
                radius=radius,
                mass=mass,
                red=f"{red:.6f}",
                green=f"{green:.6f}",
                blue=f"{blue:.6f}",
                lead=lead,
                solid_fraction=f"{solid_fraction:.9f}",
            )
        )
    for left, right in (("XY", "YZ"), ("YZ", "ZX"), ("ZX", "XY")):
        receipt_rows.append(
            row(
                "PAIR",
                a=left,
                b=right,
                raw_pearson=f"{pearson(planes[left], planes[right]):.9f}",
                raw_cosine=f"{cosine(planes[left], planes[right]):.9f}",
                wave_pearson=f"{pearson(spectra[left], spectra[right]):.9f}",
                wave_cosine=f"{cosine(spectra[left], spectra[right]):.9f}",
            )
        )
    for look, path, size, digest in outputs:
        receipt_rows.append(
            row("GGUF", look=look, path=path.as_posix(), bytes=size, sha256=digest)
        )
    receipt_rows.append(
        row(
            "SEE64FTR",
            source_manifest_sha256=hashlib.sha256(
                "\n".join(source.sha256 for source in sources).encode("ascii")
            ).hexdigest(),
            gguf_count=len(outputs),
            roundtrip="exact_by_writer_tensor_bytes",
            gpu_view="projection_only_pending_renderer_probe",
        )
    )
    receipt = "\n".join(receipt_rows) + "\n"
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(receipt, encoding="utf-8", newline="\n")
    receipt_sha = hashlib.sha256(receipt.encode("utf-8")).hexdigest()
    args.receipt.with_suffix(args.receipt.suffix + ".sha256").write_text(
        f"{receipt_sha}  {args.receipt.name}\n", encoding="ascii", newline="\n"
    )

    if args.html:
        stats = (
            f"triples {projection.triples:,} · occupied {occupied:,}/{VOXELS:,} · "
            f"solid {solid_mass/total_mass:.3%} · translucent {translucent_mass/total_mass:.3%}"
        )
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(
            html_document(args.name, cube, centre, stats),
            encoding="utf-8",
            newline="\n",
        )

    first = radial_rows[0] if radial_rows else None
    print(
        row(
            "LIRIS64",
            class_="LIRIS_LOCAL_MEASURED",
            name=args.name,
            sources=len(sources),
            bytes=sum(source.size for source in sources),
            triples=projection.triples,
            occupied=occupied,
            centre=",".join(str(value) for value in centre),
            centre_mass=centre_mass,
            first_lead=first[5] if first else "NONE",
            solid_fraction=f"{solid_mass/total_mass:.9f}",
            translucent_fraction=f"{translucent_mass/total_mass:.9f}",
            ggufs=len(outputs),
            receipt_sha256=receipt_sha,
        ).replace("class_=", "class=")
    )


if __name__ == "__main__":
    main()
