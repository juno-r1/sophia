use std::collections::BTreeMap;

use crate::datatypes::{FuncDef, TypeDef};
use crate::sophia::Value;

pub type Namespace = BTreeMap<String, Value>;
pub type Typespace = BTreeMap<String, TypeDef>;

pub fn stdlib(user: Namespace) -> Namespace
// Build the standard library.
{
	let mut namespace: Namespace = user;
	namespace.extend(TypeDef::stdlib());
	namespace.extend(FuncDef::stdlib());
	namespace
}
pub fn new() -> Namespace
// Generates the minimum required namespace.
{
	BTreeMap::from([])
}
pub fn infer(values: &Namespace) -> Typespace
// Build a typespace from a namespace.
{
	values
	.iter()
	.map(|(k, v)| (k.clone(), TypeDef::infer(v)))
	.collect()
}
