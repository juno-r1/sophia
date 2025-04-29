use malachite::Natural;
use malachite::num::basic::traits::One;

use crate::sophia::Value;

use super::predicates::Predicate;

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct TypeDef {
	predicates: Vec<Predicate>,
	prototype: Value,
}

impl TypeDef
{
	pub fn new() -> TypeDef
	{
		TypeDef{
			predicates: vec![],
			prototype: Value::new_none()
		}
	}
	pub fn from_super(supertype: &TypeDef, predicate: Predicate, prototype: Option<Value>) -> TypeDef
	{
		let mut methods = supertype.predicates.clone();
		methods.push(predicate);
		TypeDef{
			predicates: methods,
			prototype: prototype.unwrap_or(supertype.prototype.clone())
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
			Value::List(_) => TypeDef::std_list(),
			Value::Record(_) => TypeDef::std_record(),
			Value::Function(_) => TypeDef::std_any(),
			Value::Type(_) => TypeDef::std_any(),
		}
	}
	pub fn read(descriptor: &str) -> TypeDef
	// Creates a TypeDef from a type descriptor.
	{
		match descriptor {
			"?" => TypeDef::new(), // Infer return type.
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
			_ => panic!("Type not supported: {}", descriptor)
		}
	}
	pub fn call(&self, value: &Value) -> bool
	{
		self.predicates
		.iter()
		.all(|predicate| {predicate.call(value)})
	}
	pub fn check(&self, predicate: &Predicate) -> bool
	// Universal dispatch check exploiting properties of structural typing.
	{
		self.predicates
		.iter()
		.find(|x| *x == predicate)
		.is_some()
	}
	pub fn criterion(&self, other: &Self) -> Option<&Predicate>
	// Gets the most specific predicate that two typedefs don't share.
	// This operation is non-commutative.
	{
		let criteria: Vec<&Predicate> = self.predicates
			.iter()
			.filter_map(
				|x| {
					for y in &other.predicates {
						if *x == *y {
							return None
						}
					}
					Some(x)
				}
			).collect();
		criteria.last().map(|x| *x)
	}
}

impl ToString for TypeDef
{
	fn to_string(&self) -> String
	{
		self.predicates
		.iter()
		.map(|predicate| predicate.to_string())
		.collect::<Vec<String>>()
		.join(".")
	}
}

// impl std::fmt::Debug for TypeDef
// {
// 	fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result
// 	{
// 		write!(
// 			f,
// 			"{}",
// 			self.types
// 			.iter()
// 			.map(|predicate| format!("{predicate}"))
// 			.collect::<Vec<String>>()
// 			.join(".")
// 		)
// 	}
// }

impl PartialOrd for TypeDef
// Structural typing relations.
{
	fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering>
	// Subtype relation.
	// Returns:
	// Less if self is a strict subtype of other;
	// Greater if self is not a strict subtype of other;
	// Equal if self and other are equal.
	{
		if self.predicates == other.predicates {
			Some(std::cmp::Ordering::Equal)
		} else {
			let criteria: Vec<&Predicate> = other.predicates
				.iter()
				.filter_map(
					|x| {
						for y in &self.predicates {
							if *x == *y {
								return None
							}
						}
						Some(x)
					}
				).collect();
			if criteria.is_empty() {
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
