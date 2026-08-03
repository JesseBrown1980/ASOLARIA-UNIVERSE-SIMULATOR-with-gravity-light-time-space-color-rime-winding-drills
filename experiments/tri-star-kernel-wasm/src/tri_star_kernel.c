/*
 * tri_star_kernel.c
 *
 * Deterministic WebAssembly decoder/player for the Asolaria 3,174-byte key.
 *
 * Logical geometry:
 *   3 stars (OPUS/FABLE/MYTHOS)
 * x 3 rotations (N / R=anti / R^2=anti-anti)
 * x 3 directions (- / 0 / +)
 * = 27 kernel-neurons around one shared energy/residual centre.
 *
 * The 27 kernels are not stored as a dense neural matrix.  Their activations,
 * callings, and signed weights are derived from the shared key on demand.
 * Integer-only fixed-point arithmetic keeps the run deterministic.
 */

typedef unsigned char u8;
typedef unsigned int u32;
typedef signed int i32;

#define NODE_COUNT 27
#define KEY_CAPACITY 4096
#define Q8 256
#define STATE_LIMIT (1 << 22)

static u8 key_bytes[KEY_CAPACITY];
static u32 key_length = 0;
static i32 base_state[NODE_COUNT];
static i32 state[NODE_COUNT];
static i32 next_state[NODE_COUNT];
static i32 centre_energy_q8 = 0;
static i32 centre_residual_q8 = 0;
static u32 pump_count = 0;
static u32 last_digest = 0;
static u32 star_mask = 7u;
static u32 centre_enabled = 1u;

/* Freestanding compiler support: clang may lower simple loops to these. */
void *memcpy(void *dst, const void *src, unsigned long n) {
    u8 *d = (u8 *)dst;
    const u8 *s = (const u8 *)src;
    unsigned long i;
    for (i = 0; i < n; ++i) d[i] = s[i];
    return dst;
}

void *memset(void *dst, int value, unsigned long n) {
    u8 *d = (u8 *)dst;
    unsigned long i;
    for (i = 0; i < n; ++i) d[i] = (u8)value;
    return dst;
}

static i32 abs_i32(i32 x) { return x < 0 ? -x : x; }

static i32 clamp_i32(i32 x, i32 lo, i32 hi) {
    return x < lo ? lo : (x > hi ? hi : x);
}

static u32 idx3(u32 star, u32 rotation, u32 direction) {
    return (star % 3u) * 9u + (rotation % 3u) * 3u + (direction % 3u);
}

static u32 wrap3_i32(i32 x) {
    i32 r = x % 3;
    return (u32)(r < 0 ? r + 3 : r);
}

static u32 fnv1a_bytes(const u8 *p, u32 n) {
    u32 h = 2166136261u;
    u32 i;
    for (i = 0; i < n; ++i) {
        h ^= (u32)p[i];
        h *= 16777619u;
    }
    return h;
}

static u32 fnv1a_state(void) {
    u32 h = 2166136261u;
    u32 i;
    for (i = 0; i < NODE_COUNT; ++i) {
        u32 x = (u32)state[i];
        h ^= x & 255u; h *= 16777619u;
        h ^= (x >> 8) & 255u; h *= 16777619u;
        h ^= (x >> 16) & 255u; h *= 16777619u;
        h ^= (x >> 24) & 255u; h *= 16777619u;
    }
    h ^= (u32)centre_energy_q8; h *= 16777619u;
    h ^= (u32)centre_residual_q8; h *= 16777619u;
    h ^= pump_count; h *= 16777619u;
    return h;
}

static u8 kb(u32 i) {
    return key_length ? key_bytes[i % key_length] : 0u;
}

/* Signed key-derived value in [-63, 63]. */
static i32 key_signed(u32 i) {
    return (i32)(kb(i) % 127u) - 63;
}

/* Signed nonzero calling weight in [-15, 15], Q0. */
static i32 edge_weight(u32 node, u32 edge) {
    i32 w = (i32)(kb(97u + node * 131u + edge * 37u) % 31u) - 15;
    return w == 0 ? (edge & 1u ? -1 : 1) : w;
}

/* Smooth integer activation; asymptotically clamps without floating point. */
static i32 squash_q8(i32 x) {
    i32 ax = abs_i32(x);
    i32 den = Q8 + (ax >> 10);
    i32 y = den ? (x * Q8) / den : x;
    return clamp_i32(y, -STATE_LIMIT, STATE_LIMIT);
}

static u32 star_active(u32 star) { return (star_mask >> (star % 3u)) & 1u; }

