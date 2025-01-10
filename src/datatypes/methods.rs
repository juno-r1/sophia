use std::collections::BTreeMap;

use crate::error;
use crate::internal::instructions::Instruction;
use crate::sophia::arche::{Function, Namespace, Type, Value};
use crate::sophia::runtime::Task;

use super::types::TypeDef;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Routine {
	Std(Function),
	User(Vec<Instruction>)
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Method {
	pub routine: Routine,
	pub name: String,
	pub params: Vec<String>,
	pub last: TypeDef,
	pub signature: Vec<TypeDef>,
	pub arity: usize,
	pub closure: Namespace,
}

impl Method
{
	pub fn new_method_std(routine: Function, params: Vec<String>, types: Vec<TypeDef>) -> Method
	{
		Method{
			routine: Routine::Std(routine),
			name: params[0].clone(),
			params: params[1..].to_vec(),
			last: types[0].clone(),
			signature: types[1..].to_vec(),
			arity: params.len() - 1,
			closure: BTreeMap::new()
		}
	}
	pub fn new_method_user(instructions: Vec<Instruction>, params: Vec<String>, types: Vec<TypeDef>) -> Method
	{
		Method{
			routine: Routine::User(instructions),
			name: params[0].clone(),
			params: params[1..].to_vec(),
			last: types[0].clone(),
			signature: types[1..].to_vec(),
			arity: params.len() - 1,
			closure: BTreeMap::new()
		}
	}
	pub fn call(&self, task: &mut Task, args: Vec<Value>) -> Result<Value, String>
	{
		match self.routine {
			Routine::Std(function) => function(task, args),
			Routine::User(_) => error!(IMPL)
		}
	}
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Predicate{
	// Non-capturing built-in predicates.
	Base{
		routine: Type,
		name: String,
	},
	// Capturing built-in predicates.
	Std{
		routine: Type,
		name: String,
		signature: Vec<TypeDef>,
		arity: usize,
		closure: Namespace,
	},
	// User-defined predicates.
	User{
		instructions: Vec<Instruction>,
		name: String,
		params: Vec<String>,
		last: TypeDef,
		signature: Vec<TypeDef>,
		arity: usize,
		closure: Namespace,
	},
}

impl Predicate
{
	pub fn new_predicate_base(name: &str, routine: Type) -> Predicate
	{
		Predicate::Base{
			routine,
			name: name.into()
		}
	}
	pub fn new_any() -> Predicate
	{
		Predicate::Base{
			routine: Task::type_any,
			name: format!("any")
		}
	}
	pub fn call(&self, value: &Value) -> bool
	{
		match self {
			Predicate::Base{routine, ..} => routine(value.clone()),
			Predicate::Std{..} => false,
			Predicate::User{..} => false,
		}
	}
}