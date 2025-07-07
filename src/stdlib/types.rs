use crate::datatypes::{Predicate, TypeDef};
use crate::std_mod;

use malachite::Rational;
use malachite::num::basic::traits::Zero;

use crate::sophia::Value;

impl TypeDef
// Standard library types.
{
	pub fn std_any() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::new(),
			Predicate::std_any(),
			None
		)
	}
	pub fn std_none() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_any(),
			Predicate::std_none(),
			None
		)
	}
	pub fn std_some() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_any(),
			Predicate::std_some(),
			None
		)
	}
	pub fn std_boolean() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_boolean(),
			Some(Value::new_boolean(true))
		)
	}
	pub fn std_number() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_number(),
			Some(Value::new_number(Rational::ZERO))
		)
	}
	pub fn std_integer() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_number(),
			Predicate::std_integer(),
			None
		)
	}
	pub fn std_string() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_string(),
			Some(Value::new_string(String::new()))
		)
	}
	pub fn std_range() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_range(),
			None
		)
	}
	pub fn std_function() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_function(),
			None
		)
	}
	pub fn std_type() -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_type(),
			Some(Value::new_type(TypeDef::std_any()))
		)
	}
}

impl TypeDef
// Internal type constructors.
{
	pub fn std_list(x0: TypeDef) -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_list(Value::new_type(x0)),
			None
		)
	}
	pub fn std_record(x0: TypeDef, x1: TypeDef) -> TypeDef
	{
		TypeDef::from_super(
			&TypeDef::std_some(),
			Predicate::std_record(Value::new_type(x0), Value::new_type(x1)),
			None
		)
	}
}

std_mod!
{
	list: {
		use crate::datatypes::TypeDef;
	};
	std_fn!
	{
		Type list_t(Type x0)
		{
			TypeDef::std_list(x0)
		}
	}
}

std_mod!
{
	record: {
		use crate::datatypes::TypeDef;
	};
	std_fn!
	{
		Type record_tt(Type x0, Type x1)
		{
			TypeDef::std_record(x0, x1)
		}
	}
}
