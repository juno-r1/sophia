use malachite::Rational;
use malachite::num::basic::traits::One;

#[derive(Debug, Clone, PartialEq, Eq)]
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
        &self.start <= x
        && x <= &self.end
        && ((x - &self.start) / &self.step).into_denominator() == Rational::ONE
    }
    pub fn get(&self, index: Rational) -> Option<Rational>
    // Enables O(1) indexing without mutation.
    {
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
        ((&self.end - &self.start) / &self.step) + Rational::ONE
    }
}

impl Iterator for Range
{
    type Item = Rational;

    fn next(&mut self) -> Option<Self::Item>
    // Uses self.start as the accumulator.
    {
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