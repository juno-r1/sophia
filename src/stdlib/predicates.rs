use std::collections::BTreeMap;

use crate::datatypes::Predicate;
use crate::sophia::Value;

impl Predicate
// Standard library predicates.
{
	pub fn std_any() -> Predicate
	{
		Predicate::new_std(
			"any",
			Predicate::impl_any
		)
	}
	pub fn std_none() -> Predicate
	{
		Predicate::new_std(
			"none",
			Predicate::impl_none
		)
	}
	pub fn std_some() -> Predicate
	{
		Predicate::new_std(
			"some",
			Predicate::impl_some
		)
	}
	pub fn std_boolean() -> Predicate
	{
		Predicate::new_std(
			"boolean",
			Predicate::impl_boolean
		)
	}
	pub fn std_number() -> Predicate
	{
		Predicate::new_std(
			"number",
			Predicate::impl_number
		)
	}
	pub fn std_integer() -> Predicate
	{
		Predicate::new_std(
			"integer",
			Predicate::impl_integer
		)
	}
	pub fn std_string() -> Predicate
	{
		Predicate::new_std(
			"string",
			Predicate::impl_string
		)
	}
	pub fn std_range() -> Predicate
	{
		Predicate::new_std(
			"range",
			Predicate::impl_range
		)
	}
	pub fn std_list(x0: Value) -> Predicate
	{
		Predicate::new_capturing(
			"list",
			Predicate::impl_list,
			BTreeMap::from([
				(format!("x0"), x0)
			])
		)
	}
	pub fn std_record(x0: Value, x1: Value) -> Predicate
	{
		Predicate::new_capturing(
			"record",
			Predicate::impl_record,
			BTreeMap::from([
				(format!("x0"), x0),
				(format!("x1"), x1)
			])
		)
	}
	pub fn std_function() -> Predicate
	{
		Predicate::new_std(
			"function",
			Predicate::impl_function
		)
	}
	pub fn std_type() -> Predicate
	{
		Predicate::new_std(
			"type",
			Predicate::impl_type
		)
	}
}
