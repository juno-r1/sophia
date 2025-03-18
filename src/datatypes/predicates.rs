use std::collections::BTreeMap;

use crate::internal::instructions::Instruction;
use crate::sophia::arche::Value;
use crate::stdlib::std::Namespace;

type BuiltIn = fn(&Value) -> bool;
type BuiltInCapturing = fn(&Value, Vec<&Value>) -> bool;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum Routine {
	Std(BuiltIn),
	Capturing(BuiltInCapturing),
	User(Vec<Instruction>)
}

#[derive(Debug, Clone, Eq, Hash)]
pub struct Predicate {
	routine: Routine,
	closure: Namespace,
	name: String,
}

impl Predicate
{
	pub fn new_std(name: &str, routine: BuiltIn) -> Predicate
	{
		Predicate{
			routine: Routine::Std(routine),
			closure: BTreeMap::new(),
			name: name.into()
		}
	}
	pub fn new_capturing(name: &str, routine: BuiltInCapturing, closure: Namespace) -> Predicate
	{
		Predicate{
			routine: Routine::Capturing(routine),
			closure,
			name: name.into()
		}
	}
	pub fn call(&self, value: &Value) -> bool
	{
		match &self.routine {
			Routine::Std(routine) => routine(value),
			Routine::Capturing(routine) => routine(value, self.closure.values().collect()),
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

impl ToString for Predicate
{
	fn to_string(&self) -> String
	{
		self.name.clone()
	}
}