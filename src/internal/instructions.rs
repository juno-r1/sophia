use crate::internal::nodes::Node;
use crate::internal::tokens::Token;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Instruction
{
	// User functions and dispatched commands.
	// Commands retrieve their instruction from the namespace.
	// Their names are plain by convention.
	Command{
		name: String,					// Function name.
		address: String,				// Writeable address.
		args: Vec<String>,				// Readable addresses.
		arity: usize,					// Length of args.
	},
	// Internal functions.
	// Internals execute directly from the task.
	// Their names are prefixed with '.' by convention.
	Bind{
		args: Vec<String>,				// Readable addresses.
		params: Vec<String>,			// Binding names.
		types: Vec<String>,				// Binding signature.
	},
	Break,
	// Check{
	// 	address: String,				// Writeable address.
	// 	register: String,				// Readable address.
	// 	typename: Option<String>, 		// Checked type.
	// },
	Continue,
	// Function{
	// 	name: String,					// Function name.
	// 	signature: Signature,			// Parameter signature.
	// 	arity: usize,					// Number of arguments.
	// },
	Future{
		address: String,
		args: Vec<String>,
	},
	Iterator{
		address: String,
		register: String,
	},
	Link(Vec<String>),
	List{
		address: String,
		args: Vec<String>,
	},
	Loop,
	// Meta,
	Next{
		index: String,
		register: String,
	},
	Range{
		address: String,
		start: String,
		end: String,
		step: String,
	},
	Receive(String),
	Record{
		address: String,
		keys: Vec<String>,
		values: Vec<String>,
	},
	Return(String),
	Skip,
	Type{
		name: String,
		supertype: String,
		prototype: Option<String>,
	},
	// Use,
	Write{
		address: String, // Destination register.
		register: String, // Source register.
	},
	// Instruction labels.
	// Labels aren't executed.
	// Their names are capitalised by convention.
	START,
	ELSE,
	BIND,
	END,
}

// impl ToString for Instruction
// {
//     fn to_string(&self) -> String
//     {
// 		match self {
// 			Instruction::Command{name, address, args, arity} => {
// 				let body: String = format!("{name} {address}");
// 				let args: String = args.join(" ");
// 				match arity {
// 					0 => body,
// 					_ => format!("{body} {args}")
// 				}
// 			},
// 			Instruction::Bind{args, signature, ..} => {
// 				let args: String = args.join(" ");
// 				let signature: String = signature
// 					.iter()
// 					.fold(
// 						format!(""),
// 						|mut acc, (name, typename)| {
// 							acc.push_str(
// 								&format!("; {typename} {name}")
// 							);
// 							acc
// 						}
// 					);
// 				format!("bind {args}{signature}")
// 			}
// 			_ => format!("")
// 			// Instruction::Internal{name, address, args, labels, arity, count} => {
// 			// 	let mut buf: String = name.into();
// 			// 	buf.push_str(" "); buf.push_str(address);
// 			// 	match arity {
// 			// 		0 => {},
// 			// 		_ => {buf.push_str(" "); buf.push_str(&args.join(" "))},
// 			// 	};
// 			// 	buf.push_str(";");
// 			// 	match count {
// 			// 		0 => {},
// 			// 		_ => {buf.push_str(" "); buf.push_str(&labels.join(" "))},
// 			// 	};
// 			// 	buf
// 			// },
// 			// Instruction::Bind(signature) => {
// 			// 	let mut buf: String = format!(".bind:");
// 			// 	for (k, v) in signature {
// 			// 		buf.push_str(
// 			// 			format!(" {v} {k};")
// 			// 			.as_str()
// 			// 		);
// 			// 	}
// 			// 	buf
// 			// }
// 			// Instruction::Label(name) => {
// 			// 	let mut buf: String = name.into();
// 			// 	buf.push_str(";");
// 			// 	// match label {
// 			// 	// 	0 => {},
// 			// 	// 	_ => {buf.push_str(" "); buf.push_str(&labels.join(" "))},
// 			// 	// };
// 			// 	buf
// 			// }
// 		}
//     }
// }