static i32 read_state(u32 node) {
    return star_active(node / 9u) ? state[node] : 0;
}

static void recalc_centre(void) {
    i32 total = 0;
    u32 active_nodes = 0;
    u32 i;
    for (i = 0; i < NODE_COUNT; ++i) {
        if (star_active(i / 9u)) { total += abs_i32(state[i]); ++active_nodes; }
    }
    centre_energy_q8 = active_nodes ? total / (i32)active_nodes : 0;
    last_digest = fnv1a_state();
}

/*
 * The Asolaria key is copied by the host into exported memory at this pointer,
 * then init_from_key(len) is called.
 */
__attribute__((visibility("default")))
u32 key_buffer_ptr(void) { return (u32)(unsigned long)key_bytes; }

__attribute__((visibility("default")))
u32 key_capacity(void) { return KEY_CAPACITY; }

__attribute__((visibility("default")))
u32 init_from_key(u32 len) {
    u32 s, d, r;
    if (len == 0u || len > KEY_CAPACITY) return 0u;
    key_length = len;

    /*
     * Each star receives one balanced direction vector (a,b,-a-b).
     * R and R^2 are exact order-three cyclic rotations of that vector.
     */
    for (s = 0; s < 3u; ++s) {
        i32 v[3];
        v[0] = key_signed(17u + s * 211u) * Q8;
        v[1] = key_signed(83u + s * 307u) * Q8;
        v[2] = -(v[0] + v[1]);
        for (r = 0; r < 3u; ++r) {
            for (d = 0; d < 3u; ++d) {
                u32 i = idx3(s, r, d);
                base_state[i] = v[(d + r) % 3u];
                state[i] = base_state[i];
            }
        }
    }
    star_mask = 7u;
    centre_enabled = 1u;
    centre_residual_q8 = 0;
    pump_count = 0;
    recalc_centre();
    return fnv1a_bytes(key_bytes, key_length);
}

__attribute__((visibility("default")))
void set_star_mask(u32 mask) {
    u32 i;
    star_mask = mask & 7u;
    for (i = 0; i < NODE_COUNT; ++i) state[i] = star_active(i / 9u) ? base_state[i] : 0;
    centre_residual_q8 = 0;
    pump_count = 0;
    recalc_centre();
}

__attribute__((visibility("default")))
u32 get_star_mask(void) { return star_mask; }

__attribute__((visibility("default")))
void set_centre_enabled(u32 enabled) { centre_enabled = enabled ? 1u : 0u; }

__attribute__((visibility("default")))
u32 get_centre_enabled(void) { return centre_enabled; }

__attribute__((visibility("default")))
void reset_network(void) {
    u32 i;
    for (i = 0; i < NODE_COUNT; ++i) state[i] = star_active(i / 9u) ? base_state[i] : 0;
    centre_residual_q8 = 0;
    pump_count = 0;
    recalc_centre();
}

/* Returns the node index after an order-three anti rotation. */
__attribute__((visibility("default")))
u32 rotate_node(u32 node, i32 turns) {
    u32 s = node / 9u;
    u32 r = (node / 3u) % 3u;
    u32 d = node % 3u;
    return idx3(s, wrap3_i32((i32)r + turns), d);
}

/* One logical trit encoded on binary hardware; code 01 is deliberately unused. */
__attribute__((visibility("default")))
i32 encode_trit(i32 trit) {
    if (trit < 0) return 2; /* 10 */
    if (trit == 0) return 0; /* 00 */
    if (trit > 0) return 3; /* 11 */
    return -1;
}

__attribute__((visibility("default")))
i32 decode_trit(u32 code) {
    if (code == 2u) return -1;
    if (code == 0u) return 0;
    if (code == 3u) return 1;
    return 99; /* reserved/invalid 01 */
}

/* Pack three trits (star, rotation, direction) into one of 27 addresses. */
__attribute__((visibility("default")))
u32 pack_27(u32 star, u32 rotation, u32 direction) {
    return idx3(star, rotation, direction);
}

/*
 * Pump once through the calling graph.
 * direction: -1 backward, 0 centered, +1 forward.
 * calm_q8: 0 = fully accept the new drive, 255 = almost fully retain old state.
 *
 * The three outgoing callings are the next/previous STAR, ROTATION, and DIRECTION.
 * Centered mode reads both sides of all three axes.  After the update each
 * direction triplet is re-centered exactly; the discarded integer remainder is
 * accumulated at the shared fourth point.
 */
