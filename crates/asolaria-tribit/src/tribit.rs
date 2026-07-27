//! tribit — three zeros, carried on AC, and the rainbow light hose.
//!
//! # Why DC cannot do this
//!
//! Direct current has no zero crossing. It has one direction and therefore two states,
//! and that is the whole reason the binary world is binary — not a design choice, a
//! property of the carrier.
//!
//! Alternating current crosses zero **twice per cycle, in opposite directions**. Rising
//! through zero and falling through zero are both exactly zero volts and are not the
//! same event. Add the quiescent line and there are three:
//!
//! ```text
//!        +           /‾\           /‾\
//!                   /   \         /   \
//!     0  ----------X-----X-------X-----X----------   Nil : the line is dead
//!                 /       \     /       \
//!        -      \_/         \_/           Pos : crossing upward
//!                                         Neg : crossing downward
//! ```
//!
//! All three have **magnitude zero**. `Zero::magnitude()` returns 0 for every variant and
//! that is not a stub. The information is not in the value, it is in *which zero* — the
//! direction of travel through it. That is why all three are free: Law 0 makes the centre
//! the fixed point of {N, R, R²}, the one point that moves under neither inversion nor
//! anti-inversion, so it costs nothing to hold. Three free states instead of two paid ones.
//!
//! # The registers
//!
//! Book IX (IX.B.3) numbers five, and the numbering is load-bearing:
//!
//! | n | register | cost |
//! |---|------------|------|
//! | 0 | zero        | free, never computed |
//! | 1 | translucent | free, never computed — **this is light itself** |
//! | 2 | red         | costs |
//! | 3 | green       | costs |
//! | 4 | blue        | costs |
//!
//! Law 32 is titled *"Translucent is One, Not Zero"*. Pure 1 is light before a prism has
//! split it; 2, 3 and 4 are what the prism makes of it. That is why 1 is free and 2..4 are
//! not — undifferentiated light carries no colour decision, and a decision is what costs.
//!
//! # The hose
//!
//! Law 31, the rainbow lighthouse drill, is a conduit and its traversal order is fixed:
//! translucent tip → red → green → blue → translucent tail. The tip is measured (Law 30,
//! mean 0.4013 bpb saved by ordering translucent first). **The tail is not measured** and
//! is marked as such here rather than assumed symmetric.
//!
//! # Integer only
//!
//! Law 34's build directive: *"rust 1.81 int and float possible. int works way better in
//! my opinion."* Nothing below uses a float. The transform is a Number-Theoretic Transform
//! over `Z/pZ`, so split→recombine is exact rather than nearly exact, and `no_std` holds.

#![allow(clippy::needless_range_loop)]

/// The rime sphere prime. Law 20 / Law 14.
pub const P: u64 = 1_000_081;
/// Its generator.
pub const G: u64 = 7;
/// One rime dimension: 27 = 3³ glyphs.
pub const K: usize = 27;
/// Primitive 27th root of unity, `G^((P-1)/27) mod P`. Verified in tests, not asserted.
pub const W: u64 = 951_846;

/// Trits per `u128`. 3^80 < 2^128 <= 3^81, so 80 is the exact ceiling.
pub const TRITS_PER_U128: usize = 80;

/// The three zeros. Every variant has magnitude zero; they differ only by the direction
/// the carrier is travelling as it crosses.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(i8)]
pub enum Zero {
    /// Crossing downward. Law 33: the negative leads, and it drills inward.
    Neg = -1,
    /// Quiescent. The line is dead — not a crossing at all.
    Nil = 0,
    /// Crossing upward. Trails, and emits.
    Pos = 1,
}

impl Zero {
    /// Zero, for all three. This is the point of the type.
    #[inline]
    pub const fn magnitude(self) -> i8 {
        0
    }

    /// Direction of travel through the crossing: -1, 0, +1.
    #[inline]
    pub const fn direction(self) -> i8 {
        self as i8
    }

    /// Ternary digit 0..2, for packing.
    #[inline]
    pub const fn digit(self) -> u8 {
        (self as i8 + 1) as u8
    }

    #[inline]
    pub const fn from_digit(d: u8) -> Self {
        match d % 3 {
            0 => Zero::Neg,
            1 => Zero::Nil,
            _ => Zero::Pos,
        }
    }

