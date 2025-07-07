use std::collections::BTreeMap;

use crate::datatypes::Predicate;
use crate::sophia::Value;

impl Predicate
// Standard library predicates.
{
	pub fn std_any() -> Predicate
	{
		Predicate::new_std(
			"Any",
			Predicate::impl_any
		)
	}
	pub fn std_none() -> Predicate
	{
		Predicate::new_std(
			"None",
			Predicate::impl_none
		)
	}
	pub fn std_some() -> Predicate
	{
		Predicate::new_std(
			"Some",
			Predicate::impl_some
		)
	}
	pub fn std_boolean() -> Predicate
	{
		Predicate::new_std(
			"Boolean",
			Predicate::impl_boolean
		)
	}
	pub fn std_number() -> Predicate
	{
		Predicate::new_std(
			"Number",
			Predicate::impl_number
		)
	}
	pub fn std_integer() -> Predicate
	{
		Predicate::new_std(
			"Integer",
			Predicate::impl_integer
		)
	}
	pub fn std_string() -> Predicate
	{
		Predicate::new_std(
			"String",
			Predicate::impl_string
		)
	}
	pub fn std_range() -> Predicate
	{
		Predicate::new_std(
			"Range",
			Predicate::impl_range
		)
	}
	pub fn std_list(x0: Value) -> Predicate
	{
		Predicate::new_capturing(
			"List",
			Predicate::impl_list,
			BTreeMap::from([
				(format!("x0"), x0)
			])
		)
	}
	pub fn std_record(x0: Value, x1: Value) -> Predicate
	{
		Predicate::new_capturing(
			"Record",
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
			"Function",
			Predicate::impl_function
		)
	}
	pub fn std_type() -> Predicate
	{
		Predicate::new_std(
			"Type",
			Predicate::impl_type
		)
	}
}
