use crate::error;
use crate::internal::instructions::Instruction;
use crate::internal::nodes::Node;
use crate::internal::patterns;
use crate::stdlib::std::{new_namespace, Namespace};

use super::hemera::Partial;

pub fn parse(source: &str) -> Partial<(Vec<Instruction>, Namespace)>
{
	// Normalise source file.
	let source: String = patterns::normalise(source);
	// Check validity of source file.
	if patterns::is_empty(&source) {
		return Ok((Instruction::default(), new_namespace()));
	};
	if patterns::is_unquoted(&source) {
		return error!(SNTX, "Unmatched quotes");
	};
	if patterns::is_unmatched(&source) {
		return error!(SNTX, "Unmatched parentheses");
	};
	// Generate AST from source.
	let tree: Node = Node::module(&source)?;
	// Generate instructions and namespace from AST.
	Ok(tree.generate())
}

// pub fn analyse(&self) -> Vec<Instruction>
// // Optimise parsed instructions.
// {
// 	let mut instructions: VecDeque<Instruction> = self
// 		.instructions
// 		.clone()
// 		.into();
// 	let mut acc: Vec<Instruction> = vec![];
// 	loop {
// 		match instructions.pop_front() {
// 			Some(ins) => {
// 				match &ins {
// 					Instruction::BIND => {
// 						Instruction::resolve_bind(&mut instructions, &mut acc)
// 					},
// 					_ => {
// 						acc.push(ins)
// 					}
// 				}
// 			},
// 			None => break
// 		};
// 	};
// 	acc
// }