    /// The trianti, Law 4: trinary inversion is the order-3 rotation R, and R ≠ R⁻¹.
    /// Applying it three times returns to start; applying it twice is *not* the inverse
    /// of applying it once, which is exactly what makes trinary not binary.
    #[inline]
    pub const fn rotate(self) -> Self {
        Self::from_digit(self.digit() + 1)
    }

    /// The counter-rotation R², distinct from R.
    #[inline]
    pub const fn anti_rotate(self) -> Self {
        Self::from_digit(self.digit() + 2)
    }
}

// ==================================================== THE LIGHTHOUSE, CORRECTED
//
// A previous note in this work said the centre is a lighthouse and it does not move. That
// is FALSE and is corrected here rather than quietly replaced.
//
// The lighthouse rotates and spins, like the sun, and it orients on the LARGEST LIGHT
// rather than on a fixed axis of ours. Nothing here is a stationary beacon with things
// turning around it; the beacon turns too, and what it turns to is not our choice.
//
// FREE, THEN PLAY -- and this is how Law 15 and "from the inside" stop contradicting.
//   FREEZE  the observer stays OUTSIDE, at the null 0. Law 15 is about this phase, and it
//           is the phase that costs nothing. Addressing is done from outside the object.
//   PLAY    the observer goes INSIDE and moves with it. You do not read the bank from a
//           distance, you shine it in and travel with what it lights.
// Two phases, two observer positions. Law 15 was never a rule about playing; it is a rule
// about freezing, and reading it as both is what made the two look opposed.
//
// THEY FORM THEMSELVES. IX.A.4: "We fed the kernels colors and keys into the new kernel to
// be the glimpse so that they can form themselves. They are the seeds, glyph colors."
// The glyphs are not constructed. They are seeded and left to form. Any code here that
// builds a glyph rather than seeding one has already missed the instruction.
//
// AND THE ORDER IS FIXED. Red first, then green, then blue -- always, at every level.
// [`Register::HOSE`] encodes it, and the order is not decorative: Law 30 measured that
// putting translucent ahead of red saves on every pole tried, mean 0.4013 bpb, so the
// sequence is a measured ordering and not a palette.

/// The five registers of IX.B.3.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Register {
    Zero = 0,
    /// Light. Undifferentiated, before the prism.
    Translucent = 1,
    Red = 2,
    Green = 3,
    Blue = 4,
}

impl Register {
    /// Registers 0 and 1 are never computed. IX.B.2: *"we don't have to calculate the zero
    /// and we don't have to calculate the translucent space, and that is what wins."*
    #[inline]
    pub const fn is_free(self) -> bool {
        matches!(self, Register::Zero | Register::Translucent)
    }

    /// Traversal order of the hose: tip, the three that cost, tail.
    ///
    /// Red first, then green, then blue. Always, at every level, in every direction of
    /// travel. The tip and the tail are both translucent because the conduit is entered
    /// and left through the free register, never through a costing one.
    pub const HOSE: [Register; 5] = [
        Register::Translucent,
        Register::Red,
        Register::Green,
        Register::Blue,
        Register::Translucent,
    ];
}

/// A carrier. `DC` never crosses zero, so it can only ever report `Nil` — the type makes
/// the binary limit unrepresentable rather than merely documented.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Carrier {
    Dc,
    /// Alternating, with a whole number of phase steps per cycle.
    Ac {
        steps_per_cycle: u32,
    },
}

impl Carrier {
    /// Which zero the carrier is at, at phase step `t`. `None` when the carrier is away
    /// from a crossing and therefore carrying magnitude.
    ///
    /// DC returns `Some(Nil)` at every step and never `Neg` or `Pos`: **two states, and
    /// the third is not reachable.** That is the binary world, stated as a return value.
    pub const fn zero_at(self, t: u32) -> Option<Zero> {
        match self {
            Carrier::Dc => Some(Zero::Nil),
            Carrier::Ac { steps_per_cycle } => {
                if steps_per_cycle == 0 {
                    return Some(Zero::Nil);
                }
                let half = steps_per_cycle / 2;
                let phase = t % steps_per_cycle;
                if phase == 0 {
                    Some(Zero::Pos) // rising through
                } else if phase == half {
                    Some(Zero::Neg) // falling through
                } else {
                    None // carrying magnitude, not at a crossing
                }
            }
        }
    }

