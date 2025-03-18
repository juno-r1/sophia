use std::hash::Hash;

use malachite::num::basic::traits::Zero;
use malachite::Rational;

use crate::datatypes::functions::FuncDef;
use crate::datatypes::range::Range;
use crate::datatypes::sequence::Sequence;
use crate::datatypes::types::TypeDef;
use crate::internal::tokens::Token;

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
// Value constructors must take only 1 argument.
// This is because they have to work with std_fn!.
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
	pub fn new_list(x: Sequence) -> Value
	{
		Value::Sequence(Box::new(x))
	}
	pub fn new_record(x: Sequence) -> Value
	{
		Value::Sequence(Box::new(x))
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
			Token::Boolean(x) => Value::new_boolean(*x),
			Token::String(x) => Value::new_string(x.clone()),
			Token::Range => Value::new_range(Range::new(Rational::ZERO, Rational::ZERO, Rational::ZERO)),
			Token::List => Value::new_list(Sequence::new_list(vec![])),
			Token::Record => Value::new_record(Sequence::new_record(vec![], vec![])),
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
