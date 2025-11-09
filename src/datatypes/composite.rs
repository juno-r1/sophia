use crate::sophia::Value;
use crate::stdlib::Namespace;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Product {
    Unit,
    Single(Value),
    Tuple(Vec<Value>),
    Compound(Namespace),
}

impl Product
// Built-in product constructors.
{
    pub fn new_unit() -> Product
    {
        Product::Unit
    }
    pub fn new_single(value: Value) -> Product
    {
        Product::Single(value)
    }
    pub fn new_tuple(value: Vec<Value>) -> Product
    {
        Product::Tuple(value)
    }
    pub fn new_compound(value: Namespace) -> Product
    {
        Product::Compound(value)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Sum {
    pub tag: String,
    variant: Product,
}

impl Sum
// Built-in sum constructors.
{
    // Generic variant.
    pub fn new_variant(tag: &str, variant: Product) -> Sum
    {
        Sum{
            tag: tag.into(),
            variant
        }
    }
    // Option type.
    pub fn new_some(x: Value) -> Sum
    {
        Sum{
            tag: format!("Some"),
            variant: Product::new_single(x)
        }
    }
    pub fn new_none() -> Sum
    {
        Sum{
            tag: format!("None"),
            variant: Product::new_unit()
        }
    }
    // Result type.
    pub fn new_ok(x: Value) -> Sum
    {
        Sum{
            tag: format!("Ok"),
            variant: Product::new_single(x)
        }
    }
    pub fn new_error(x: Value) -> Sum
    {
        Sum{
            tag: format!("Error"),
            variant: Product::new_single(x)
        }
    }
}