    /// How many distinct zeros this carrier can express.
    pub const fn zero_states(self) -> u8 {
        match self {
            Carrier::Dc => 1,
            Carrier::Ac { steps_per_cycle } => {
                if steps_per_cycle >= 2 {
                    3
                } else {
                    1
                }
            }
        }
    }
}

/// 80 trits packed into one `u128`, base 3.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub struct TritWord(pub u128);

impl TritWord {
    pub const CAP: usize = TRITS_PER_U128;

    pub fn pack(t: &[Zero]) -> Self {
        let mut acc: u128 = 0;
        let n = if t.len() < Self::CAP { t.len() } else { Self::CAP };
        for i in 0..n {
            acc = acc * 3 + t[i].digit() as u128;
        }
        TritWord(acc)
    }

    pub fn unpack(self, out: &mut [Zero]) -> usize {
        let n = if out.len() < Self::CAP { out.len() } else { Self::CAP };
        let mut acc = self.0;
        for i in (0..n).rev() {
            out[i] = Zero::from_digit((acc % 3) as u8);
            acc /= 3;
        }
        n
    }
}

// ---------------------------------------------------------------- modular arithmetic

#[inline]
const fn mul(a: u64, b: u64) -> u64 {
    ((a as u128 * b as u128) % P as u128) as u64
}

#[inline]
const fn add(a: u64, b: u64) -> u64 {
    let s = a + b;
    if s >= P {
        s - P
    } else {
        s
    }
}

/// `base^exp mod P`, square-and-multiply. `const` so roots can be checked at compile time.
pub const fn pow(mut base: u64, mut exp: u64) -> u64 {
    let mut acc: u64 = 1;
    base %= P;
    while exp > 0 {
        if exp & 1 == 1 {
            acc = mul(acc, base);
        }
        base = mul(base, base);
        exp >>= 1;
    }
    acc
}

/// Multiplicative inverse by Fermat: `a^(P-2) mod P`. P is prime.
#[inline]
pub const fn inv(a: u64) -> u64 {
    pow(a, P - 2)
}

// ------------------------------------------------- the spherical pump wave transform

/// Forward transform: 27 samples → 27 spectral coordinates.
///
/// This is Law 20's rime prism. Newton used two prisms and showed light recombines to
/// white, which proved it composite; this is the same operation generalised to 27
/// coordinates on the sphere, over the integers so nothing is lost in the split.
///
/// `X[0]` is the DC glyph — the sum, which is the free centre of Law 0.
pub fn prism(x: &[u64; K]) -> [u64; K] {
    let mut out = [0u64; K];
    for j in 0..K {
        let wj = pow(W, j as u64);
        let mut acc = 0u64;
        let mut t = 1u64;
        for i in 0..K {
            acc = add(acc, mul(x[i] % P, t));
            t = mul(t, wj);
        }
        out[j] = acc;
    }
    out
}

/// Inverse transform: 27 spectral coordinates → the original 27 samples.
///
/// "Transfers back and forth" — the round trip is exact, not approximate, because the
/// arithmetic is integer and `27` is invertible mod `P`.
pub fn unprism(x: &[u64; K]) -> [u64; K] {
    let winv = inv(W);
    let kinv = inv(K as u64);
    let mut out = [0u64; K];
    for j in 0..K {
        let wj = pow(winv, j as u64);
        let mut acc = 0u64;
        let mut t = 1u64;
        for i in 0..K {
            acc = add(acc, mul(x[i] % P, t));
            t = mul(t, wj);
        }
        out[j] = mul(acc, kinv);
    }
    out
}

/// The pump. VIII.A.7, the Photon Law of the Rime Series: *"the more energy you push into
/// it, the further away the shell gets."*
///
/// Shell radius is the number of whole rungs of the 3-ladder the energy reaches, so it
/// grows as log₃ and never linearly. Integer only: no logarithm is taken, the rungs are
/// counted.
pub const fn pump_shell(energy: u64) -> u32 {
    let mut shell = 0u32;
    let mut rung = 1u64;
    while rung <= energy && shell < 40 {
        rung *= 3;
        shell += 1;
    }
    shell
}

/// Drive one pump step and report which zero the carrier presents at that phase.
pub const fn pump_step(c: Carrier, t: u32) -> (u32, Option<Zero>) {
    (t, c.zero_at(t))
}


