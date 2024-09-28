use std::collections::{BTreeMap, HashMap};

use malachite::Rational;

use crate::datatypes::functions::FuncDef;
use crate::datatypes::types::TypeDef;

use crate::sophia::runtime::Task;

// Enum of all concrete data types.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Value {
	Boolean(Box<bool>),
	Number(Box<Rational>),
	String(Box<String>),
	List(Box<Vec<Value>>),
	Record(Box<BTreeMap<Value, Value>>),
	Function(Box<FuncDef>),
	Type(Box<TypeDef>),
	None,
	Err
}

impl Value
{
	
	pub fn new_any(x: Value) -> Value
	{
		x
	}
	pub fn new_boolean(x: bool) -> Value
	{
		Value::Boolean(Box::new(x))
	}
	pub fn new_number(x: Rational) -> Value
	{
		Value::Number(Box::new(x))
	}
	pub fn new_string(x: String) -> Value
	{
		Value::String(Box::new(x))
	}
	pub fn new_list(x: Vec<Value>) -> Value
	{
		Value::List(Box::new(x))
	}
	pub fn new_record(x: BTreeMap<Value, Value>) -> Value
	{
		Value::Record(Box::new(x))
	}
	pub fn new_function(x: FuncDef) -> Value
	{
		Value::Function(Box::new(x))
	}
	pub fn new_type(x: TypeDef) -> Value
	{
		Value::Type(Box::new(x))
	}
	pub fn new_none() -> Value
	{
		Value::None
	}
}

pub type Function = fn(&mut Task, Vec<Value>) -> Value;

pub type Namespace = HashMap<String, Value>;
pub type Typespace = HashMap<String, TypeDef>;

pub fn stdlib() -> Namespace
// Build the standard library.
{
	let mut namespace: Namespace = HashMap::new();
	//namespace.extend(TypeDef::stdlib());
	namespace.extend(FuncDef::stdlib());
	namespace
}
pub fn infer_namespace(values: &Namespace) -> Typespace
// Build a typespace from a namespace.
{
	values
	.iter()
	.map(
		|(k, v)| {
			(k.clone(), TypeDef::infer(v))
		}
	).collect()
}