impl Instruction
// Instruction constructors.
{
	pub fn new_command(name: &str, address: &str, args: Vec<String>) -> Instruction
	{
		let arity = args.len();
		Instruction::Command{
			name: name.into(),
			address: address.into(),
			args,
			arity
		}
	}
	pub fn new_bind(args: Vec<String>, params: Vec<String>, types: Vec<String>) -> Instruction
	{
		Instruction::Bind{
			args,
			params,
			types
		}
	}
	// pub fn new_check(address: &str, register: &str, typename: Option<String>) -> Instruction
	// {
	// 	Instruction::Check{
	// 		address: address.into(),
	// 		register: register.into(),
	// 		typename
	// 	}
	// }
	// pub fn new_function(name: &str, signature: Signature) -> Instruction
	// {
	// 	let arity = signature.len();
	// 	Instruction::Function{
	// 		name: name.into(),
	// 		signature,
	// 		arity,
	// 	}
	// }
	pub fn new_future(address: &str, args: Vec<String>) -> Instruction
	{
		Instruction::Future{
			address: address.into(),
			args
		}
	}
	pub fn new_iterator(address: &str, register: &str) -> Instruction
	{
		Instruction::Iterator{
			address: address.into(),
			register: register.into()
		}
	}
	pub fn new_list(address: &str, args: Vec<String>) -> Instruction
	{
		Instruction::List{
			address: address.into(),
			args
		}
	}
	pub fn new_next(index: &str, register: &str) -> Instruction
	{
		Instruction::Next{
			index: index.into(),
			register: register.into()
		}
	}
	pub fn new_range(address: &str, start: &str, end: &str, step: &str) -> Instruction
	{
		Instruction::Range{
			address: address.into(),
			start: start.into(),
			end: end.into(),
			step: step.into(),
		}
	}
	pub fn new_record(address: &str, keys: Vec<String>, values: Vec<String>) -> Instruction
	{
		Instruction::Record{
			address: address.into(),
			keys,
			values
		}
	}
	pub fn new_type(name: &str, supertype: &str) -> Instruction
	{
		Instruction::Type{
			name: name.into(),
			supertype: supertype.into(),
			prototype: None,
		}
	}
	pub fn new_type_prototype(name: &str, supertype: &str, prototype: &str) -> Instruction
	{
		Instruction::Type{
			name: name.into(),
			supertype: supertype.into(),
			prototype: Some(prototype.into()),
		}
	}
	pub fn new_write(address: &str, register: &str) -> Instruction
	{
		Instruction::Write{
			address: address.into(),
			register: register.into()
		}
	}
	pub fn default() -> Vec<Instruction>
	{
		vec![
			Instruction::START,
			Instruction::Return(format!("-1")),
			Instruction::END
		]
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
				} => Instruction::type_execute(node, &name, &supertype, prototype),
				// Token::Function{
				// 	name,
				// 	signature
				// } => Instruction::function_execute(&name, &signature),
				| Token::Module
				| Token::If
				| Token::While 
				| Token::For(_)
				| Token::Else => Instruction::block_execute(node),
				_ => vec![]
			},
			1 => match &node.token {
				| Token::If
				| Token::While
				| Token::LeftConditional => Instruction::branch_execute(node),
				Token::For(index) => Instruction::for_execute(node, &index),
				Token::RightConditional => Instruction::right_con_execute(node),
				_ => vec![]
			},
			_ => vec![]
		}
    }
	pub fn block_execute(node: &Node) -> Vec<Instruction>
	{
		vec![if node.branch {Instruction::ELSE} else {Instruction::START}]
	}
	pub fn type_execute(node: &Node, name: &str, supertype: &str, prototype: &bool) -> Vec<Instruction>
	{
		if *prototype {
			vec![
				// Instruction::new_check(
				// 	&node.register,
				// 	&node.nodes[0].register,
				// 	Some(supertype.into())
				// ),
				Instruction::new_type_prototype(
					name,
					&supertype,
					&node.register
				),
				Instruction::START
			]
		} else {
			vec![
				Instruction::new_type(
					name,
					&supertype
				),
				Instruction::START
			]
		}
	}
	// pub fn function_execute(name: &str, signature: &IndexMap<String, String>) -> Vec<Instruction>
	// {
	// 	vec![
	// 		Instruction::new_function(
	// 			name,
	// 			signature.clone()
	// 		),
	// 		Instruction::START
	// 	]
	// }
	pub fn branch_execute(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::new_command(
				"if",
				&node.register,
				vec![node.nodes[0].register.clone()]
			)
		]
	}
	pub fn for_execute(node: &Node, index: &str) -> Vec<Instruction>
	{
		vec![
			Instruction::new_iterator(
				&node.register,
				&node.nodes[0].register
			),
			if node.branch {Instruction::ELSE} else {Instruction::START},
			Instruction::new_next(
				index,
				&node.register
			)
		]
	}
	pub fn right_con_execute(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::new_write(
				&node.register,
				&node.nodes[0].register
			),
			Instruction::new_command(
				"if",
				&node.register,
				vec![]
			),
			Instruction::END,
			Instruction::ELSE
		]
	}
}

