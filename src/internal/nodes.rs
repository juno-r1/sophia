use std::collections::VecDeque;
use std::ops::Not;

use regex::Captures;
use utils::coerce::Coerce;
use utils::re::{re_extract, re_const};

use crate::internal::lexer::Lexer;
use crate::internal::patterns;
use crate::internal::tokens::Token;
use crate::sophia::arche::Value;
use crate::sophia::hemera::Partial;
use crate::stdlib::std::{new_namespace, Namespace};

use super::instructions::Instruction;

#[derive(Debug, Clone)]
pub struct Node {
    pub token: Token,
    pub nodes: Vec<Node>,
    pub scope: usize,
    pub branch: bool,
	pub register: String,
}

impl Node
// Generic constructors.
{
    pub fn module() -> Node
    // Creates the head node of a module.
    {
        Node{
            token: Token::Module,
            nodes: vec![],
            scope: 0,
            branch: false,
			register: format!("0")
        }
    }
    pub fn leaf(token: Token) -> Node
    // Creates an unlinked leaf node.
    // The node takes ownership of the token.
    {
        Node{
            token,
            nodes: vec![],
            scope: 0,
            branch: false,
			register: format!("0")
        }
    }
    pub fn branch(token: Token, nodes: Vec<Node>) -> Node
    // Creates an unlinked branch node.
    // The node takes ownership of the token and the child nodes.
    {
        Node{
            token,
            nodes,
            scope: 0,
            branch: false,
			register: format!("0")
        }
    }
}

impl Node
// AST generation.
{
	pub fn tree(source: Vec<String>) -> Partial<Node>
	// Creates an AST from a list of logical lines.
    // Here's tree!
	{
		// Parse lines into statement nodes.
		let mut lines: VecDeque<Node> = source
        .into_iter()
        .filter( // Ignore empty lines.
            |line: &String| -> bool {
                re_const(patterns::WHITESPACE)
                .is_match(line)
                .not()
            }
        )
         // Parse lines as nodes.
        .map(
            |line: String| -> Partial<Node> {
                let scope = utils::string::count(&line, '\t');
                let (pattern, branch): (String, bool) =
                    if let Some(branch) = re_const(patterns::BRANCH).captures(&line[scope..]) {
                        (re_extract(&branch, "branch"), true)
                    } else {
                        (line[scope..].into(), false)
                    };
                let mut node = Node::statement(pattern.trim())?;
                node.scope = scope + 1;
                node.branch = branch;
                Ok(node)
            }
        ).collect::<Partial<VecDeque<Node>>>()?;
        // Create head node.
		let mut acc: VecDeque<Node> = VecDeque::from([Node::module()]);
		// Link nodes into singly linked AST.
        while let Some(line) = lines.pop_front() {
            // While not below the scope of the last node:
            while line.scope <= acc
            .back()
            .unwrap()
            .scope {
                 // Pop last node.
                let last = acc
                    .pop_back()
                    .unwrap();
                // Push last node to the nodes of its head.
                acc
                .back_mut()
                .unwrap()
                .nodes
                .push(last);
            };
            // Push line to accumulator.
            acc.push_back(line);
        };
        // Fold remaining nodes.
        loop {
            let last = acc
                .pop_back()
                .unwrap();
            match acc.front_mut() {
                // Push node to head.
                Some(head) => head.nodes.push(last),
                // Return module node.
                None => break Ok(last)
            }
        }
	}
    pub fn expression(pattern: &str) -> Partial<Node>
    // Creates a filled expression.
    // The node takes ownership of the token.
    // The lexer must remain in this scope because CaptureMatches is horrible to work with.
    {
        let re = re_const(&[
            patterns::NUMBER,
            patterns::STRING,
            patterns::NAME,
            patterns::ENV,
            patterns::RECEIVE,
            patterns::RANGE,
            patterns::RECORD,
            patterns::LIST,
            patterns::L_PARENS,
            patterns::R_PARENS,
            patterns::PAIR,
            patterns::OPERATOR,
        ].join("|"));
        let mut lexer = Lexer::new(re.captures_iter(pattern));
        lexer.next();
        lexer.parse(0)
    }
    pub fn statement(pattern: &str) -> Partial<Node>
    // Creates a filled statement.
    {
		// if let Some(cap) = re_const(patterns::TYPE).captures(&pattern) {
		// 	Node::new_type(cap)
		// } else if let Some(cap) = re_const(patterns::FUNCTION).captures(&pattern) {
		// 	Node::new_function(cap)
        Ok(
            if re_const(patterns::ASSIGN).is_match(&pattern) {
                Node::new_assign(&pattern)?
            } else if let Some(cap) = re_const(patterns::IF).captures(&pattern) {
                Node::new_if(cap)?
            } else if let Some(cap) = re_const(patterns::WHILE).captures(&pattern) {
                Node::new_while(cap)?
            } else if let Some(cap) = re_const(patterns::FOR).captures(&pattern) {
                Node::new_for(cap)?
            } else if let Some(cap) = re_const(patterns::RETURN).captures(&pattern) {
                Node::new_return(cap)?
            } else if let Some(cap) = re_const(patterns::LINK).captures(&pattern) {
                Node::new_link(cap)
            } else if let Some(cap) = re_const(patterns::USE).captures(&pattern) {
                Node::new_use(cap)
            } else if re_const(patterns::CONTINUE).is_match(&pattern) {
                Node::new_continue()
            } else if re_const(patterns::BREAK).is_match(&pattern) {
                Node::new_break()
            } else if re_const(patterns::ELSE).is_match(&pattern) {
                Node::new_else()
            } else {
                Node::expression(&pattern)?
            }
        )
    }
}

