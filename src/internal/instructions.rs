use std::collections::{BTreeMap, VecDeque};

use crate::internal::nodes::Node;
use crate::internal::tokens::Token;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Instruction
{
	Command{
		name: String,
		address: String,
		args: Vec<String>,
		arity: usize,
	},
	Internal{
		name: String,
		address: String,
		args: Vec<String>, 		// Readable addresses.
		labels: Vec<String>, 	// Non-readable names.
		arity: usize, 			// Length of args.
		count: usize, 			// Length of labels.
	},
	Label(String)
}

impl ToString for Instruction
{
    fn to_string(&self) -> String
    {
		match self {
			Instruction::Command{name, address, args, arity} => {
				let mut buf: String = name.into();
				buf.push_str(" "); buf.push_str(address);
				match arity {
					0 => {},
					_ => {buf.push_str(" "); buf.push_str(&args.join(" "))},
				};
				// buf.push_str(";");
				// match label {
				// 	0 => {},
				// 	_ => {buf.push_str(" "); buf.push_str(&labels.join(" "))},
				// };
				buf
			},
			Instruction::Internal{name, address, args, labels, arity, count} => {
				let mut buf: String = name.into();
				buf.push_str(" "); buf.push_str(address);
				match arity {
					0 => {},
					_ => {buf.push_str(" "); buf.push_str(&args.join(" "))},
				};
				buf.push_str(";");
				match count {
					0 => {},
					_ => {buf.push_str(" "); buf.push_str(&labels.join(" "))},
				};
				buf
			},
			Instruction::Label(name) => {
				let mut buf: String = name.into();
				buf.push_str(";");
				// match label {
				// 	0 => {},
				// 	_ => {buf.push_str(" "); buf.push_str(&labels.join(" "))},
				// };
				return buf;
			}
		}
    }
}

impl Instruction
// Instruction constructors.
{
	pub fn command(name: &str, address: &str, args: Vec<String>) -> Instruction
	// Commands retrieve their instruction from the namespace.
	// Their names are plain by convention.
	{
		Instruction::Command{
			name: name.into(),
			address: address.into(),
			args: args.clone(),
			arity: args.len()
		}
	}
	pub fn internal(name: &str, address: &str, args: Vec<String>, labels: Vec<String>) -> Instruction
	// Internals execute directly from the task.
	// Their names are prefixed with '.' by convention.
	{
		Instruction::Internal{
			name: name.into(),
			address: address.into(),
			args: args.clone(),
			labels: labels.clone(),
			arity: args.len(),
			count: labels.len()
		}
	}
	pub fn label(name: &str) -> Instruction
	// Labels aren't executed.
	// Their names are capitalised by convention.
	{
		Instruction::Label(name.into())
	}
}

impl Instruction
// Execute protocol.
{
	pub fn execute(node: &Node, index: usize) -> Vec<Instruction>
	// Generates intermediate instructions.
    {
		match index {
			0 => match &node.token {
				Token::Type{
					name,
					supertype,
					prototype
				} 						=> Instruction::type_execute(node, &name, &supertype, prototype),
				Token::Function{
					name,
					signature
				} 						=> Instruction::function_execute(&name, &signature),
				Token::Module			|
				Token::If 				|
				Token::While 			|
				Token::For(_) 			|
				Token::Else 			=> Instruction::block_execute(node),
				_ 						=> vec![]
			},
			1 => match &node.token {
				Token::If 				|
				Token::While 			|
				Token::LeftConditional 	=> Instruction::branch_execute(node),
				Token::For(index) 		=> Instruction::for_execute(node, &index),
				Token::RightConditional => Instruction::right_con_execute(node),
				_ 						=> vec![]
			},
			_ => vec![]
		}
    }
	pub fn block_execute(node: &Node) -> Vec<Instruction>
	{
		vec![Instruction::label(if node.branch {"ELSE"} else {"START"})]
	}
	pub fn type_execute(node: &Node, name: &str, supertype: &str, prototype: &bool) -> Vec<Instruction>
	{
		if *prototype {
			vec![
				Instruction::internal(
					".check",
					&node.register,
					vec![
						node.nodes[0].register.clone(),
						supertype.into()
					],
					vec![]
				),
				Instruction::internal(
					".type",
					name,
					vec![
						supertype.into(),
						node.register.clone()
					],
					vec![]
				),
				Instruction::label("START")
			]
		} else {
			vec![
				Instruction::internal(
					".type",
					name,
					vec![
						supertype.into()
					],
					vec![]
				),
				Instruction::label("START")
			]
		}
	}
	pub fn function_execute(name: &str, signature: &BTreeMap<String, String>) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".function",
				name,
				signature
				.values()
				.cloned()
				.collect(),
				signature
				.keys()
				.cloned()
				.collect()
			),
			Instruction::label("START")
		]
	}
	pub fn branch_execute(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::command(
				"if",
				&node.register,
				vec![node.nodes[0].register.clone()]
			)
		]
	}
	pub fn for_execute(node: &Node, index: &str) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".iterator",
				&node.register,
				vec![node.nodes[0].register.clone()],
				vec![]
			),
			Instruction::label(if node.branch {"ELSE"} else {"START"}),
			Instruction::internal(
				".next",
				index,
				vec![node.register.clone()],
				vec![]
			)
		]
	}
	pub fn right_con_execute(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".bind",
				"0",
				vec![node.nodes[0].register.clone()],
				vec![node.register.clone()]
			),
			Instruction::command(
				"if",
				&node.register,
				vec![]
			),
			Instruction::label("END"),
			Instruction::label("ELSE")
		]
	}
}

