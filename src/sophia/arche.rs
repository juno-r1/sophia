use std::collections::BTreeMap;
use std::hash::Hash;

use malachite::Rational;

use crate::datatypes::functions::FuncDef;
use crate::datatypes::range::Range;
use crate::datatypes::sequence::Sequence;
use crate::datatypes::types::TypeDef;
use crate::internal::tokens::Token;

use super::runtime::Task;

// Enum of all concrete data types.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Value {
	Boolean(Box<bool>),
	Number(Box<Rational>),
	String(Box<String>),
	Range(Box<Range>),
	Sequence(Box<Sequence>),
	Function(Box<FuncDef>),
	Type(Box<TypeDef>),
	None,
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
	pub fn new_range(x: Range) -> Value
	{
		Value::Range(Box::new(x))
	}
	pub fn new_list(x: Vec<Value>) -> Value
	{
		Value::Sequence(Box::new(Sequence::new_list(&x)))
	}
	pub fn new_record(k: Vec<Value>, v: Vec<Value>) -> Value
	{
		Value::Sequence(Box::new(Sequence::new_record(&k, &v)))
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
	pub fn constant(token: &Token) -> Value
	// Map literals to constants.
	{
		match token {
			Token::Number(x) => Value::new_number(x.clone()),
			Token::String(x) => Value::new_string(x.clone()),
			Token::Boolean(x) => Value::new_boolean(*x),
			Token::List => Value::new_list(vec![]),
			Token::Record => Value::new_record(vec![], vec![]),
			_ => Value::new_none()
		}
	}
}

impl PartialOrd for Value
{
	fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering>
	{
		self.to_key().partial_cmp(&other.to_key())
	}
}

impl Ord for Value
{
	fn cmp(&self, other: &Self) -> std::cmp::Ordering
	{
		self.partial_cmp(other).unwrap()
	}
}

impl Value
{
	fn to_key(&self) -> String
	// Converts value to ordered hashable key.
	// Unstable implementation.
	{
		format!("{self:?}")
	}
}

pub type Function = fn(&mut Task, Vec<Value>) -> Result<Value, String>;
pub type Type = fn(Value) -> bool;
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
pub fn new_namespace() -> Namespace
// Generates the minimum required namespace.
{
	BTreeMap::from([
		(format!("0"), Value::new_none()),
		(format!("-1"), Value::new_none())
	])
}
pub fn infer_namespace(values: &Namespace) -> Typespace
// Build a typespace from a namespace.
{
	values
	.iter()
	.map(|(k, v)| (k.clone(), TypeDef::infer(v)))
	.collect()
}

#[macro_export]
macro_rules! std_mod
// Defines a standard library function with its associated dependencies.
{
	($name:ident; $(std_fn!$method:tt)+) => {
		pub mod $name
		{
			use macros::std_fn;

			use crate::error;
			use crate::sophia::arche::Value;
			use crate::sophia::runtime::Task;

			$(std_fn!$method)+
		}
	};
	($name:ident: {$($statement:item)+}; $(std_fn!$method:tt)+) => {
		pub mod $name
		{
			use macros::std_fn;

			use crate::error;
			use crate::sophia::arche::Value;
			use crate::sophia::runtime::Task;

			$($statement)+
			$(std_fn!$method)+
		}
	};
}