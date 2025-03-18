use std::collections::BTreeMap;

use crate::error;
use crate::internal::instructions::Instruction;
use crate::sophia::arche::Value;
use crate::sophia::hemera::Partial;
use crate::sophia::runtime::Task;
use crate::stdlib::std::Namespace;

use super::types::TypeDef;

type BuiltIn = fn(&mut Task, Vec<Value>) -> Partial<Value>;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
enum Routine {
	Std(BuiltIn),
	User(Vec<Instruction>)
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Method {
	routine: Routine,
	closure: Namespace,
	name: String,
	params: Vec<String>,
	pub last: TypeDef,
	pub signature: Vec<TypeDef>,
	pub partial: bool,
	pub arity: usize,
}

impl Method
{
	pub fn new_std(routine: BuiltIn, params: Vec<String>, types: Vec<TypeDef>, partial: bool) -> Method
	{
		Method{
			routine: Routine::Std(routine),
			closure: BTreeMap::new(),
			name: params[0].clone(),
			params: params[1..].to_vec(),
			last: types[0].clone(),
			signature: types[1..].to_vec(),
			partial,
			arity: params.len() - 1
		}
	}
	pub fn new_user(instructions: Vec<Instruction>, params: Vec<String>, types: Vec<TypeDef>, partial: bool) -> Method
	{
		Method{
			routine: Routine::User(instructions),
			closure: BTreeMap::new(),
			name: params[0].clone(),
			params: params[1..].to_vec(),
			last: types[0].clone(),
			signature: types[1..].to_vec(),
			partial,
			arity: params.len() - 1
		}
	}
	pub fn call(&self, task: &mut Task, args: Vec<Value>) -> Partial<Value>
	{
		match self.routine {
			Routine::Std(function) => function(task, args),
			Routine::User(_) => error!(IMPL)
		}
	}
}
