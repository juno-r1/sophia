use crate::error;
use crate::internal::instructions::Instruction;
use crate::internal::nodes::Node;
use crate::internal::patterns;

use super::arche::{new_namespace, Namespace};

pub fn parse(source: &str) -> Result<(Vec<Instruction>, Namespace), String>
{
	// Normalise source file and split into logical lines.
	let source: String = patterns::normalise(source);
	if patterns::is_empty(&source) {
		return Ok((Instruction::default(), new_namespace()));
	};
	if patterns::is_unquoted(&source) {
		return error!(UQTE);
	};
	if patterns::is_unmatched(&source) {
		return error!(UPRN);
	};
	let lines: Vec<String> = patterns::split(&source);
	// Generate AST from lines.
	let tree: Node = Node::tree(lines);
	// Generate instructions and namespace from AST.
	// Rust is a bit annoying about mutable references, so reaching a node is O(n).
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