use std::ops::{Add, Div, Mul, Neg, Sub};

use malachite::num::arithmetic::traits::Abs;
use malachite::Rational;
use malachite::num::basic::traits::{One, Zero};

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
    pub fn get(&self, index: Rational) -> Option<Rational>
    // Enables O(1) indexing without mutation.
    {
        if self.step == 0 {
            return None;
        };
        let x = if index >= 0 {
            &self.start + &self.step * index
        } else {
            &self.end + &self.step * (index + Rational::ONE)
        };
        if self.start <= x && x <= self.end {
            Some(x)
        } else {
            None
        }
    }
    pub fn len(&self) -> Rational
    {
        if self.step == 0 {
            Rational::ZERO
        } else {
            ((&self.end - &self.start) / &self.step) + Rational::ONE
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