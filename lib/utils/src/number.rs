use malachite::Rational;

pub fn modulo(x: Rational, y: Rational) -> Rational
// Implementation borrowed from Python's Rational module.
// Malachite doesn't implement modulo for Rationals, but it does for Naturals.
// Modulo and remainder are equivalent operations for Naturals.
// Panics if y is 0.
{
    let (nx, dx) = x.into_numerator_and_denominator();
    let (ny, dy) = y.into_numerator_and_denominator();
    let (a, b) = (nx * &dy, ny * &dx);
    Rational::from_naturals(
        ((a % &b) + &b) % &b,
        &dx * &dy
    )
}