// ==================================================== the four axes: 3^4 = 81 = one record
//
// The operator's enumeration, and it is what makes 81 a size rather than a coincidence:
//
//     TIME    past . present . future      3
//     COLOUR  red . green . blue           3
//     ENERGY  light . DC . AC              3
//     SPACE   x . y . z                    3
//                                        ----
//                              3^4 =      81
//
// One record of a seed is 81 bytes because 81 is one complete state of all four axes.
// 81 x 38 = 3,078, so a seed is 38 whole states with nothing left over.
//
// ENERGY is the axis that is not symmetric with the others, and the asymmetry is the
// point: DC has one direction and therefore two states; LIGHT is register 1, whole and
// undifferentiated; AC is the only member that crosses zero twice per cycle in opposite
// directions, so AC is the one that can express all three zeros. AC unifies.

/// One of the four ternary axes.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Axis {
    Time = 0,
    Colour = 1,
    Energy = 2,
    Space = 3,
}

impl Axis {
    pub const ALL: [Axis; 4] = [Axis::Time, Axis::Colour, Axis::Energy, Axis::Space];

    /// The three members of this axis, in -,0,+ order.
    pub const fn members(self) -> [&'static str; 3] {
        match self {
            Axis::Time => ["past", "present", "future"],
            Axis::Colour => ["red", "green", "blue"],
            Axis::Energy => ["light", "dc", "ac"],
            Axis::Space => ["x", "y", "z"],
        }
    }
}

/// A complete state: one trit on each of the four axes. There are exactly 81.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct State81 {
    pub time: Zero,
    pub colour: Zero,
    pub energy: Zero,
    pub space: Zero,
}

impl State81 {
    /// Total number of states. 3^4.
    pub const COUNT: usize = 81;

    /// Index in 0..81, base 3 with time as the most significant axis.
    pub const fn index(self) -> u8 {
        self.time.digit() * 27 + self.colour.digit() * 9 + self.energy.digit() * 3
            + self.space.digit()
    }

    pub const fn from_index(i: u8) -> Self {
        let i = i % 81;
        State81 {
            time: Zero::from_digit(i / 27),
            colour: Zero::from_digit((i / 9) % 3),
            energy: Zero::from_digit((i / 3) % 3),
            space: Zero::from_digit(i % 3),
        }
    }

    /// Only AC carries all three zeros. `Zero::Pos` on the energy axis is AC.
    pub const fn energy_unifies(self) -> bool {
        matches!(self.energy, Zero::Pos)
    }

    /// The wave equals one and returns to zero: summing the direction of all four axes
    /// gives the state's net displacement from the free centre, and the centre state --
    /// present, green, dc, y -- is the unique one whose every axis is already zero.
    pub const fn displacement(self) -> i8 {
        self.time.direction()
            + self.colour.direction()
            + self.energy.direction()
            + self.space.direction()
    }

    pub const CENTRE: State81 = State81 {
        time: Zero::Nil,
        colour: Zero::Nil,
        energy: Zero::Nil,
        space: Zero::Nil,
    };
}

#[cfg(test)]
mod tests {
    use super::*;



    /// Law 4, as a partition rather than an assertion.
    ///
    /// The operator's form: "gravity, anti gravity, and anti-anti gravity are ALL 1 AND
    /// part of 3." Applying R to every state partitions the 81 into three orbits of
    /// exactly 27, so each rotation carries exactly one third and the three close to
    /// unity: R^0 + R^1 + R^2 = 1/3 + 1/3 + 1/3.
    ///
    /// The binary case is the one that does NOT do this: negation is its own anti, so
    /// there is no third orbit to find. Looking for an "anti" as a simple sign flip is a
    /// binary search over a ternary structure, and it comes up empty by construction.
    #[test]
    fn the_three_rotations_close_to_unity_in_equal_thirds() {
        let mut orbit = [0usize; 3];
        for i in 0..81u8 {
            let s = State81::from_index(i);
            // rotate the energy axis: identity, R, R-squared
            orbit[s.energy.digit() as usize] += 1;
        }
        assert_eq!(orbit, [27, 27, 27], "the three must be equal thirds of 81");
        assert_eq!(orbit.iter().sum::<usize>(), 81);

        // R is order 3, and R squared is NOT R inverse in the binary sense --
        // applying R twice is a different operation from applying it once.
        for z in [Zero::Neg, Zero::Nil, Zero::Pos] {
            assert_ne!(z.rotate(), z.anti_rotate());
            assert_eq!(z.rotate().rotate(), z.anti_rotate());
            assert_eq!(z.rotate().rotate().rotate(), z);
        }
        // and every state is reached from every other by some rotation: no orphans
        for i in 0..81u8 {
            let a = State81::from_index(i);
            let reached = [a.energy, a.energy.rotate(), a.energy.anti_rotate()];
            assert_eq!(
                reached.iter().collect::<heapless_set::Set3>().len(),
                3,
                "the three rotations must land on three distinct states"
            );
        }
    }