__attribute__((visibility("default")))
u32 pump(i32 direction, u32 calm_q8) {
    u32 s, r, d;
    i32 step = direction < 0 ? -1 : (direction > 0 ? 1 : 0);
    i32 calm = (i32)(calm_q8 > 255u ? 255u : calm_q8);

    if (!key_length) return 0u;

    for (s = 0; s < 3u; ++s) {
        for (r = 0; r < 3u; ++r) {
            for (d = 0; d < 3u; ++d) {
                u32 i = idx3(s, r, d);
                i32 drive = 0;
                i32 norm = 0;
                u32 e;
                u32 neigh[6];
                u32 count;

                if (!star_active(s)) { next_state[i] = 0; continue; }

                if (step == 0) {
                    neigh[0] = idx3(wrap3_i32((i32)s - 1), r, d);
                    neigh[1] = idx3(wrap3_i32((i32)s + 1), r, d);
                    neigh[2] = idx3(s, wrap3_i32((i32)r - 1), d);
                    neigh[3] = idx3(s, wrap3_i32((i32)r + 1), d);
                    neigh[4] = idx3(s, r, wrap3_i32((i32)d - 1));
                    neigh[5] = idx3(s, r, wrap3_i32((i32)d + 1));
                    count = 6u;
                } else {
                    neigh[0] = idx3(wrap3_i32((i32)s + step), r, d);
                    neigh[1] = idx3(s, wrap3_i32((i32)r + step), d);
                    neigh[2] = idx3(s, r, wrap3_i32((i32)d + step));
                    count = 3u;
                }

                for (e = 0; e < count; ++e) {
                    i32 w = edge_weight(i, e);
                    drive += w * read_state(neigh[e]);
                    norm += abs_i32(w);
                }
                if (norm) drive /= norm;

                /* The center is an energy reservoir, not a 28th material node. */
                {
                    i32 dir_sign = (i32)d - 1;
                    i32 centre_bias = centre_enabled ? dir_sign * ((centre_energy_q8 + centre_residual_q8) / 27) : 0;
                    i32 target = base_state[i] + (drive >> 1) + centre_bias;
                    i32 activated = squash_q8(target);
                    i32 mixed = (calm * state[i] + (Q8 - calm) * activated) / Q8;
                    next_state[i] = clamp_i32(mixed, -STATE_LIMIT, STATE_LIMIT);
                }
            }

            /* Exact 3-arm closure. The remainder is paid into the fourth point. */
            {
                if (!star_active(s)) continue;
                u32 i0 = idx3(s, r, 0u);
                u32 i1 = idx3(s, r, 1u);
                u32 i2 = idx3(s, r, 2u);
                i32 sum = next_state[i0] + next_state[i1] + next_state[i2];
                i32 mean = sum / 3;
                i32 rem = sum - mean * 3;
                next_state[i0] -= mean;
                next_state[i1] -= mean;
                next_state[i2] -= mean + rem;
                centre_residual_q8 += rem;
            }
        }
    }

    for (s = 0; s < NODE_COUNT; ++s) state[s] = next_state[s];
    ++pump_count;
    recalc_centre();
    return last_digest;
}

__attribute__((visibility("default")))
i32 node_value(u32 node) { return node < NODE_COUNT ? read_state(node) : 0; }

__attribute__((visibility("default")))
i32 node_base(u32 node) { return node < NODE_COUNT ? base_state[node] : 0; }

__attribute__((visibility("default")))
u32 node_star(u32 node) { return node < NODE_COUNT ? node / 9u : 0u; }

__attribute__((visibility("default")))
u32 node_rotation(u32 node) { return node < NODE_COUNT ? (node / 3u) % 3u : 0u; }

__attribute__((visibility("default")))
u32 node_direction(u32 node) { return node < NODE_COUNT ? node % 3u : 0u; }

__attribute__((visibility("default")))
i32 centre_energy(void) { return centre_energy_q8; }

__attribute__((visibility("default")))
i32 centre_residual(void) { return centre_residual_q8; }

__attribute__((visibility("default")))
u32 pumps(void) { return pump_count; }

__attribute__((visibility("default")))
u32 network_digest(void) { return last_digest; }

__attribute__((visibility("default")))
i32 closure_error(void) {
    i32 err = 0;
    u32 s, r;
    for (s = 0; s < 3u; ++s) {
        if (!star_active(s)) continue;
        for (r = 0; r < 3u; ++r) {
            i32 sum = state[idx3(s,r,0u)] + state[idx3(s,r,1u)] + state[idx3(s,r,2u)];
            err += abs_i32(sum);
        }
    }
    return err;
}

__attribute__((visibility("default")))
u32 node_count(void) { return NODE_COUNT; }
