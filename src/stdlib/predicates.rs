use malachite::Natural;
use malachite::num::basic::traits::One;

use crate::sophia::arche::Value;

use crate::datatypes::predicates::Predicate;

impl Predicate
// Standard library predicates.
{
	pub fn std_any() -> Predicate
	{
		Predicate::new_std(
			"any",
			|_| true
		)
	}
	pub fn std_none() -> Predicate
	{
		Predicate::new_std(
			"none",
			|x| match x {
				Value::None => true,
				_ => false
			}
		)
	}
	pub fn std_some() -> Predicate
	{
		Predicate::new_std(
			"some",
			|x| match x {
				Value::None => false,
				_ => true
			}
		)
	}
	pub fn std_boolean() -> Predicate
	{
		Predicate::new_std(
			"boolean",
			|x| match x {
				Value::Boolean(_) => true,
				_ => false
			}
		)
	}
	pub fn std_number() -> Predicate
	{
		Predicate::new_std(
			"number",
			|x| match x {
				Value::Number(_) => true,
				_ => false
			}
		)
	}
	pub fn std_integer() -> Predicate
	{
		Predicate::new_std(
			"integer",
			|x| match x {
				Value::Number(x) if x.denominator_ref() == &Natural::ONE => true,
				_ => false
			}
		)
	}
	pub fn std_sequence() -> Predicate
	{
		Predicate::new_std(
			"sequence",
			|x| match x {
				| Value::String(_)
				| Value::Range(_)
				| Value::List(_)
				| Value::Record(_) => true,
				_ => false
			}
		)
	}
	pub fn std_string() -> Predicate
	{
		Predicate::new_std(
			"string",
			|x| match x {
				Value::String(_) => true,
				_ => false
			}
		)
	}
	pub fn std_range() -> Predicate
	{
		Predicate::new_std(
			"range",
			|x| match x {
				Value::Range(_) => true,
				_ => false
			}
		)
	}
	pub fn std_list() -> Predicate
	{
		Predicate::new_std(
			"list",
			|x| match x {
				Value::List(_) => true,
				_ => false
			}
		)
	}
	pub fn std_record() -> Predicate
	{
		Predicate::new_std(
			"record",
			|x| match x {
				Value::Record(_) => true,
				_ => false
			}
		)
	}
	pub fn std_function() -> Predicate
	{
		Predicate::new_std(
			"function",
			|x| match x {
				Value::Function(_) => true,
				_ => false
			}
		)
	}
	pub fn std_type() -> Predicate
	{
		Predicate::new_std(
			"type",
			|x| match x {
				Value::Type(_) => true,
				_ => false
			}
		)
	}
}