impl Instruction {
// End protocol.
    pub fn end(node: &Node) -> Vec<Instruction>
	// Generates final instructions.
    {
        match &node.token {
			Token::Type{..} => Instruction::type_end(),
			| Token::Module
			| Token::Function{..} => Instruction::method_end(node),
			Token::Assign{params, types} => Instruction::assign_end(node, params, types),
			Token::If => Instruction::if_end(node),
			| Token::While
			| Token::For{..} => Instruction::loop_end(),
			Token::Return => Instruction::return_end(node),
			Token::Link(links) => Instruction::link_end(&links),
			// Token::Use{names, source} 	=> Instruction::use_end(&names, &source),
			Token::Else => Instruction::else_end(),
			Token::Continue => Instruction::continue_end(),
			Token::Break => Instruction::break_end(),
			Token::Receive(name) => Instruction::receive_end(name),
			Token::Sequence(_) => Instruction::sequence_end(node),
			// Token::Meta(_) 				=> Instruction::meta_end(node),
			Token::Bind => Instruction::bind_end(node),
			Token::RightConditional => Instruction::right_con_end(node),
			Token::Call => Instruction::call_end(node),
			Token::Index => Instruction::index_end(node),
			| Token::Prefix(symbol)
			| Token::Infix(symbol)
			| Token::InfixR(symbol) => Instruction::operator_end(node, symbol),
            _ => vec![]
        }
    }
	fn type_end() -> Vec<Instruction>
	{
		vec![
			Instruction::new_command(
				"constraint",
				"0",
				vec![]
			),
			Instruction::END
		]
	}
	fn method_end(_: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::Return(
				format!("-1")
				// node.nodes
				// .last()
				// .unwrap()
				// .register
				// .clone()
			),
			Instruction::END
		]
	}
	fn assign_end(node: &Node, params: &Vec<String>, types: &Vec<String>) -> Vec<Instruction>
	{
		vec![
			Instruction::new_bind(
				node.nodes.iter()
				.map(|node| node.register.clone())
				.collect(),
				params.clone(),
				types.clone()
			)
		]
		// let mut instructions = vec![Instruction::BIND];
		// let args: Vec<(String, String, String)> = signature
		// 	.values()
		// 	.enumerate()
		// 	.map(
		// 		|(i, typename)| {
		// 			(
		// 				(str::parse::<usize>(&node.register).unwrap() + i).to_string(),
		// 				node.nodes[i].register.clone(),
		// 				typename.clone()
		// 			)
		// 		}
		// 	)
		// 	.collect();
		// instructions.extend(
		// 	args
		// 	.iter()
		// 	.map(
		// 		|(address, register, typename)| {
		// 			Instruction::new_check(
		// 				address,
		// 				register,
		// 				match typename.as_str() {
		// 					"?" => None,
		// 					_ => Some(typename.clone())
		// 				}
		// 			)
		// 		}
		// 	)
		// );
		// instructions.push(
		// 	Instruction::new_bind(
		// 		args
		// 		.iter()
		// 		.map(|(address, ..)| address.clone())
		// 		.collect(),
		// 		signature.clone()
		// 	)
		// );
		// instructions
	}
	fn if_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::new_command(
				"if",
				&node.register,
				vec![]
			),
			Instruction::END
		]
	}
	fn loop_end() -> Vec<Instruction>
	{
		vec![
			Instruction::Loop,
			Instruction::END
		]
	}
	fn return_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::Return(
				if node.nodes.is_empty()
				{format!("-1")} else
				{node.nodes[0].register.clone()},
			),
		]
	}
	fn link_end(links: &Vec<String>) -> Vec<Instruction>
	{
		vec![Instruction::Link(links.clone())]
	}
	// fn use_end(names: &Vec<String>, source: &Option<String>) -> Vec<Instruction>
	// {
	// 	vec![
	// 		Instruction::internal(
	// 			".use",
	// 			match source {
	// 				Some(filename) => filename,
	// 				None => "0"
	// 			},
	// 			vec![],
	// 			names.clone()
	// 		),
	// 	]
	// }
	fn else_end() -> Vec<Instruction>
	{
		vec![Instruction::END]
	}
	fn continue_end() -> Vec<Instruction>
	{
		vec![
			Instruction::Continue
		]
	}
	fn break_end() -> Vec<Instruction>
	{
		vec![
			Instruction::Break
		]
	}
	fn receive_end(name: &str) -> Vec<Instruction>
	{
		vec![Instruction::Receive(name.into())]
	}
	fn sequence_end(node: &Node) -> Vec<Instruction>
	{
		match node.nodes[0].token {
			Token::Pair if node.nodes[0].nodes.len() == 3 => vec![
				Instruction::new_range(
					&node.register,
					&node.nodes[0].nodes[0].register,
					&node.nodes[0].nodes[1].register,
					&node.nodes[0].nodes[2].register
				)
			],
			Token::Pair => vec![
				Instruction::new_record(
					&node.register,
					node.nodes
					.iter()
					.map(|x| x.nodes[0].register.clone())
					.collect(),
					node.nodes
					.iter()
					.map(|x| x.nodes[1].register.clone())
					.collect()
				)
			],
			_ => vec![
				Instruction::new_list(
					&node.register,
					node.nodes
					.iter()
					.map(|x| x.register.clone())
					.collect()
				)
			] 
		}
	}
	// fn meta_end(node: &Node) -> Vec<Instruction>
	// {
	// 	vec![
	// 		Instruction::internal(
	// 			"meta",
	// 			&node.register, 
	// 			vec![
	// 				node.nodes[0].register.clone()
	// 			],
	// 			vec![]
	// 		)
	// 	]
	// }
	fn bind_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::new_future(
				&node.register,
				node
				.nodes
				.iter()
				.map(|x| x.register.clone())
				.collect()
			)
		]
	}
	fn right_con_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::new_write(
				&node.register,
				&node.nodes[1].register.clone()
			)
		]
	}
	fn pair_end(node: &Node) -> Vec<Instruction>
	{
		if node.nodes.len() == 3 {
			vec![
				Instruction::new_range(
					&node.register,
					&node.nodes[0].register,
					&node.nodes[1].register,
					&node.nodes[2].register
				)
			]
		} else {
			vec![]
		}
	}
	fn call_end(node: &Node) -> Vec<Instruction>
	{
		vec![
			Instruction::new_command(
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
			Instruction::new_command(
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
					|x| Instruction::new_command(
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
			Instruction::new_command(
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

// impl Instruction
// // Instruction generation for optimisations.
// {
// 	pub fn resolve_bind(instructions: &mut VecDeque<Instruction>, acc: &mut Vec<Instruction>)
// 	// Evaluates type checking for name binding, removing instructions if the type check is known to succeed.
// 	// Currently does not bother to remove unnecessary type checks.
// 	{
// 		let mut registers: Vec<String> = vec![];
// 		loop {
// 			match instructions
// 			.pop_front()
// 			.unwrap() {
// 				Instruction::Bind{signature, ..} => {
// 					acc.push(
// 						Instruction::new_bind(
// 							registers,
// 							signature.clone()
// 						)
// 					);
// 					break
// 				},
// 				Instruction::Check{address, register, typename} => {
// 					match typename {
// 						Some(_) => registers.push(register.clone()),
// 						None => {
// 							registers.push(address.clone());
// 							acc.push(
// 								Instruction::new_check(
// 									&address,
// 									&register,
// 									None
// 								)
// 							)
// 						}
// 					}
// 				},
// 				_ => {}
// 			}
// 		}
// 	}
// }