impl Instruction {
// End protocol.
    pub fn end(node: &Node) -> Vec<Instruction>
	// Generates final instructions.
    {
        match &node.token {
			Token::Type{..}				=> Instruction::type_end(),
			Token::Module				|
			Token::Function{..} 		=> Instruction::method_end(node),
			Token::Assign(binds) 		=> Instruction::assign_end(node, &binds),
			Token::If 					=> Instruction::if_end(node),
			Token::While 				|
			Token::For{..} 				=> Instruction::loop_end(),
			Token::Return 				=> Instruction::return_end(node),
			Token::Link(links) 			=> Instruction::link_end(&links),
			Token::Use{names, source} 	=> Instruction::use_end(&names, &source),
			Token::Else 				=> Instruction::else_end(),
			Token::Continue 			=> Instruction::continue_end(),
			Token::Break				=> Instruction::break_end(),
			Token::Receive(name) 		=> Instruction::receive_end(name),
			Token::Sequence(_) 			=> Instruction::sequence_end(node),
			Token::Meta(_) 				=> Instruction::meta_end(node),
			Token::Bind 				=> Instruction::bind_end(node),
			Token::RightConditional		=> Instruction::right_con_end(node),
			Token::Pair					=> Instruction::pair_end(node),
			Token::Call					=> Instruction::call_end(node),
			Token::Index				=> Instruction::index_end(node),
			Token::Prefix(symbol) 		|
			Token::Infix(symbol) 		|
			Token::InfixR(symbol)		=> Instruction::operator_end(node, symbol),
            _ 							=> vec![]
        }
    }
	fn type_end() -> Vec<Instruction>
	{
		vec![
			Instruction::command(
				"constraint",
				"0",
				vec![]
			),
			Instruction::label("END")
		]
	}
	fn method_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::command(
				"return",
				"0",
				vec![
					node
					.nodes
					.last()
					.unwrap()
					.register
					.clone()
				]
			),
			Instruction::label("END")
		]
	}
	fn assign_end(node: &Node, binds: &BTreeMap<String, String>) -> Vec<Instruction>
	{
		let mut instructions = vec![Instruction::label("BIND")];
		instructions.extend(
			binds
			.values()
			.enumerate()
			.map(
				|(i, typename)| {
					Instruction::internal(
						".check",
						&(str::parse::<usize>(&node.register).unwrap() + i).to_string(),
						vec![
							node.nodes[i].register.clone(),
							typename.clone()
						],
						vec![]
					)
				}
			)
		);
		instructions.push(
			Instruction::internal(
				".bind",
				"0",
				vec![],
				binds
				.keys()
				.cloned()
				.collect()
			)
		);
		instructions
	}
	fn if_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::command(
				"if",
				&node.register,
				vec![]
			),
			Instruction::label("END")
		]
	}
	fn loop_end() -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".loop",
				"0",
				vec![],
				vec![]
			),
			Instruction::label("END")
		]
	}
	fn return_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			// Instruction::internal(
			// 	".check",
			// 	&node.register,
			// 	vec![
			// 		if node.nodes.is_empty() {node.register.clone()} else {node.nodes[0].register.clone()},
			// 		"".into() // Incorrect.
			// 	],
			// 	vec![]
			// ),
			Instruction::command(
				"return",
				"0",
				if node.nodes.is_empty() {vec![]} else {vec![node.register.clone()]},
			),
		]
	}
	fn link_end(links: &Vec<String>) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".link",
				"0", 
				vec![],
				links.clone()
			)
		]
	}
	fn use_end(names: &Vec<String>, source: &Option<String>) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".use",
				match source {
					Some(filename) => filename,
					None => "0"
				},
				vec![],
				names.clone()
			),
		]
	}
	fn else_end() -> Vec<Instruction>
	{
		vec![Instruction::label("END")]
	}
	fn continue_end() -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".continue",
				"0",
				vec![],
				vec![]
			)
		]
	}
	fn break_end() -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".break",
				"0",
				vec![],
				vec![]
			)
		]
	}
	fn receive_end(name: &str) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".receive",
				name,
				vec![],
				vec![]
			)
		]
	}
	fn sequence_end(node: &Node) -> Vec<Instruction>
	{
		if node.nodes.is_empty() {
			vec![]
		} else {
			match node.nodes[0].token {
				Token::Pair if node.nodes[0].nodes.len() == 3 => vec![
					Instruction::internal(
						".range",
						&node.register,
						node.nodes[0].nodes
						.iter()
						.map(|x| x.register.clone())
						.collect(),
						vec![]
					)
				],
				Token::Pair => vec![
					Instruction::internal(
						".record",
						&node.register,
						node.nodes
						.iter()
						.map(|x| x.nodes[1].register.clone())
						.collect(),
						node.nodes
						.iter()
						.map(|x| x.nodes[0].register.clone())
						.collect()
					)
				],
				_ => vec![
					Instruction::internal(
						".list",
						&node.register,
						node.nodes
						.iter()
						.map(|x| x.register.clone())
						.collect(),
						vec![]
					)
				] 
			}
		}
	}
	fn meta_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				"meta",
				&node.register, 
				vec![
					node.nodes[0].register.clone()
				],
				vec![]
			)
		]
	}
	fn bind_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".future",
				&node.register,
				node
				.nodes
				.iter()
				.map(|x| x.register.clone())
				.collect(),
				vec![]
			)
		]
	}
	fn right_con_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::internal(
				".bind",
				"0",
				vec![
					node.nodes[1].register.clone()
				],
				vec![
					node.register.clone()
				]
			)
		]
	}
	fn pair_end(node: &Node) -> Vec<Instruction>
	{
		if node.nodes.len() == 3 {
			vec![
				Instruction::internal(
					".slice",
					&node.register,
					node.nodes
					.iter()
					.map(|x| x.register.clone())
					.collect(),
					vec![]
				)
			]
		} else {
			vec![]
		}
	}
	fn call_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::command(
				&node.nodes[0].register,
				&node.register,
				node
				.nodes[1..]
				.iter()
				.map(|x| x.register.clone())
				.collect()
			)
		]
	}
	fn index_end(node: &Node) -> Vec<Instruction>
	{
		let mut instructions: Vec<Instruction> = vec![
			Instruction::command(
				"[",
				&node.register,
				vec![
					node.nodes[0].register.clone(),
					node.nodes[1].register.clone()
				]
			)
		];
		if node.nodes.len() > 2 {
			instructions.extend(
				node.nodes[2..]
				.iter()
				.map(
					|x| Instruction::command(
						"[",
						&node.register,
						vec![
							node.register.clone(),
							x.register.clone()
						]
					)
				)
			);
		};
		instructions
	}
	fn operator_end(node: &Node, symbol: &str) -> Vec<Instruction>
	{
		vec![
			Instruction::command(
				symbol,
				&node.register,
				node
				.nodes
				.iter()
				.map(|x| x.register.clone())
				.collect()
			)
		]
	}
}

impl Instruction
// Instruction generation for optimisations.
{
	pub fn bind(instructions: &mut VecDeque<Instruction>, acc: &mut Vec<Instruction>)
	// Evaluates type checking for name binding, removing instructions if the type check is known to succeed.
	// Currently does not bother to remove unnecessary type checks.
	{
		let mut registers: Vec<String> = vec![];
		loop {
			match instructions
			.pop_front()
			.unwrap() {
				Instruction::Internal{name, address, labels, ..} if name == ".bind" => {
					acc.push(
						Instruction::internal(
							".bind",
							&address,
							registers,
							labels
						)
					);
					break
				},
				Instruction::Internal{name, address, args, labels, ..} if name == ".check" => {
					if args[1] == "?" {
						registers.push(args[0].clone())
					} else {
						registers.push(address.clone());
						acc.push(
							Instruction::internal(
								".check",
								&address,
								args,
								labels
							)
						)
					}
				}
				_ => {}
			}
		}
	}
}