// fn new_type(cap: Captures) -> Node
// {
//     let name = cap_to_string(&cap, "name");
//     let supertype: String = match cap.name("supertype") {
//         Some(supertype) => supertype.to_string(),
//         None => format!("any")
//     };
// 	match cap.name("prototype") {
// 		Some(prototype) => Node::branch(
// 			Token::Type{
// 				name,
// 				supertype,
// 				prototype: true
// 			},
// 			match cap.name("expression") {
// 				Some(expression) => vec![
// 					Node::expression(prototype.into()),
// 					Node::expression(expression.into())
// 				],
// 				None => vec![
// 					Node::expression(prototype.into())
// 				]
// 			}
// 		),
// 		None => Node::branch(
// 			Token::Type{
// 				name,
// 				supertype,
// 				prototype: false
// 			},
// 			match cap.name("expression") {
// 				Some(expression) => vec![
// 					Node::expression(expression.into())
// 				],
// 				None => vec![],
// 			}
// 		)
// 	}
// }
// fn new_function(cap: Captures) -> Node
// {
//     let funname: String = cap_to_string(&cap, "name");
//     let funtype: String = match cap.name("final") {
//         Some(x) => x.to_string(),
//         None => format!("any")
//     };
//     let params = cap_to_string(&cap, "params");
//     let signature: IndexMap<String, String> = if params.is_empty() {
//         IndexMap::from([
//             (funname.clone(), funtype.clone())
// 		])
//     } else {
//         re_const(r"\s*,\s*")
//         .split(params)
//         .fold(
//             IndexMap::new(),
//             |mut acc, param| {
//                 let mut split = param.split(" ");
//                 let left = split.next().unwrap();
//                 match split.next() {
//                     Some(right) => acc.insert(
//                         right.into(),
//                         left.into()
//                     ),
//                     None => acc.insert(
//                         left.into(),
//                         format!("any")
//                     )
//                 };
//                 acc
//             }
//         )
//     };
//     Node::branch(
//         Token::Function{
// 			name: funname,
// 			params,
//             types
// 		},
//         match cap.name("expression") {
//             Some(expression) => vec![
//                 Node::expression(expression.into())
//             ],
//             None => vec![]
//         }
//     )
// }

