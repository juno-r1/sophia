use std::str::FromStr;

use malachite::Rational;
use malachite::num::conversion::traits::{FromSciString, RoundingInto};
use malachite::rounding_modes::RoundingMode;
use regex::Match;

pub trait Coerce
{
    fn to_string(&self) -> String
    {
        panic!("Unimplemented coerce to string")
    }
    fn to_usize(&self) -> usize
    {
        panic!("Unimplemented coerce to usize")
    }
    fn to_isize(&self) -> isize
    {
        panic!("Unimplemented coerce to isize")
    }
    fn to_rational(&self) -> Option<Rational>
    {
        panic!("Unimplemented coerce to rational")
    }
}

impl Coerce for str
{
    fn to_rational(&self) -> Option<Rational>
    {
        if self.contains('.') || self.contains('e') {
            Rational::from_sci_string(self)
        } else {
            Rational::from_str(self).ok()
        }
    }
}

impl <'a> Coerce for Match<'a>
{
    fn to_string(&self) -> String
    {
        ToString::to_string(self.as_str())
    }
}

impl Coerce for Rational
{
    fn to_usize(&self) -> usize
    {
        RoundingInto::<usize>::rounding_into(
            self,
            RoundingMode::Down
        ).0
    }
    fn to_isize(&self) -> isize
    {
        RoundingInto::<isize>::rounding_into(
            self,
            RoundingMode::Down
        ).0
    }
}