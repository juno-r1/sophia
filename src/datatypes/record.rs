use std::collections::BTreeMap;

// use malachite::{Natural, Rational};
// use malachite::num::basic::traits::One;
// use utils::coerce::Coerce;

use crate::sophia::arche::Value;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
// Custom implementation for insertion order keymap.
// Maps Key -> usize -> Value.
// Also tracks own length.
// Intended to be immutable, so doesn't need to implement in-place mutation.
pub struct Record {
    k: BTreeMap<Value, usize>,
    v: Vec<Value>,
    l: usize,
}

impl Record
{
    pub fn new(k: Vec<Value>, v: Vec<Value>) -> Record
    {
        if k.len() == v.len() {
            Record{
                k: BTreeMap::from_iter(
                    k.iter()
                    .enumerate()
                    .map(|(index, value)| (value.clone(), index))
                ),
                v,
                l: k.len()
            }
        } else {
            panic!("Keys and values incompatible");
        }
    }
}

impl Record
{
    pub fn safe_get(&self, index: Value) -> Option<&Value>
    // Index record without panic.
    {
        self.k.get(&index).and_then(|i| self.v.get(*i))

    }
}
