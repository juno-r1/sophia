use std::collections::BTreeMap;
use std::ops::Index;

use malachite::{Natural, Rational};
use malachite::num::basic::traits::One;
use utils::coerce::Coerce;

use crate::sophia::arche::Value;

type KeyMap = BTreeMap<Value, usize>;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
// Custom sequence implementation.
// Insertion order list or record.
// If KeyMap is present, maps values to values.
// This is done by mapping Key -> usize -> Value.
// Also tracks own length.
// Intended to be immutable, so doesn't need to implement in-place mutation.
pub struct Sequence {
    k: Option<KeyMap>,
    v: Vec<Value>,
    l: usize,
}

impl Sequence
{
    pub fn new_list(x: &Vec<Value>) -> Sequence
    {
        Sequence{
            k: None,
            v: x.clone(),
            l: x.len()
        }
    }
    pub fn new_record(k: &Vec<Value>, v: &Vec<Value>) -> Sequence
    {
        if k.len() == v.len() {
            Sequence{
                k: Some(
                    BTreeMap::from_iter(
                        k.iter()
                        .enumerate()
                        .map(|(index, value)| (value.clone(), index))
                    )
                ),
                v: v.clone(),
                l: k.len()
            }
        } else {
            panic!("Keys and values incompatible");
        }
    }
}

impl Index<Rational> for Sequence
{
    type Output = Value;

    fn index(&self, index: Rational) -> &Self::Output
    {
        match self {
            Sequence{k: None, v, l} => {
                // Integer indices only!
                if index.denominator_ref() != &Natural::ONE {
                    panic!("Index {index} out of bounds")
                };
                // Convert index to usize to play nice with Rust.
                let i: usize = if index >= 0 {
                    index.to_usize()
                } else if -(&index) > *l {
                    *l - index.to_usize()
                } else {
                    panic!("Index {index} out of bounds");
                };
                // Use normalised index.
                // Rust is smart enough to know that usize can't be less than 0.
                if &i < l {
                    &v[i]
                } else {
                    panic!("Index {index} out of bounds");
                }
            },
            Sequence{..} => panic!("Invalid index of record"),
        }
    }
}

impl Index<Value> for Sequence
{
    type Output = Value;

    fn index(&self, index: Value) -> &Self::Output
    {
        match self {
            Sequence{k: Some(k), v, ..} => {
                if k.contains_key(&index) {
                    &v[k[&index]]
                } else {
                    panic!("Record has no key {:?}", index);
                }
            },
            Sequence{..} => panic!("Invalid index of list"),
        }
    }
}

impl Sequence
{
    pub fn has_keys(&self) -> bool
    {
        self.k.is_some()
    }
}