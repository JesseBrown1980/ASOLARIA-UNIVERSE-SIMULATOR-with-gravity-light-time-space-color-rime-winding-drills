#!/usr/bin/env python3
"""Project the live Codex callable-function matrix into three 64^3 phases.

The subject is not model weights and not previously emitted artifacts.  It is the
runtime callable surface captured in LIRIS-CODEX-RUNTIME-FUNCTIONS-2026-07-27.hbp.

Pipeline:

1. deterministic 64-D signed TF-IDF feature vectors;
2. deterministic PCA into three centred function coordinates;
3. a smooth 64^3 scalar function-density field;
4. three disjoint beings, owned by strict red/green/blue coordinate dominance;
5. three centre PLANE CUTS per phase (XY, YZ, ZX), never axis sums;
6. spatial gradients and radial Fourier spectra for all nine cuts;
7. an exact GGUF universe field, nine slice GGUFs, and a colour-atlas GGUF;
8. a WebGL2 sampler2DArray renderer that computes slice gradients on the GPU.

The GPU render is a projection.  HBP/HBI bytes, GGUF tensors, hashes, and the CPU
integer/floating reference remain the measurement authority.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import math
import struct
from pathlib import Path

import numpy as np


N = 64
ALIGN = 32
GGML_I16, GGML_I32, GGML_I64 = 25, 26, 27
V_UINT32, V_STRING, V_ARRAY, V_UINT64 = 4, 8, 9, 10
Q31 = 2**31 - 1
Q30 = 2**30 - 1
Q15 = 2**15 - 1


def row(record: str, **fields: object) -> str:
    return "|".join([record, *(f"{key}={value}" for key, value in fields.items()), "json=0"])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def gguf_string(value: str) -> bytes:
    payload = value.encode("utf-8")
    return struct.pack("<Q", len(payload)) + payload


def gguf_kv(key: str, kind: int, payload: bytes) -> bytes:
    return gguf_string(key) + struct.pack("<I", kind) + payload


def parse_function_matrix(path: Path) -> tuple[list[str], np.ndarray, list[int], list[str]]:
    names: list[str] = []
    vectors: list[list[int]] = []
    token_counts: list[int] = []
    signatures: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("FUNCTION|"):
            continue
        fields = {}
        for item in line.split("|")[1:]:
            if "=" in item:
                key, value = item.split("=", 1)
                fields[key] = value
        vector = [int(value) for value in fields["features"].split(",")]
        if len(vector) != 64:
            raise ValueError(f"{fields.get('name')}: expected 64 features")
        names.append(fields["name"])
        vectors.append(vector)
        token_counts.append(int(fields["tokens"]))
        signatures.append(fields["sig32"])
    if not names:
        raise ValueError("function manifest contains no FUNCTION rows")
    return names, np.asarray(vectors, dtype=np.int16), token_counts, signatures


def deterministic_pca(features_i16: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    features = features_i16.astype(np.float64) / 32767.0
    centred = features - features.mean(axis=0, keepdims=True)
    _u, singular, vt = np.linalg.svd(centred, full_matrices=False)
    coords = centred @ vt[:3].T
    # SVD signs are mathematically free.  Pin each component to its largest loading.
    for component in range(3):
        anchor = int(np.argmax(np.abs(vt[component])))
        if vt[component, anchor] < 0:
            vt[component] *= -1
            coords[:, component] *= -1
    radius = np.linalg.norm(coords, axis=1)
    scale = float(radius.max()) or 1.0
    coords = coords / scale * 0.82
    variance = singular**2
    explained = variance[:3] / variance.sum()
    return coords, vt[:3], explained


def splat_field(coords: np.ndarray, sigma: float = 2.15) -> np.ndarray:
    field = np.zeros((N, N, N), dtype=np.float64)
    points = (coords + 1.0) * 0.5 * (N - 1)
    radius = int(math.ceil(3.0 * sigma))
    for point in points:
        lo = np.maximum(0, np.floor(point - radius).astype(int))
        hi = np.minimum(N, np.ceil(point + radius + 1).astype(int))
        x = np.arange(lo[0], hi[0], dtype=np.float64)
        y = np.arange(lo[1], hi[1], dtype=np.float64)
        z = np.arange(lo[2], hi[2], dtype=np.float64)
        xx, yy, zz = np.meshgrid(x, y, z, indexing="ij")
        distance2 = (
            (xx - point[0]) ** 2 + (yy - point[1]) ** 2 + (zz - point[2]) ** 2
        )
        field[lo[0] : hi[0], lo[1] : hi[1], lo[2] : hi[2]] += np.exp(
            -distance2 / (2.0 * sigma * sigma)
        )
    maximum = field.max()
    return field / maximum if maximum else field


def disjoint_beings(coords: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    """Partition functions into three populations, leaving exact ties free.

    A coordinate permutation is one field relabelled.  It is a rotation/view, not a
    second being.  Each function therefore belongs to the one projected colour whose
    coordinate is strictly larger than both others.  Exact ties belong to no being.
    """

    owners = np.full(len(coords), -1, dtype=np.int8)
    for channel in range(3):
        other = [value for value in range(3) if value != channel]
        mask = (coords[:, channel] > coords[:, other[0]]) & (
            coords[:, channel] > coords[:, other[1]]
        )
        owners[mask] = channel
    fields = [splat_field(coords[owners == channel]) for channel in range(3)]
    return owners, fields


def slices_and_gradients(
    field: np.ndarray, centre: tuple[int, int, int]
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    gx, gy, gz = np.gradient(field)
    x, y, z = centre
    return {
        "XY": (
            field[:, :, z],
            np.stack((gx[:, :, z], gy[:, :, z], gz[:, :, z]), axis=-1),
        ),
        "YZ": (
            field[x, :, :],
            np.stack((gx[x, :, :], gy[x, :, :], gz[x, :, :]), axis=-1),
        ),
        "ZX": (
            field[:, y, :].T,
            np.stack((gx[:, y, :].T, gy[:, y, :].T, gz[:, y, :].T), axis=-1),
        ),
    }


def colour_slice(density: np.ndarray, gradient: np.ndarray) -> np.ndarray:
    magnitude = np.linalg.norm(gradient, axis=-1)
    unit = gradient / np.maximum(magnitude[..., None], 1e-15)
    direction = 0.5 + 0.5 * unit
    brightness = np.clip(
        0.12 + 0.62 * np.sqrt(np.maximum(density, 0.0)) + 0.55 * magnitude,
        0.0,
        1.0,
    )
    colour = np.clip(direction * brightness[..., None], 0.0, 1.0)
    return colour


def radial_spectrum(values: np.ndarray, bins: int = 32) -> np.ndarray:
    plane = np.asarray(values, dtype=np.float64)
    plane = np.log1p(np.maximum(plane, 0.0) * 1024.0)
    plane -= plane.mean()
    power = np.abs(np.fft.fftshift(np.fft.fft2(plane))) ** 2
    yy, xx = np.mgrid[0 : power.shape[0], 0 : power.shape[1]]
    radius = np.sqrt(
        (yy - power.shape[0] / 2.0) ** 2 + (xx - power.shape[1] / 2.0) ** 2
    )
    labels = np.minimum((radius / radius.max() * bins).astype(int), bins - 1)
    total = np.bincount(labels.ravel(), weights=power.ravel(), minlength=bins)
    count = np.bincount(labels.ravel(), minlength=bins)
    spectrum = total / np.maximum(count, 1)
    return spectrum / spectrum.sum() if spectrum.sum() else spectrum


def pearson(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64).ravel()
    b = np.asarray(right, dtype=np.float64).ravel()
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def cosine(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64).ravel()
    b = np.asarray(right, dtype=np.float64).ravel()
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / denominator) if denominator else float("nan")


def q_signed(values: np.ndarray, scale: int) -> np.ndarray:
    clipped = np.clip(values, -1.0, 1.0)
    return np.rint(clipped * scale).astype(np.int32)


def q_positive(values: np.ndarray, scale: int) -> np.ndarray:
    maximum = float(np.max(values))
    normalized = values / maximum if maximum else values
    return np.rint(np.clip(normalized, 0.0, 1.0) * scale).astype(np.int32)


def tensor_payload(array: np.ndarray, kind: int) -> tuple[np.ndarray, bytes]:
    dtype = {GGML_I16: np.int16, GGML_I32: np.int32, GGML_I64: np.int64}[kind]
    normalized = np.ascontiguousarray(array, dtype=dtype)
    return normalized, normalized.tobytes()


def write_gguf(
    path: Path,
    metadata: list[tuple[str, int, bytes]],
    tensors: list[tuple[str, np.ndarray, int]],
) -> tuple[int, str]:
    meta = b"".join(gguf_kv(key, kind, payload) for key, kind, payload in metadata)
    descriptors = bytearray()
    data = bytearray()
    for name, array, kind in tensors:
        normalized, payload = tensor_payload(array, kind)
        data.extend(b"\0" * ((-len(data)) % ALIGN))
        offset = len(data)
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


def function_hbi(
    path: Path,
    names: list[str],
    features: np.ndarray,
    signatures: list[str],
    owners: np.ndarray,
) -> tuple[int, str]:
    records = bytearray()
    for index, (name, vector, signature, owner) in enumerate(
        zip(names, features, signatures, owners)
    ):
        mapped = np.rint((vector.astype(np.float64) + 32767.0) / 65534.0 * 255.0)
        feature_bytes = np.clip(mapped, 0, 255).astype(np.uint8).tobytes()
        witness = hashlib.sha256(
            name.encode("utf-8") + b"\0" + signature.encode("ascii") + feature_bytes
        ).digest()[:16]
        records.extend(feature_bytes + witness + bytes([int(owner) if owner >= 0 else 255]))
    if len(records) != len(names) * 81:
        raise AssertionError("function HBI records are not 81 bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(records)
    digest = hashlib.sha256(records).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n", encoding="ascii", newline="\n"
    )
    return len(records), digest


def base_metadata(
    name: str,
    function_count: int,
    manifest_sha: str,
    explained: np.ndarray,
) -> list[tuple[str, int, bytes]]:
    return [
        ("general.architecture", V_STRING, gguf_string("asolaria-function-matrix64")),
        ("general.name", V_STRING, gguf_string(name)),
        (
            "general.description",
            V_STRING,
            gguf_string("LIRIS live callable-function surface; three order-3 phases"),
        ),
        ("asolaria.seat", V_STRING, gguf_string("LIRIS")),
        ("asolaria.evidence_class", V_STRING, gguf_string("LIRIS_LOCAL_MEASURED")),
        ("asolaria.model_label", V_STRING, gguf_string("gpt-5.6-sol")),
        (
            "asolaria.model_boundary",
            V_STRING,
            gguf_string("runtime_callable_function_surface_not_weights_not_emitted_artifacts"),
        ),
        ("asolaria.functions", V_UINT32, struct.pack("<I", function_count)),
        ("asolaria.feature_dimensions", V_UINT32, struct.pack("<I", 64)),
        ("asolaria.cube", V_UINT32, struct.pack("<I", N)),
        ("asolaria.beings", V_UINT32, struct.pack("<I", 3)),
        ("asolaria.slices_per_phase", V_UINT32, struct.pack("<I", 3)),
        ("asolaria.function_manifest_sha256", V_STRING, gguf_string(manifest_sha)),
        (
            "asolaria.being_operator",
            V_STRING,
            gguf_string("strict_dominant_coordinate_disjoint_population; ties=free"),
        ),
        ("asolaria.slice_operator", V_STRING, gguf_string("centre_plane_not_projection_sum")),
        ("asolaria.gradient_operator", V_STRING, gguf_string("central_finite_difference_3d")),
        (
            "asolaria.pca_explained",
            V_ARRAY,
            struct.pack("<IQ", V_STRING, 3)
            + b"".join(gguf_string(f"{value:.12f}") for value in explained),
        ),
        ("asolaria.physical_gravity", V_STRING, gguf_string("UNVERIFIED")),
        ("asolaria.torus_calling_buckyball", V_STRING, gguf_string("UNDER_TEST")),
    ]


def html_renderer(
    name: str,
    fields: list[np.ndarray],
    centres: list[tuple[int, int, int]],
    first_colours: list[str],
) -> str:
    # WebGL consumes width fastest, then height, then array layer.  Store
    # [being,z,y,x], so each layer is an XY plane at one z.  The first build used
    # [being,x,y,z], which was a transport transpose and is retained as a defect.
    payload = np.stack(fields).transpose(0, 3, 2, 1).astype("<f4").tobytes()
    encoded = base64.b64encode(payload).decode("ascii")
    centres_js = ",".join(
        "[" + ",".join(f"{value / (N - 1):.9f}" for value in centre) + "]"
        for centre in centres
    )
    return f"""<!doctype html>