impl Node
// Statement constructors.
{
    fn new_assign(pattern: &str) -> Partial<Node>
    {
        let (params, types, nodes) = re_const(patterns::BIND)
            .captures_iter(pattern)
            .try_fold(
                (vec![], vec![], vec![]),
                |mut acc: (Vec<String>, Vec<String>, Vec<Node>), cap| {
                    let name = re_extract(&cap, "name");
                    match cap.name("type") {
                        Some(x) => {
                            acc.0.push(x.to_string());
                            acc.1.push(name);
                        },
                        None => {
                            acc.0.push(name);
                            acc.1.push(format!("?"));
                        }
                    };
                    acc.2.push(Node::expression(&re_extract(&cap, "expression"))?);
                    Ok(acc)
                }
            )?;
        Ok(Node::branch(Token::Assign{params, types}, nodes))
    }
    fn new_if(cap: Captures) -> Partial<Node>
    {
        Ok(
            Node::branch(
                Token::If,
                vec![Node::expression(&re_extract(&cap, "expression"))?]
            )
        )
    }
    fn new_while(cap: Captures) -> Partial<Node>
    {
        Ok(
            Node::branch(
                Token::While,
                vec![Node::expression(&re_extract(&cap, "expression"))?]
            )
        )
    }
    fn new_for(cap: Captures) -> Partial<Node>
    {  
        Ok(
            Node::branch(
                Token::For(re_extract(&cap, "index")),
                vec![Node::expression(&re_extract(&cap, "iterator"))?]
            )
        )
    }
    fn new_return(cap: Captures) -> Partial<Node>
    {
        Ok(
            Node::branch(
                Token::Return,
                match cap.name("expression") {
                    Some(expression) => vec![Node::expression(expression.into())?],
                    None => vec![]
                }
            )
        )
    }
    fn new_link(cap: Captures) -> Node
    {
        Node::branch(
            Token::Link(
                re_const(r"\s*,\s*")
                .split(&re_extract(&cap, "names"))
                .fold(
                    vec![],
                    |mut acc, name| {
                        acc.push(name.into());
                        acc
                    }
                )
            ),
            vec![]
        )
    }
    fn new_use(cap: Captures) -> Node
    {
        Node::branch(
            Token::Use{
                names: re_const(r"\s*,\s*")
                .split(&re_extract(&cap, "names"))
                .fold(
                    vec![],
                    |mut acc, name| {
                        acc.push(name.into());
                        acc
                    }
                ),
                source: match cap.name("source") {
                    Some(x) => Some(x.to_string()),
                    None => None
                }
			},
            vec![]
        )
    }
    fn new_else() -> Node
    {
        Node::branch(
            Token::Else,
            vec![]
        )
    }
    fn new_continue() -> Node
    {
        Node::leaf(Token::Continue)
    }
    fn new_break() -> Node
    {
        Node::leaf(Token::Break)
    }
	// pub fn debug(&self, indent: usize)
	// {
	// 	println!("{}{:?}", ". ".repeat(indent), self.token);
	// 	for node in self.nodes.clone() {
	// 		node.debug(indent + 1)
	// 	}
	// }
}

impl Node
// Instruction generation.
{
	pub fn generate(mut self) -> (Vec<Instruction>, Namespace)
	// Generates a list of instructions from an AST.
	// Rust is a bit annoying about mutable references, so reaching a node is O(n).
	{
        let mut instructions: Vec<Instruction> = vec![];
        let mut namespace: Namespace = new_namespace();
		let mut path: Vec<usize> = vec![];
		let mut index: usize = 0;
        let mut constant: isize = -1;
		loop {
            // Start at top of tree.
			let mut head = &mut self;
            // Navigate to head node.
			for i in &path {
				head = head
					.nodes
					.get_mut(*i)
					.unwrap();
			}
            // Get initial instructions.
			instructions.extend(Instruction::execute(head, index));
            // Get current node.
            // Never called for leaf nodes, and doesn't need to be.
			match head.nodes.get_mut(index) {
                // Going down?
				Some(node) => {
                    // Push index to path.
					path.push(index);
                    // Reset index.
					index = 0;
                    // Set registers.
                    node.register = match &node.token {
                        | Token::Env(name)
                        | Token::Name(name)
                        | Token::Receive(name)
                        => name.clone(),
                        | Token::Number(_)
                        | Token::String(_)
                        | Token::Boolean(_)
                        | Token::Range
                        | Token::List
                        | Token::Record
                        => {
                            constant -= 1;
                            namespace.insert(
                                constant.to_string(),
                                Value::constant(&node.token)
                            );
                            constant.to_string()
                        },
                        Token::Null => format!("-1"),
                        _ => (path.iter().sum::<usize>() + 1).to_string()
                    };
				},
                // Going up?
				None => {
                    // Set context-sensitive registers.
                    head.register = match &head.token {
                        Token::Parenthesis(_) => head.nodes[0].register.clone(),
                        _ => head.register.clone()
                    };
                    println!("{:?} {}", head.token, head.register);
                    // Get final instructions.
					instructions.extend(Instruction::end(head));
                    // Increment path or exit.
					index = match path.pop() {
						Some(i) => i + 1,
						None => return (instructions, namespace)
					}
				}
			}
		}
	}
}
