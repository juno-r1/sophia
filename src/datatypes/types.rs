use std::collections::HashMap;

use malachite::{Natural, Rational};
use malachite::num::basic::traits::{Zero, One};

use crate::sophia::arche::{Namespace, Value};
use crate::sophia::runtime::Task;

use super::methods::Predicate;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TypeDef {
	types: Vec<Predicate>,
	prototype: Value,
}

impl TypeDef
{
	pub fn new(types: Vec<Predicate>, prototype: Option<Value>) -> TypeDef
	{
		TypeDef{
			types,
			prototype: match prototype {
				Some(x) => x,
				None => Value::new_none()
			}
		}
	}
	pub fn from_super(supertype: &TypeDef, types: Vec<Predicate>, prototype: Option<Value>) -> TypeDef
	{
		let mut methods = supertype.types.clone();
		methods.extend(types);
		TypeDef{
			types: methods,
			prototype: match prototype {
				Some(x) => x,
				None => supertype.prototype.clone()
			}
		}
	}
// 		attributes = descriptor.split('.')
// 		datatype = types[attributes[0]]
// 		methods = []
// 		for item in attributes[1:]:
// 			name, value = item.split(':')
// 			try:
// 				value = int(value)
// 			except ValueError:
// 				value = types[value]
// 			methods.append(properties[name](value))
// 		return cls(datatype, *methods) # Create new typedef from base datatype
	pub fn read(descriptor: &str) -> TypeDef
	// Creates a TypeDef from a type descriptor.
	{
		match descriptor {
			"?" => TypeDef::new(vec![], None), // Infer return type.
			"any" => TypeDef::std_any(),
			"none" => TypeDef::std_none(),
			"some" => TypeDef::std_some(),
			"boolean" => TypeDef::std_boolean(),
			"number" => TypeDef::std_number(),
			"integer" => TypeDef::std_integer(),
			"string" => TypeDef::std_string(),
			_ => panic!("Type not currently supported")
		}
	}
// types = {
// 	'any': std_any,
// 	'none': std_none,
// 	'some': std_some,
// 	'type': std_type,
// 	'function': std_function,
// 	'boolean': std_boolean,
// 	'number': std_number,
// 	'integer': std_integer,
// 	'sequence': std_sequence,
// 	'string': std_string,
// 	'list': std_list,
// 	'record': std_record,
// 	'slice': std_slice,
// 	'future': std_future
// }
// properties = {
// 	'element': cls_element,
// 	'length': cls_length
// }
	pub fn check(&self, predicate: Predicate) -> bool
	// Universal dispatch check exploiting properties of structural typing.
	{
		self.types
		.iter()
		.find(|x| **x == predicate)
		.is_some()
	}
	pub fn criterion(&self, other: Self) -> Option<Predicate>
	// 	Gets the most specific predicate that two typedefs don't share.
	// 	This operation is non-commutative.
	{
		let criteria: Vec<Predicate> = self.types
			.iter()
			.filter_map(
				|x| {
					for y in other.clone().types {
						if *x == y {
							return None
						}
					}
					Some(x.clone())
				}
			).collect();
		match criteria.last() {
			Some(x) => Some(x.clone()),
			None => None
		}
	}
}
// Standard library types.
impl TypeDef
{
	pub fn stdlib() -> Namespace
	{
		// Produces a key-value pair with a standard library type.
		macro_rules! new_type {
			($name:expr, $method:ident) => {
				($name.into(), Value::new_type(TypeDef::$method()))
			};
		}
		// Produces the standard type namespace.
		HashMap::from(
			[
				new_type!("any", std_any),
				new_type!("none", std_none),
				new_type!("some", std_some),
				new_type!("boolean", std_boolean),
				new_type!("number", std_number),
				new_type!("integer", std_integer),
				new_type!("string", std_string),
			]
		)
	}
	fn std_any() -> TypeDef
	{
		TypeDef::new(
			vec![
				Predicate::new_predicate_base(
					"any",
					Task::type_any
				)
			],
			None
		)
	}
	fn std_none() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_any(),
			vec![
				Predicate::new_predicate_base(
					"none",
					Task::type_none
				)
			],
			Some(Value::new_none())
		)
	}
	fn std_some() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_any(),
			vec![
				Predicate::new_predicate_base(
					"some",
					Task::type_some
				)
			],
			None
		)
	}
	fn std_boolean() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			vec![
				Predicate::new_predicate_base(
					"boolean",
					Task::type_boolean
				)
			],
			Some(Value::new_boolean(true))
		)
	}
	fn std_number() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			vec![
				Predicate::new_predicate_base(
					"number",
					Task::type_number
				)
			],
			Some(Value::new_number(Rational::ZERO))
		)
	}
	fn std_integer() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_number(),
			vec![
				Predicate::new_predicate_base(
					"integer",
					Task::type_integer
				)
			],
			None
		)
	}
	fn std_string() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			vec![
				Predicate::new_predicate_base(
					"string",
					Task::type_string
				)
			],
			Some(Value::new_string(String::new()))
		)
	}
}

impl Task
{
	pub fn type_any(self, _: Vec<Value>) -> Value
	{
		Value::new_boolean(true)
	}
	pub fn type_none(self, args: Vec<Value>) -> Value
	{
		match args[0] {
			Value::None => Value::new_boolean(true),
			_ => Value::new_boolean(false)
		}
	}
	pub fn type_some(self, args: Vec<Value>) -> Value
	{
		match args[0] {
			Value::None => Value::new_boolean(false),
			_ => Value::new_boolean(true)
		}
	}
	pub fn type_boolean(self, args: Vec<Value>) -> Value
	{
		match args[0] {
			Value::Boolean(_) => Value::new_boolean(true),
			_ => Value::new_boolean(false)
		}
	}
	pub fn type_number(self, args: Vec<Value>) -> Value
	{
		match args[0] {
			Value::Number(_) => Value::new_boolean(true),
			_ => Value::new_boolean(false)
		}
	}
	pub fn type_integer(self, args: Vec<Value>) -> Value
	{
		match args[0].clone() {
			Value::Number(x) if x.denominator_ref() == &Natural::ONE => Value::new_boolean(true),
			_ => Value::new_boolean(false)
		}
	}
	pub fn type_string(self, args: Vec<Value>) -> Value
	{
		match args[0] {
			Value::String(_) => Value::new_boolean(true),
			_ => Value::new_boolean(false)
		}
	}
}