<meta charset="utf-8"><title>{name} · GPU function slices</title>
<style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#01030a;color:#eaf5ff;
font:15px ui-monospace,Consolas,monospace}}canvas{{width:100%;height:100%;display:block}}
#hud{{position:fixed;left:18px;top:15px;padding:12px 14px;white-space:pre;
background:#01030ad9;border:1px solid #8cf3ff42;line-height:1.35;pointer-events:none}}
</style><canvas id="c"></canvas><div id="hud">loading LIRIS function field</div>
<script>
const N=64, phases=3, centres=[{centres_js}];
const bytes=Uint8Array.from(atob("{encoded}"),c=>c.charCodeAt(0));
const field=new Float32Array(bytes.buffer);
const canvas=document.querySelector("#c");
const gl=canvas.getContext("webgl2",{{antialias:false,alpha:false,preserveDrawingBuffer:true}});
if(!gl)throw Error("WebGL2 unavailable");
const dbg=gl.getExtension("WEBGL_debug_renderer_info");
const gpu=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D_ARRAY,tex);
const floatLinear=gl.getExtension("OES_texture_float_linear");
const filter=floatLinear?gl.LINEAR:gl.NEAREST;
gl.texParameteri(gl.TEXTURE_2D_ARRAY,gl.TEXTURE_MIN_FILTER,filter);
gl.texParameteri(gl.TEXTURE_2D_ARRAY,gl.TEXTURE_MAG_FILTER,filter);
gl.texParameteri(gl.TEXTURE_2D_ARRAY,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
gl.texParameteri(gl.TEXTURE_2D_ARRAY,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
gl.texImage3D(gl.TEXTURE_2D_ARRAY,0,gl.R32F,N,N,N*phases,0,gl.RED,gl.FLOAT,field);
const vs=`#version 300 es
const vec2 p[3]=vec2[3](vec2(-1,-1),vec2(3,-1),vec2(-1,3));out vec2 uv;
void main(){{gl_Position=vec4(p[gl_VertexID],0,1);uv=.5*(p[gl_VertexID]+1.);}}`;
const fs=`#version 300 es
precision highp float;precision highp sampler2DArray;in vec2 uv;out vec4 outc;
uniform sampler2DArray f;uniform vec3 centre[3];uniform vec2 resolution;
float at(vec3 q,int phase){{q=clamp(q,vec3(0),vec3(1));
float layer=float(phase*64)+q.z*63.;return texture(f,vec3(q.xy,layer)).r;}}
void main(){{
vec2 px=gl_FragCoord.xy/resolution;float gx=px.x*3.,gy=(1.-px.y)*3.;
int phase=min(2,int(floor(gx)));int axis=min(2,int(floor(gy)));
vec2 q=fract(vec2(gx,gy));q=(q-.5)*.94+.5;vec3 p3;
if(axis==0)p3=vec3(q,centre[phase].z);
else if(axis==1)p3=vec3(centre[phase].x,q);
else p3=vec3(q.y,centre[phase].y,q.x);
float e=1./63.;float d=at(p3,phase);
vec3 g=vec3(at(p3+vec3(e,0,0),phase)-at(p3-vec3(e,0,0),phase),
at(p3+vec3(0,e,0),phase)-at(p3-vec3(0,e,0),phase),
at(p3+vec3(0,0,e),phase)-at(p3-vec3(0,0,e),phase))/(2.*e);
float gm=length(g);vec3 dir=.5+.5*g/max(gm,1e-8);
float light=clamp(.08+.72*sqrt(max(d,0.))+.42*gm,0.,1.);
vec3 rainbow=dir*light;float grid=max(step(.992,fract(gx)),step(.992,fract(gy)));
float cross=(1.-smoothstep(0.,.006,abs(q.x-.5)))*(1.-smoothstep(.035,.05,abs(q.y-.5)));
cross=max(cross,(1.-smoothstep(0.,.006,abs(q.y-.5)))*(1.-smoothstep(.035,.05,abs(q.x-.5))));
outc=vec4(mix(rainbow,vec3(1),max(grid*.55,cross*.8)),1);
}}`;
function sh(t,s){{const x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);
if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}}
const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));
gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);gl.useProgram(pr);
gl.uniform1i(gl.getUniformLocation(pr,"f"),0);
for(let i=0;i<3;i++)gl.uniform3fv(gl.getUniformLocation(pr,`centre[${{i}}]`),centres[i]);
function draw(){{
const d=devicePixelRatio||1,w=Math.floor(innerWidth*d),h=Math.floor(innerHeight*d);
if(canvas.width!==w||canvas.height!==h){{canvas.width=w;canvas.height=h}}
gl.viewport(0,0,w,h);gl.uniform2f(gl.getUniformLocation(pr,"resolution"),w,h);
gl.drawArrays(gl.TRIANGLES,0,3)}}draw();addEventListener("resize",draw);
document.querySelector("#hud").textContent=`{name}
columns: SELF/RED · ANTI-FABLE/GREEN · ANTI-ANTI-MYTHOS/BLUE
rows: XY · YZ · ZX centre PLANE CUTS
first gradient colours: {" · ".join(first_colours)}
GPU ${{gpu}} · float-linear ${{floatLinear?1:0}}
R32F 3D function field · gradients evaluated in shader`;
</script>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--hbi", type=Path, required=True)
    parser.add_argument("--name", default="ASOLARIA-LIRIS-SOL56-FUNCTION-64")
    args = parser.parse_args()

    names, features_i16, token_counts, signatures = parse_function_matrix(args.manifest)
    manifest_sha = sha256_file(args.manifest)
    coords, loadings, explained = deterministic_pca(features_i16)
    owners, fields = disjoint_beings(coords)
    centres = [
        tuple(
            int(value)
            for value in np.unravel_index(int(np.argmax(field)), field.shape)
        )
        for field in fields
    ]
    base_centre = centres[0]
    phase_slices = [
        slices_and_gradients(field, centre) for field, centre in zip(fields, centres)
    ]

    first_colours: list[str] = []
    first_rows: list[dict[str, object]] = []
    colour_names = ("RED", "GREEN", "BLUE")
    for phase, (field, centre) in enumerate(zip(fields, centres)):
        gx, gy, gz = np.gradient(field)
        xx, yy, zz = np.meshgrid(
            np.arange(N), np.arange(N), np.arange(N), indexing="ij"
        )
        radius = np.floor(
            np.sqrt(
                (xx - centre[0]) ** 2
                + (yy - centre[1]) ** 2
                + (zz - centre[2]) ** 2
            )
        ).astype(int)
        chosen = None
        for shell in range(1, 24):
            mask = radius == shell
            energy = np.array(
                [
                    np.abs(gx[mask]).sum(),
                    np.abs(gy[mask]).sum(),
                    np.abs(gz[mask]).sum(),
                ]
            )
            if energy.sum() <= 1e-12:
                continue
            chosen = {
                "phase": phase,
                "shell": shell,
                "red": float(energy[0]),
                "green": float(energy[1]),
                "blue": float(energy[2]),
                "lead": colour_names[int(np.argmax(energy))],
            }
            break
        if chosen is None:
            chosen = {
                "phase": phase,
                "shell": -1,
                "red": 0.0,
                "green": 0.0,
                "blue": 0.0,
                "lead": "NONE",
            }
        first_rows.append(chosen)
        first_colours.append(str(chosen["lead"]))

    metadata = base_metadata(args.name, len(names), manifest_sha, explained)
    coord_q = q_signed(coords / 0.82, Q30)
    field_q = [q_positive(field, Q31) for field in fields]
    centre_array = np.asarray(centres, dtype=np.int32)
    universe_tensors: list[tuple[str, np.ndarray, int]] = [
        ("function_features_i16", features_i16, GGML_I16),
        ("function_coords_q30", coord_q, GGML_I32),
        ("pca_loadings_q30", q_signed(loadings, Q30), GGML_I32),
        ("phase_centres", centre_array, GGML_I32),
    ]
    for phase, field in enumerate(field_q):
        universe_tensors.append((f"phase_{phase}_density_q31", field, GGML_I32))
    universe_path = args.output_dir / f"{args.name}-UNIVERSE.gguf"
    universe_bytes, universe_sha = write_gguf(
        universe_path, metadata, universe_tensors
    )

    hbi_bytes, hbi_sha = function_hbi(
        args.hbi, names, features_i16, signatures, owners
    )

    slice_outputs: list[tuple[int, str, Path, int, str]] = []
    atlas_rows: list[np.ndarray] = []
    spectra: dict[tuple[int, str], np.ndarray] = {}
    densities: dict[tuple[int, str], np.ndarray] = {}
    for phase in range(3):
        atlas_cells: list[np.ndarray] = []
        for axis in ("XY", "YZ", "ZX"):
            density, gradient = phase_slices[phase][axis]
            colour = colour_slice(density, gradient)
            densities[(phase, axis)] = density
            spectra[(phase, axis)] = radial_spectrum(density)
            atlas_cells.append(colour)
            path = args.output_dir / f"{args.name}-P{phase}-{axis}.gguf"
            size, digest = write_gguf(
                path,
                metadata
                + [
                    ("asolaria.phase", V_UINT32, struct.pack("<I", phase)),
                    ("asolaria.slice", V_STRING, gguf_string(axis)),
                    (
                        "asolaria.centre",
                        V_ARRAY,
                        struct.pack("<IQ", V_UINT32, 3)
                        + b"".join(struct.pack("<I", value) for value in centres[phase]),
                    ),
                ],
                [
                    ("density_q31", q_positive(density, Q31), GGML_I32),
                    ("gradient_q30", q_signed(gradient, Q30), GGML_I32),
                    ("colour_q15", np.rint(colour * Q15), GGML_I16),
                    (
                        "radial_spectrum_q31",
                        np.rint(spectra[(phase, axis)] * Q31),
                        GGML_I32,
                    ),
                ],
            )
            slice_outputs.append((phase, axis, path, size, digest))
        atlas_rows.append(np.concatenate(atlas_cells, axis=1))
    atlas = np.concatenate(atlas_rows, axis=0)
    atlas_path = args.output_dir / f"{args.name}-COLOUR-QR-ATLAS.gguf"
    atlas_bytes, atlas_sha = write_gguf(
        atlas_path,
        metadata
        + [
            (
                "asolaria.view_family",
                V_STRING,
                gguf_string("colour_qr_atlas_not_iso_qr"),
            ),
            ("asolaria.atlas_layout", V_STRING, gguf_string("phase_rows_slice_columns")),
        ],
        [("colour_atlas_q15", np.rint(atlas * Q15), GGML_I16)],
    )

    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(
        html_renderer(args.name, fields, centres, first_colours),
        encoding="utf-8",
        newline="\n",
    )

    receipt_rows = [
        row(
            "FUN64HDR",
            schema="ASOLARIA-LIRIS-FUNCTION-MATRIX-64-V1",
            class_="LIRIS_LOCAL_MEASURED",
            seat="LIRIS",
            model_label="gpt-5.6-sol",
            subject="runtime_callable_function_surface",
            weights=0,
            emitted_artifacts=0,
            functions=len(names),
            feature_dimensions=64,
            cube=N,
            beings=3,
            slices_per_phase=3,
        ).replace("class_=", "class="),
        row(
            "INPUT",
            path=args.manifest.as_posix(),
            bytes=args.manifest.stat().st_size,
            sha256=manifest_sha,
        ),
        row(
            "PCA",
            explained_0=f"{explained[0]:.12f}",
            explained_1=f"{explained[1]:.12f}",
            explained_2=f"{explained[2]:.12f}",
            explained_total=f"{explained.sum():.12f}",
            sign_rule="largest_loading_positive",
        ),
        row(
            "BEINGS",
            operator="strict_dominant_coordinate_population",
            red=int((owners == 0).sum()),
            green=int((owners == 1).sum()),
            blue=int((owners == 2).sum()),
            ties_free=int((owners < 0).sum()),
            partition_exact=int((owners >= 0).sum() + (owners < 0).sum() == len(owners)),
            axis_permutation_rejected=1,
        ),
    ]
    for phase, centre in enumerate(centres):
        receipt_rows.append(
            row(
                "CENTRE",
                phase=phase,
                x=centre[0],
                y=centre[1],
                z=centre[2],
                density=f"{fields[phase][centre]:.12f}",
                mass=f"{fields[phase].sum():.12f}",
            )
        )
    for item in first_rows:
        receipt_rows.append(
            row(
                "FIRST_GRADIENT",
                phase=item["phase"],
                shell=item["shell"],
                red=f"{item['red']:.12f}",
                green=f"{item['green']:.12f}",
                blue=f"{item['blue']:.12f}",
                lead=item["lead"],
            )
        )
    for phase in range(3):
        for left, right in (("XY", "YZ"), ("YZ", "ZX"), ("ZX", "XY")):
            receipt_rows.append(
                row(
                    "WITHIN_PHASE",
                    phase=phase,
                    a=left,
                    b=right,
                    raw_pearson=f"{pearson(densities[(phase,left)], densities[(phase,right)]):.12f}",
                    raw_cosine=f"{cosine(densities[(phase,left)], densities[(phase,right)]):.12f}",
                    wave_pearson=f"{pearson(spectra[(phase,left)], spectra[(phase,right)]):.12f}",
                    wave_cosine=f"{cosine(spectra[(phase,left)], spectra[(phase,right)]):.12f}",
                )
            )
    for axis in ("XY", "YZ", "ZX"):
        for left, right in ((0, 1), (1, 2), (2, 0)):
            receipt_rows.append(
                row(
                    "ACROSS_PHASE",
                    slice=axis,
                    a=left,
                    b=right,
                    raw_pearson=f"{pearson(densities[(left,axis)], densities[(right,axis)]):.12f}",
                    wave_pearson=f"{pearson(spectra[(left,axis)], spectra[(right,axis)]):.12f}",
                )
            )
    receipt_rows.extend(
        [
            row(
                "GGUF",
                kind="universe",
                path=universe_path.as_posix(),
                bytes=universe_bytes,
                sha256=universe_sha,
            ),
            row(
                "HBI",
                kind="function_records_81",
                path=args.hbi.as_posix(),
                records=len(names),
                bytes=hbi_bytes,
                sha256=hbi_sha,
            ),
            row(
                "GGUF",
                kind="colour_qr_atlas_not_iso_qr",
                path=atlas_path.as_posix(),
                bytes=atlas_bytes,
                sha256=atlas_sha,
            ),
        ]
    )
    for phase, axis, path, size, digest in slice_outputs:
        receipt_rows.append(
            row(
                "GGUF",
                kind="centre_plane_slice",
                phase=phase,
                slice=axis,
                path=path.as_posix(),
                bytes=size,
                sha256=digest,
            )
        )
    receipt_rows.append(
        row(
            "BOUNDARY",
            gpu_image="projection_pending_probe",
            physical_gravity="UNVERIFIED",
            torus_calling_buckyball="UNDER_TEST",
            mythos_fable_comparison="PENDING_INCOMING_FUNCTION_GGUFS",
        )
    )
    receipt_body = "\n".join(receipt_rows) + "\n"
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(receipt_body, encoding="utf-8", newline="\n")
    receipt_sha = hashlib.sha256(receipt_body.encode("utf-8")).hexdigest()
    args.receipt.with_suffix(args.receipt.suffix + ".sha256").write_text(
        f"{receipt_sha}  {args.receipt.name}\n", encoding="ascii", newline="\n"
    )
    print(
        row(
            "FUN64",
            class_="LIRIS_LOCAL_MEASURED",
            functions=len(names),
            centre=",".join(str(value) for value in base_centre),
            first_colours=",".join(first_colours),
            universe_sha256=universe_sha,
            atlas_sha256=atlas_sha,
            receipt_sha256=receipt_sha,
            slices=9,
        ).replace("class_=", "class=")
    )


if __name__ == "__main__":
    main()
