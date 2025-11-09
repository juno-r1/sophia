use std::hash::{DefaultHasher, Hash};

use malachite::Rational;

use crate::datatypes::{Sum, FuncDef, Range, Record, Product, TypeDef};
use crate::parser::{patterns, Node};

// Enum of all concrete data types.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Value {
	Boolean(Box<bool>),
	Number(Box<Rational>),
	String(Box<String>),
	Range(Box<Range>),
	List(Box<Vec<Value>>),
	Record(Box<Record>),
	Function(Box<FuncDef>),
	Type(Box<TypeDef>),
	Sum(Box<Sum>),
	Struct(Box<Product>),
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
	pub fn new_list(x: Vec<Value>) -> Value
	{
		Value::List(Box::new(x))
	}
	pub fn new_record(x: Record) -> Value
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
	pub fn new_sum(x: Sum) -> Value
	{
		Value::Sum(Box::new(x))
	}
	pub fn new_struct(x: Product) -> Value
	{
		Value::Struct(Box::new(x))
	}
}

impl PartialOrd for Value
{
	fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering>
	{
		let mut hasher = DefaultHasher::new();
		self.hash(&mut hasher).partial_cmp(&other.hash(&mut hasher))
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
// Testing utilities.
{
	pub fn test(source: &str) -> Value
	// Test utility for parsing a value from a string.
	{
		let tree: Node = Node::tree(&patterns::normalise(source)).expect(&format!("Invalid test value: {source}"));
		tree.constant()
	}
	pub fn assert(self, other: &str)
	{
		assert_eq!(self, Value::test(other));
	}
	pub fn assert_type(self, other: TypeDef)
	{
		match self {
			Value::Type(x) => assert_eq!(*x, other),
			_ => panic!()
		}
	}
	// pub fn assert_true(self)
    // {
    //     assert_eq!(self, Value::new_boolean(true))
    // }
    // pub fn assert_false(self)
    // {
    //     assert_eq!(self, Value::new_boolean(false))
    // }
    // pub fn assert_null(self)
    // {
    //     assert_eq!(self, Value::new_none())
    // }
    // pub fn assert_number(self, value: &str)
    // {
    //     assert_eq!(self, Value::new_number(value.to_rational().unwrap()));
    // }
    // pub fn assert_string(self, value: &str)
    // {
    //     assert_eq!(self, Value::new_string(value.into()));
    // }
    // pub fn assert_type(self, typedef: TypeDef)
    // {
    //     assert_eq!(self, Value::new_type(typedef))
    // }
}