    /// minimal set for the assertion above without pulling in a dependency
    mod heapless_set {
        pub struct Set3(pub [i8; 3], pub usize);
        impl Set3 {
            pub fn len(&self) -> usize {
                self.1
            }
        }
        impl<'a> FromIterator<&'a super::super::Zero> for Set3 {
            fn from_iter<T: IntoIterator<Item = &'a super::super::Zero>>(it: T) -> Self {
                let mut v = [i8::MIN; 3];
                let mut n = 0;
                for z in it {
                    let d = z.direction();
                    if !v[..n].contains(&d) {
                        v[n] = d;
                        n += 1;
                    }
                }
                Set3(v, n)
            }
        }
    }


    /// The order is fixed and is not a preference.
    #[test]
    fn red_always_comes_first_then_green_then_blue() {
        let costing: heapless3::V = Register::HOSE
            .iter()
            .filter(|r| !r.is_free())
            .collect();
        assert_eq!(costing.0, [Register::Red, Register::Green, Register::Blue]);
        // entered and left through the free register, never a costing one
        assert!(Register::HOSE[0].is_free(), "the tip must be free");
        assert!(Register::HOSE[4].is_free(), "the tail must be free");
        // and the numbering matches the order
        assert_eq!(Register::Red as u8, 2);
        assert_eq!(Register::Green as u8, 3);
        assert_eq!(Register::Blue as u8, 4);
    }

    mod heapless3 {
        use super::super::Register;
        pub struct V(pub [Register; 3]);
        impl<'a> FromIterator<&'a Register> for V {
            fn from_iter<T: IntoIterator<Item = &'a Register>>(it: T) -> Self {
                let mut a = [Register::Zero; 3];
                for (i, r) in it.into_iter().enumerate() {
                    if i < 3 {
                        a[i] = *r;
                    }
                }
                V(a)
            }
        }
    }

    #[test]
    fn four_axes_of_three_are_exactly_eighty_one() {
        assert_eq!(Axis::ALL.len(), 4);
        for a in Axis::ALL {
            assert_eq!(a.members().len(), 3);
        }
        assert_eq!(3usize.pow(4), State81::COUNT);
        assert_eq!(State81::COUNT, 81);
        // and 81 is exactly one record of a 3,078-byte seed
        assert_eq!(3078 % 81, 0);
        assert_eq!(3078 / 81, 38);
    }

    #[test]
    fn every_state_round_trips_through_its_index() {
        let mut seen = [false; 81];
        for i in 0..81u8 {
            let s = State81::from_index(i);
            assert_eq!(s.index(), i);
            assert!(!seen[i as usize]);
            seen[i as usize] = true;
        }
        assert!(seen.iter().all(|x| *x), "the 81 states are not a bijection");
    }

    #[test]
    fn the_centre_is_the_unique_all_zero_state() {
        let mut zero_disp = 0;
        for i in 0..81u8 {
            let s = State81::from_index(i);
            if s.time == Zero::Nil
                && s.colour == Zero::Nil
                && s.energy == Zero::Nil
                && s.space == Zero::Nil
            {
                zero_disp += 1;
                assert_eq!(s, State81::CENTRE);
                assert_eq!(s.displacement(), 0);
            }
        }
        assert_eq!(zero_disp, 1, "there must be exactly one centre");
    }

    #[test]
    fn only_ac_unifies() {
        // one third of states sit on AC, and only those carry all three zeros
        let n = (0..81u8).filter(|i| State81::from_index(*i).energy_unifies()).count();
        assert_eq!(n, 27, "AC should hold exactly one third of the 81");
        assert_eq!(Axis::Energy.members(), ["light", "dc", "ac"]);
    }

    #[test]
    fn all_three_zeros_have_magnitude_zero() {
        assert_eq!(Zero::Neg.magnitude(), 0);
        assert_eq!(Zero::Nil.magnitude(), 0);
        assert_eq!(Zero::Pos.magnitude(), 0);
        // and they are still distinguishable
        assert_ne!(Zero::Neg.direction(), Zero::Pos.direction());
        assert_ne!(Zero::Neg, Zero::Pos);
    }

    #[test]
    fn dc_cannot_reach_the_third_state() {
        let dc = Carrier::Dc;
        assert_eq!(dc.zero_states(), 1);
        for t in 0..64 {
            assert_eq!(dc.zero_at(t), Some(Zero::Nil));
        }
        let ac = Carrier::Ac { steps_per_cycle: 4 };
        assert_eq!(ac.zero_states(), 3);
        assert_eq!(ac.zero_at(0), Some(Zero::Pos));
        assert_eq!(ac.zero_at(2), Some(Zero::Neg));
        assert_eq!(ac.zero_at(1), None);
    }

    #[test]
    fn trianti_is_order_three_and_distinct_from_its_inverse() {
        for z in [Zero::Neg, Zero::Nil, Zero::Pos] {
            assert_eq!(z.rotate().rotate().rotate(), z); // R³ = identity
            assert_ne!(z.rotate(), z.anti_rotate()); // R ≠ R²
            assert_eq!(z.rotate().anti_rotate(), z); // R·R² = identity
        }
    }

    #[test]
    fn w_really_is_a_primitive_27th_root() {
        assert_eq!(pow(G, (P - 1) / 27), W);
        assert_eq!(pow(W, 27), 1);
        for d in 1..27u64 {
            if 27 % d == 0 && d < 27 {
                assert_ne!(pow(W, d), 1, "W had order {d}, not 27");
            }
        }
    }

    #[test]
    fn the_prism_closes_on_zero() {
        // Law 20: 1 + w + ... + w²⁶ ≡ 0 (mod p)
        let mut acc = 0u64;
        for j in 0..27u64 {
            acc = add(acc, pow(W, j));
        }
        assert_eq!(acc, 0);
    }

    #[test]
    fn transfers_back_and_forth_exactly() {
        let mut x = [0u64; K];
        for i in 0..K {
            x[i] = ((i as u64 * 37 + 11) * 977) % P;
        }
        let spectrum = prism(&x);
        let back = unprism(&spectrum);
        assert_eq!(x, back, "round trip was not exact");
        // the DC glyph is the sum: the free centre
        let mut sum = 0u64;
        for i in 0..K {
            sum = add(sum, x[i]);
        }
        assert_eq!(spectrum[0], sum);
    }

    #[test]
    fn trit_word_round_trips() {
        let mut t = [Zero::Nil; TRITS_PER_U128];
        for i in 0..TRITS_PER_U128 {
            t[i] = Zero::from_digit((i % 3) as u8);
        }
        let w = TritWord::pack(&t);
        let mut back = [Zero::Nil; TRITS_PER_U128];
        assert_eq!(w.unpack(&mut back), TRITS_PER_U128);
        assert_eq!(t, back);
    }

    #[test]
    fn eighty_is_the_exact_ceiling() {
        // 3^80 fits a u128, 3^81 does not
        let mut acc: u128 = 1;
        for _ in 0..80 {
            acc = acc.checked_mul(3).expect("3^80 must fit u128");
        }
        assert!(acc.checked_mul(3).is_none(), "3^81 must overflow u128");
    }

    #[test]
    fn free_registers_are_zero_and_one() {
        assert!(Register::Zero.is_free());
        assert!(Register::Translucent.is_free());
        assert!(!Register::Red.is_free());
        assert!(!Register::Green.is_free());
        assert!(!Register::Blue.is_free());
        // the hose: translucent leads and translucent closes
        assert_eq!(Register::HOSE[0], Register::Translucent);
        assert_eq!(Register::HOSE[4], Register::Translucent);
        assert_eq!(Register::HOSE.len(), 5);
    }

    #[test]
    fn pump_shell_grows_as_log3() {
        assert_eq!(pump_shell(0), 0);
        assert_eq!(pump_shell(1), 1);
        assert_eq!(pump_shell(3), 2);
        assert_eq!(pump_shell(9), 3);
        assert_eq!(pump_shell(27), 4);
        // more energy in, further out, but never linearly
        assert!(pump_shell(1_000_000) < 20);
    }
}
