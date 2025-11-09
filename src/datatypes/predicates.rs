use std::collections::BTreeMap;

use crate::parser::Instruction;
use crate::sophia::Value;
use crate::stdlib::Namespace;

type BuiltIn = fn(&Predicate, &Value) -> bool;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum Routine {
	Std(BuiltIn),
	User(Vec<Instruction>)
}

#[derive(Debug, Clone, Eq, Hash)]
pub struct Predicate {
	routine: Routine,
	closure: Namespace,
}

impl Predicate
{
	pub fn new_std(routine: BuiltIn) -> Predicate
	{
		Predicate{
			routine: Routine::Std(routine),
			closure: BTreeMap::new()
		}
	}
	pub fn new_capturing(routine: BuiltIn, closure: Namespace) -> Predicate
	{
		Predicate{
			routine: Routine::Std(routine),
			closure
		}
	}
	pub fn call(&self, value: &Value) -> bool
	{
		match &self.routine {
			Routine::Std(routine) => routine(self, value),
			Routine::User(_) => unimplemented!()
		}
	}
}

impl PartialEq for Predicate
// Structural typing requires that equality ignores naming.
{
	fn eq(&self, other: &Self) -> bool
	{
		self.routine == other.routine && self.closure == other.closure
	}
}

impl Predicate
// Built-in predicate implementations.
{
	pub fn impl_any(&self, _: &Value) -> bool
	{
		true
	}
	pub fn impl_boolean(&self, x: &Value) -> bool
	{
		match x {
			Value::Boolean(_) => true,
			_ => false
		}
	}
	pub fn impl_number(&self, x: &Value) -> bool
	{
		match x {
			Value::Number(_) => true,
			_ => false
		}
	}
	pub fn impl_integer(&self, x: &Value) -> bool
	{
		match x {
			Value::Number(x) if *x.denominator_ref() == 1 => true,
			_ => false
		}
	}
	pub fn impl_string(&self, x: &Value) -> bool
	{
		match x {
			Value::String(_) => true,
			_ => false
		}	
	}
	pub fn impl_range(&self, x: &Value) -> bool
	{
		match x {
			Value::Range(_) => true,
			_ => false
		}
	}
	pub fn impl_list(&self, x: &Value) -> bool
	{
		match x {
			Value::List(value) => {
				let Value::Type(x0) = self.closure.get("x0").unwrap() else {unreachable!()};
				value.iter().all(|x| x0.check(&x))
			},
			_ => false
		}
	}
	pub fn impl_record(&self, x: &Value) -> bool
	{
		match x {
			Value::Record(value) => {
				let Value::Type(x0) = self.closure.get("x0").unwrap() else {unreachable!()};
				let Value::Type(x1) = self.closure.get("x1").unwrap() else {unreachable!()};
				value.keys().iter().all(|x| x0.check(*x)) &&
				value.values().iter().all(|x| x1.check(*x))
			},
			_ => false
		}
	}
	pub fn impl_function(&self, x: &Value) -> bool
	{
		match x {
			Value::Function(_) => true,
			_ => false
		}
	}
	pub fn impl_type(&self, x: &Value) -> bool
	{
		match x {
			Value::Type(_) => true,
			_ => false
		}	
	}
	pub fn impl_sum(&self, x: &Value) -> bool
	// INCOMPLETE
	{
		match x {
			Value::Sum(x) if self.closure.contains_key(&x.tag) => true,
			_ => false
		}
	}
	pub fn impl_struct(&self, x: &Value) -> bool
	// INCOMPLETE
	{
		match x {
			Value::Struct(_) => true,
			_ => false
		}
	}
}
