use std::collections::BTreeMap;

use crate::datatypes::Predicate;
use crate::sophia::Value;
use crate::stdlib::Namespace;

impl Predicate
// Standard library predicates.
{
	pub fn std_any() -> Predicate
	{
		Predicate::new_std(Predicate::impl_any)
	}
	pub fn std_boolean() -> Predicate
	{
		Predicate::new_std(Predicate::impl_boolean)
	}
	pub fn std_number() -> Predicate
	{
		Predicate::new_std(Predicate::impl_number)
	}
	pub fn std_integer() -> Predicate
	{
		Predicate::new_std(Predicate::impl_integer)
	}
	pub fn std_string() -> Predicate
	{
		Predicate::new_std(Predicate::impl_string)
	}
	pub fn std_range() -> Predicate
	{
		Predicate::new_std(Predicate::impl_range)
	}
	pub fn std_list(x0: Value) -> Predicate
	{
		Predicate::new_capturing(
			Predicate::impl_list,
			BTreeMap::from([
				(format!("x0"), x0)
			])
		)
	}
	pub fn std_record(x0: Value, x1: Value) -> Predicate
	{
		Predicate::new_capturing(
			Predicate::impl_record,
			BTreeMap::from([
				(format!("x0"), x0),
				(format!("x1"), x1)
			])
		)
	}
	pub fn std_function() -> Predicate
	{
		Predicate::new_std(Predicate::impl_function)
	}
	pub fn std_type() -> Predicate
	{
		Predicate::new_std(Predicate::impl_type)
	}
	pub fn std_sum(x0: Namespace) -> Predicate
	{
		Predicate::new_capturing(
			Predicate::impl_sum,
			x0
		)
	}
	pub fn std_struct(x0: Value) -> Predicate
	{
		Predicate::new_capturing(
			Predicate::impl_sum,
			BTreeMap::from([
				(format!("x0"), x0)
			])
		)
	}
}
