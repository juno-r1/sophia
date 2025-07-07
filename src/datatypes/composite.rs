use crate::sophia::Value;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Enum {
    tag: String,
    variant: Variant,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Variant {
    // No value.
    Unit,
    // 1 value (optimisation of Tuple).
    Single(Value),
    // Multiple values.
    Tuple(Vec<Value>),
    // Struct-like.
    Struct,
}
