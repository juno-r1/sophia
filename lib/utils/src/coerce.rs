use malachite::Rational;
use malachite::num::conversion::traits::RoundingInto;
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
    fn to_vec<T>(&self) -> Vec<T>
    {
        panic!("Unimplemented coerce to Vec")
    }
    fn keys_into_vec<T>(&self) -> Vec<T>
    {
        panic!("Unimplemented coerce to Vec")
    }
    fn values_into_vec<T>(&self) -> Vec<T>
    {
        panic!("Unimplemented coerce to Vec")
    }
}

impl <'a> Coerce for Match<'a>
{
    fn to_string(&self) -> String
    {
        self
        .as_str()
        .to_string()
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