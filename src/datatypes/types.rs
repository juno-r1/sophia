use std::collections::BTreeMap;

use malachite::{Natural, Rational};
use malachite::num::basic::traits::{Zero, One};

use crate::sophia::arche::{Namespace, Value};
use crate::sophia::runtime::Task;

use super::methods::Predicate;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
	pub fn infer(value: &Value) -> TypeDef
	{
		match value {
			Value::None => TypeDef::std_none(),
			Value::Number(x) if x.denominator_ref() == &Natural::ONE => TypeDef::std_integer(),
			Value::Number(_) => TypeDef::std_number(),
			Value::Boolean(_) => TypeDef::std_boolean(),
			Value::String(_) => TypeDef::std_string(),
			Value::Range(_) => TypeDef::std_range(),
			Value::Sequence(x) if x.has_keys() => TypeDef::std_record(),
			Value::Sequence(_) => TypeDef::std_list(),
			Value::Function(_) => TypeDef::std_any(),
			Value::Type(_) => TypeDef::std_any(),
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
			"sequence" => TypeDef::std_sequence(),
			"string" => TypeDef::std_string(),
			"range" => TypeDef::std_range(),
			"list" => TypeDef::std_list(),
			"record" => TypeDef::std_record(),
			"function" => TypeDef::std_function(),
			"type" => TypeDef::std_type(),
			_ => panic!("Type not supported")
		}
	}
	pub fn call(&self, value: &Value) -> bool
	{
		self.types
		.iter()
		.all(|predicate| {predicate.call(value)})
	}
	pub fn check(&self, predicate: &Predicate) -> bool
	// Universal dispatch check exploiting properties of structural typing.
	{
		self.types
		.iter()
		.find(|x| *x == predicate)
		.is_some()
	}
	pub fn criterion(&self, other: &Self) -> Option<&Predicate>
	// Gets the most specific predicate that two typedefs don't share.
	// This operation is non-commutative.
	{
		let criteria: Vec<&Predicate> = self.types
			.iter()
			.filter_map(
				|x| {
					for y in &other.types {
						if *x == *y {
							return None
						}
					}
					Some(x)
				}
			).collect();
		match criteria.last() {
			Some(x) => Some(x),
			None => None
		}
	}
}
impl PartialOrd for TypeDef
// Structural typing relations.
{
	fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering>
	// 	Subtype relation.
	// 	Returns:
	//	Less if self is a strict subtype of other;
	//	Greater if self is not a strict subtype of other;
	//	Equal if self and other are equal.
	{
		if self.types == other.types {
			Some(std::cmp::Ordering::Equal)
		} else {
			let criteria: Vec<&Predicate> = other.types
				.iter()
				.filter_map(
					|x| {
						for y in &self.types {
							if *x == *y {
								return None
							}
						}
						Some(x)
					}
				).collect();
			if criteria.len() == 0 {
				Some(std::cmp::Ordering::Less)
			} else {
				Some(std::cmp::Ordering::Greater)
			}
		}	
	}
}
impl Ord for TypeDef
// Structural typing relations.
{
	fn cmp(&self, other: &Self) -> std::cmp::Ordering
	{
		self.partial_cmp(other).unwrap()
	}
}
impl TypeDef
// Standard library types.
{
	pub fn stdlib() -> Namespace
	{
		// Produces a key-value pair with a standard library type.
		macro_rules! new_type
		{
			($name:expr, $method:ident) => {
				($name.into(), Value::new_type(TypeDef::$method()))
			};
		}
		// Produces the standard type namespace.
		BTreeMap::from(
			[
				new_type!("any", std_any),
				new_type!("none", std_none),
				new_type!("some", std_some),
				new_type!("boolean", std_boolean),
				new_type!("number", std_number),
				new_type!("integer", std_integer),
				new_type!("sequence", std_sequence),
				new_type!("string", std_string),
				new_type!("range", std_range),
				new_type!("list", std_list),
				new_type!("record", std_record),
				new_type!("function", std_function),
				new_type!("type", std_type),
			]
		)
	}
	pub fn std_any() -> TypeDef
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
	pub fn std_none() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_any(),
			vec![
				Predicate::new_predicate_base(
					"none",
					Task::type_none
				)
			],
			None
		)
	}
	pub fn std_some() -> TypeDef
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
	pub fn std_boolean() -> TypeDef
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
	pub fn std_number() -> TypeDef
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
	pub fn std_integer() -> TypeDef
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
	pub fn std_sequence() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			vec![
				Predicate::new_predicate_base(
					"sequence",
					Task::type_sequence
				)
			],
			None
		)
	}
	pub fn std_string() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_sequence(),
			vec![
				Predicate::new_predicate_base(
					"string",
					Task::type_string
				)
			],
			Some(Value::new_string(String::new()))
		)
	}
	pub fn std_range() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_sequence(),
			vec![
				Predicate::new_predicate_base(
					"range",
					Task::type_range
				)
			],
			None
		)
	}
	pub fn std_list() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_sequence(),
			vec![
				Predicate::new_predicate_base(
					"list",
					Task::type_list
				)
			],
			None
		)
	}
	pub fn std_record() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_sequence(),
			vec![
				Predicate::new_predicate_base(
					"record",
					Task::type_record
				)
			],
			None
		)
	}
	pub fn std_function() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			vec![
				Predicate::new_predicate_base(
					"function",
					Task::type_function
				)
			],
			None
		)
	}
	pub fn std_type() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			vec![
				Predicate::new_predicate_base(
					"type",
					Task::type_type
				)
			],
			None
		)
	}
}

impl Task
// Standard library predicates.
{
	pub fn type_any(_: Value) -> bool
	{
		true
	}
	pub fn type_none(value: Value) -> bool
	{
		match value {
			Value::None => true,
			_ => false
		}
	}
	pub fn type_some(value: Value) -> bool
	{
		match value {
			Value::None => false,
			_ => true
		}
	}
	pub fn type_boolean(value: Value) -> bool
	{
		match value {
			Value::Boolean(_) => true,
			_ => false
		}
	}
	pub fn type_number(value: Value) -> bool
	{
		match value {
			Value::Number(_) => true,
			_ => false
		}
	}
	pub fn type_integer(value: Value) -> bool
	{
		match value {
			Value::Number(x) if x.denominator_ref() == &Natural::ONE => true,
			_ => false
		}
	}
	pub fn type_sequence(value: Value) -> bool
	{
		match value {
			| Value::String(_)
			| Value::Range(_)
			| Value::Sequence(_) => true,
			_ => false
		}
	}
	pub fn type_string(value: Value) -> bool
	{
		match value {
			Value::String(_) => true,
			_ => false
		}
	}
	pub fn type_range(value: Value) -> bool
	{
		match value {
			Value::Range(_) => true,
			_ => false
		}
	}
	pub fn type_list(value: Value) -> bool
	{
		match value {
			Value::Sequence(x) if !x.has_keys() => true,
			_ => false
		}
	}
	pub fn type_record(value: Value) -> bool
	{
		match value {
			Value::Sequence(x) if x.has_keys() => true,
			_ => false
		}
	}
	pub fn type_function(value: Value) -> bool
	{
		match value {
			Value::Function(_) => true,
			_ => false
		}
	}
	pub fn type_type(value: Value) -> bool
	{
		match value {
			Value::Type(_) => true,
			_ => false
		}
	}
}