use std::ops::{Add, Div, Mul, Neg, Sub};

use malachite::num::arithmetic::traits::Abs;
use malachite::Rational;
use malachite::num::basic::traits::One;
use utils::coerce::Coerce;
use utils::number::modulo;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Range {
    start: Rational,
    end: Rational,
    step: Rational,
}

impl Range
{
    pub fn new(start: Rational, end: Rational, step: Rational) -> Range
    {
        Range{
            start,
            end,
            step,
        }
    }
    pub fn contains(&self, x: &Rational) -> bool
    {
        self.step != 0
        && &self.start <= x
        && x <= &self.end
        && ((x - &self.start) / &self.step).into_denominator() == Rational::ONE
    }
    pub fn get(&self, index: usize) -> Option<Rational>
    // Enables O(1) indexing without mutation.
    {
        let i = Rational::from(index);
        if self.step == 0 {
            return None;
        };
        let x = if i >= 0 {
            &self.start + &self.step * i
        } else {
            &self.end + &self.step * (i + Rational::ONE)
        };
        if self.start <= x && x <= self.end {
            Some(x)
        } else {
            None
        }
    }
    pub fn len(&self) -> usize
    {
        if self.step == 0 {
            0
        } else {
            ((&self.end - &self.start) / &self.step).to_usize() + 1
        }
    }
}

impl Abs for Range
{
    type Output = Range;

    fn abs(self) -> Self::Output
    // Invert sequence if descending.
    {
        if self.step < 0 {
            Range::new(
                self.end.clone(),
                self.start.clone(),
                -self.step
            )
        } else {
            self
        }
    }
}

impl Neg for Range
{
    type Output = Range;

    fn neg(self) -> Self::Output
    {
        Range::new(
            self.end.clone(),
            self.start.clone(),
            -self.step
        )
    }
}

impl Add<Rational> for Range
{
    type Output = Range;

    fn add(self, rhs: Rational) -> Self::Output
    // Adds to the arithmetic sequence.
    {
        Range::new(
            self.start + &rhs,
            self.end + &rhs,
            self.step
        )
    }
}

impl Sub<Rational> for Range
{
    type Output = Range;

    fn sub(self, rhs: Rational) -> Self::Output
    // Subtracts from the arithmetic sequence.
    {
        Range::new(
            self.start - &rhs,
            self.end - &rhs,
            self.step
        )
    }
}

impl Mul<Rational> for Range
{
    type Output = Range;

    fn mul(self, rhs: Rational) -> Self::Output
    // Multiplies the arithmetic sequence.
    {
        Range::new(
            self.start * &rhs,
            self.end * &rhs,
            self.step * &rhs
        )
    }
}

impl Div<Rational> for Range
{
    type Output = Range;

    fn div(self, rhs: Rational) -> Self::Output
    // Divides the arithmetic sequence.
    {
        Range::new(
            self.start / &rhs,
            self.end / &rhs,
            self.step / &rhs
        )
    }
}

impl Range
// Set operations.
{
    pub fn intersection(self, other: Range) -> Range
    // Creates a range containing the numbers in both inputs.
    {
        let (mut n, mut m) = (self.step.clone(), other.step.clone());
        // Euclidean algorithm for greatest common divisor.
        while m != 0 {
            (n, m) = (m.clone(), modulo(n, m.clone()));
        };

        self
    }
    // n, m = self.step, other.step
    // while m != 0: # Euclidean algorithm for greatest common divisor
    // 	n, m = m, n % m
    // if n % (other.start - self.start) == 0: # Solution for intersection of slices
    // 	step = (self.step * other.step) / n # Step of intersection
    // 	ranges = [self.start, self.end, other.start, other.end].sort()
    // 	lower, upper = ranges[1], ranges[2]
    // 	lower = lower - (lower % step) + step # Gets highest lower bound
    // 	upper = upper - (upper % step) # Gets lowest upper bound
    // 	return slice(lower, upper, m)
}

impl Iterator for Range
{
    type Item = Rational;

    fn next(&mut self) -> Option<Self::Item>
    // Uses self.start as the accumulator.
    {
        if self.step == 0 {
            return None;
        };
        let x = self.start.clone();
        self.start += &self.step;
        if
            (self.step >= 0 && x > self.end) ||
            (self.step < 0 && x < self.end)
        {
            None
        } else {
            Some(x)
        }
    }
}

impl ToString for Range
{
    fn to_string(&self) -> String
    {
        format!(
            "{:}:{:}:{:}",
            self.start,
            self.end,
            self.step
        )
    }
}
