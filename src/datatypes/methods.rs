use std::collections::{BTreeMap, HashMap};

use crate::internal::instructions::Instruction;
use crate::sophia::arche::{Function, Namespace};
use crate::sophia::runtime::Task;

use super::types::TypeDef;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Routine {
	Std(Function),
	User(Vec<Instruction>)
}

#[derive(Debug, Clone, PartialEq, Eq)]
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
	pub fn new_method_std(routine: Function, signature: BTreeMap<String, TypeDef>) -> Method
	{
		let names: Vec<String> = signature
			.keys()
			.cloned()
			.collect();
		let types: Vec<TypeDef> = signature
			.values()
			.cloned()
			.collect();
		Method{
			routine: Routine::Std(routine),
			name: names[0].clone(),
			params: names[1..].to_vec(),
			last: types[0].clone(),
			signature: types[1..].to_vec(),
			arity: names.len() - 1,
			closure: HashMap::new()
		}
	}
	pub fn new_method_user(instructions: Vec<Instruction>, signature: BTreeMap<String, TypeDef>) -> Method
	{
		let names: Vec<String> = signature
			.keys()
			.cloned()
			.collect();
		let types: Vec<TypeDef> = signature
			.values()
			.cloned()
			.collect();
		Method{
			routine: Routine::User(instructions),
			name: names[0].clone(),
			params: names[1..].to_vec(),
			last: types[0].clone(),
			signature: types[1..].to_vec(),
			arity: names.len() - 1,
			closure: HashMap::new()
		}
	}
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Predicate{
	// Non-capturing built-in predicates.
	Base{
		routine: Function,
		name: String,
	},
	// Capturing built-in predicates.
	Std{
		routine: Function,
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
	pub fn new_predicate_base(name: &str, routine: Function) -> Predicate
	{
		Predicate::Base{
			routine,
			name: name.to_string()
		}
	}
	pub fn new_any() -> Predicate
	{
		Predicate::Base{
			routine: Task::type_any,
			name: "any".to_string()
		}
	}
}