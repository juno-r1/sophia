use std::collections::BTreeMap;
use std::hash::Hash;

use malachite::num::basic::traits::Zero;
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

#[macro_export]
macro_rules! new_fn
// Creates a standard library function.
// Deserialises signature file, then constructs function from methods.
{
	($name:expr) => {
		($name.into(), Value::new_function(FuncDef::new(vec![])))
	};
	($name:expr, $($method:ident),*) => {{
		let metadata: Metadata = serde_json::from_str(
			&std::fs::read_to_string(
				std::fs::canonicalize(
					current_dir()
					.expect("Couldn't find signature file")
					.join(format!("src/stdlib/{:}.json", $name))
				).expect("Couldn't canonicalise signature file")
			).expect("Couldn't read signature file")
		).expect("Couldn't deserialise signature file");
		(metadata.name.into(), Value::new_function(FuncDef::new(vec![$(
			Method::new_method_std(
				Task::$method,
				{
					let data = &metadata.methods
						.get(stringify!($method))
						.expect("Couldn't find method signature");
					let mut signature = vec![$name.into()];
					signature.extend(
						data.signature
						.iter()
						.map(|_| format!("_"))
					);
					signature
				},
				{
					let data = &metadata.methods
						.get(stringify!($method))
						.expect("Couldn't find method signature");
					let mut signature = vec![TypeDef::read(&data.returns)];
					signature.extend(
						data.signature
						.iter()
						.map(|x| TypeDef::read(x))
					);
					signature
				}
			)
		),*])))
	}};
}