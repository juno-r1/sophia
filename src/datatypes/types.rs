use crate::sophia::Value;

use super::predicates::Predicate;

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct TypeDef {
	predicates: Vec<Predicate>,
	prototype: Option<Value>,
}

impl TypeDef
{
	pub fn new() -> TypeDef
	{
		TypeDef{
			predicates: vec![],
			prototype: None
		}
	}
	pub fn from_predicates(predicates: Vec<Predicate>, prototype: Option<Value>) -> TypeDef
	{
		TypeDef{
			predicates,
			prototype
		}
	}
	pub fn from_super(supertype: &TypeDef, predicate: Predicate, prototype: Option<Value>) -> TypeDef
	{
		let mut predicates = supertype.predicates.clone();
		predicates.push(predicate);
		TypeDef{
			predicates,
			prototype: prototype.or(supertype.prototype.clone())
		}
	}
	pub fn infer(value: &Value) -> TypeDef
	{
		match value {
			Value::Number(x) if *x.denominator_ref() == 1 => TypeDef::std_integer(),
			Value::Number(_) => TypeDef::std_number(),
			Value::Boolean(_) => TypeDef::std_boolean(),
			Value::String(_) => TypeDef::std_string(),
			Value::Range(_) => TypeDef::std_range(),
			Value::List(x) => TypeDef::std_list(
				TypeDef::union_fold(
					x.iter().map(|x| TypeDef::infer(x)).collect()
				)
			),
			Value::Record(x) => TypeDef::std_record(
				TypeDef::union_fold(
					x.keys().iter().map(|x| TypeDef::infer(x)).collect()
				),
				TypeDef::union_fold(
					x.values().iter().map(|x| TypeDef::infer(x)).collect()
				),
			),
			Value::Function(_) => TypeDef::std_any(),
			Value::Type(_) => TypeDef::std_any(),
			_ => unreachable!()
		}
	}
	pub fn read(descriptor: &str) -> TypeDef
	// Creates a TypeDef from a type descriptor.
	{
		if descriptor.chars().last().unwrap() == '?' {
			return TypeDef::std_option(TypeDef::read(
				&descriptor[0..descriptor.len() - 1]
			));
		};
		match descriptor {
			// Infer type.
			"?" => TypeDef::new(),
			// Non-capturing types.
			"Any" => TypeDef::std_any(),
			"Boolean" => TypeDef::std_boolean(),
			"Number" => TypeDef::std_number(),
			"Integer" => TypeDef::std_integer(),
			"String" => TypeDef::std_string(),
			"Range" => TypeDef::std_range(),
			"Type" => TypeDef::std_type(),
			// Capturing types.
			"List" => TypeDef::std_list(TypeDef::std_any()),
			"Record" => TypeDef::std_record(TypeDef::std_any(), TypeDef::std_any()),
			"Function" => TypeDef::std_function(),
			// Unsupported types.
			_ => panic!("Type not supported: {descriptor}")
		}
	}
	pub fn check(&self, value: &Value) -> bool
	// Type check on the passed value.
	{
		self.predicates
		.iter()
		.all(|predicate| {predicate.call(value)})
	}
	pub fn has(&self, predicate: &Predicate) -> bool
	// Universal dispatch check exploiting properties of structural typing.
	{
		self.predicates
		.iter()
		.any(|x| x == predicate)
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
	pub fn union_fold(types: Vec<TypeDef>) -> TypeDef
	// Gets the common supertype of a list of types.
	// Only has a prototype if all types have the same prototype.
	{
		types.iter().fold(
			types.get(0).unwrap_or(&TypeDef::std_any()).clone(),
			|lhs, rhs| {
				TypeDef::from_predicates(
					lhs.predicates
					.iter()
					.filter_map(
						|x| {
							for y in &rhs.predicates {
								if *x == *y {
									return None
								}
							}
							Some(x.clone())
						}
					).collect(),
					if lhs.prototype == rhs.prototype {lhs.prototype.clone()} else {None}
				)
			}
		)
	}
}

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
