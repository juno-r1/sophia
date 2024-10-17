use std::collections::{HashMap, VecDeque};

use crate::internal::instructions::Instruction;
use crate::internal::nodes::Node;
use crate::internal::patterns;
use crate::internal::tokens::Token;

use super::arche::{Namespace, Value};

#[derive(Debug)]
pub struct Parser {
    pub instructions: Vec<Instruction>,
	pub namespace: Namespace,
	constant: isize, // Constant address.
}

impl Parser
{
    pub fn new() -> Parser
    {
        Parser{
			instructions: vec![],
			namespace: HashMap::from(
				[
					(format!("0"), Value::new_none()),
					(format!("-1"), Value::new_none())
				]
			),
			constant: -1
		}
    }
    pub fn parse(&mut self, source: &str)
    {
        let source: String = patterns::normalise(source);
        if patterns::is_empty(&source) {
            panic!("Empty source")
        };
        if patterns::is_unquoted(&source) {
            panic!("Unmatched quotes")
        };
        if patterns::is_unmatched(&source) {
            panic!("Unmatched parentheses")
        };
        let lines: Vec<String> = patterns::split(&source);
        let tree: Node = Node::tree(lines); // Here's tree!
		self.generate(tree);
	}
	fn generate(&mut self, mut tree: Node)
	// Generates a list of instructions from an AST.
	// Rust is a bit annoying about mutable references, so reaching a node is O(n).
	{
		let mut path: Vec<usize> = vec![];
		let mut index: usize = 0;
		loop {
			let mut head = &mut tree; // Start at top of tree.
			for i in &path { // Navigate to head node.
				head = head
					.nodes
					.get_mut(*i)
					.unwrap();
			}
			self.instructions.extend( // Get initial instructions.
				Instruction::execute(head, index)
			); // Never called for leaf nodes, and doesn't need to be.
			match head.nodes.get_mut(index) { // Get current node.
				Some(node) => { // Going down?
					path.push(index); // Push index to path.
					index = 0; // Reset index.
					self.register(node, &path); // Set node register.
				},
				None => { // Going up?
					self.instructions.extend( // Get final instructions.
						Instruction::end(head)
					);
					index = match path.pop() { // Increment path or exit.
						Some(i) => i + 1,
						None => break
					}
				}
			}
		}
	}
	fn register(&mut self, node: &mut Node, path: &Vec<usize>)
	// Sets the node's register.
	{
		node.register = match &node.token {
			Token::Env(name) 		|
			Token::Name(name) 		|
			Token::Receive(name) 	=> name.clone(),
			Token::Null => format!("-1"),
			Token::Sequence(_) if node.nodes.is_empty() => {
				self.constant -= 1;
				let index = self.constant.to_string();
				self.namespace.insert(
					index.clone(),
					Value::new_list(vec![])
				);
				index
			},
			Token::Number(x) => {
				self.constant -= 1;
				let index = self.constant.to_string();
				self.namespace.insert(
					index.clone(),
					Value::new_number(x.clone())
				);
				index
			},
			Token::String(x) => {
				self.constant -= 1;
				let index = self.constant.to_string();
				self.namespace.insert(
					index.clone(),
					Value::new_string(x.clone())
				);
				index
			},
			Token::Boolean(x) => {
				self.constant -= 1;
				let index = self.constant.to_string();
				self.namespace.insert(
					index.clone(),
					Value::new_boolean(x.clone())
				);
				index
			},
			_ => (path
				.iter()
				.sum::<usize>() + 1)
				.to_string()
		}
	}
	pub fn analyse(&self) -> Vec<Instruction>
	// Optimise parsed instructions.
	{
		let mut instructions: VecDeque<Instruction> = self
			.instructions
			.clone()
			.into();
		let mut acc: Vec<Instruction> = vec![];
		loop {
			match instructions.pop_front() {
				Some(ins) => {
					match &ins {
						Instruction::Label(name) if name == "BIND" => {
							Instruction::bind(&mut instructions, &mut acc)
						},
						_ => {
							acc.push(ins)
						}
					}
				},
				None => break
			};
		};
		acc
	}
}