use regex::Captures;
use utils::coerce::Coerce;
use utils::re::{re_extract, re_const};

use crate::sophia::{Partial, Value};
use crate::stdlib::{namespace, Namespace};

use super::{patterns, Instruction, Lexer, Token};

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
	pub fn tree(source: &str) -> Partial<Node>
    // Here's tree!
	// Creates an AST from a file string.
    // The node takes ownership of the token.
    // The lexer must remain in this scope because CaptureMatches is horrible to work with.
	{
        let re = patterns::pattern();
        let mut lexer = Lexer::new(re.captures_iter(source));
        lexer.next();
        lexer.parse(0)
	}
    pub fn module(source: &str) -> Partial<Node>
    // Creates a module from a file.
    {
        Ok(
            Node::branch(Token::Module, vec![Node::tree(source)?])
        )
    }
    // pub fn statement(pattern: &str) -> Partial<Node>
    // // Creates a filled statement.
    // {
	// 	// if let Some(cap) = re_const(patterns::TYPE).captures(&pattern) {
	// 	// 	Node::new_type(cap)
	// 	// } else if let Some(cap) = re_const(patterns::FUNCTION).captures(&pattern) {
	// 	// 	Node::new_function(cap)
    //     Ok(
    //         if re_const(patterns::ASSIGN).is_match(&pattern) {
    //             Node::new_assign(&pattern)?
    //         } else if let Some(cap) = re_const(patterns::IF).captures(&pattern) {
    //             Node::new_if(cap)?
    //         } else if let Some(cap) = re_const(patterns::WHILE).captures(&pattern) {
    //             Node::new_while(cap)?
    //         } else if let Some(cap) = re_const(patterns::FOR).captures(&pattern) {
    //             Node::new_for(cap)?
    //         } else if let Some(cap) = re_const(patterns::RETURN).captures(&pattern) {
    //             Node::new_return(cap)?
    //         } else if let Some(cap) = re_const(patterns::LINK).captures(&pattern) {
    //             Node::new_link(cap)
    //         } else if let Some(cap) = re_const(patterns::USE).captures(&pattern) {
    //             Node::new_use(cap)
    //         } else if re_const(patterns::CONTINUE).is_match(&pattern) {
    //             Node::new_continue()
    //         } else if re_const(patterns::BREAK).is_match(&pattern) {
    //             Node::new_break()
    //         } else if re_const(patterns::ELSE).is_match(&pattern) {
    //             Node::new_else()
    //         } else {
    //             Node::expression(&pattern)?
    //         }
    //     )
    // }
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
                    acc.2.push(Node::tree(&re_extract(&cap, "expression"))?);
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
                vec![Node::tree(&re_extract(&cap, "expression"))?]
            )
        )
    }
    fn new_while(cap: Captures) -> Partial<Node>
    {
        Ok(
            Node::branch(
                Token::While,
                vec![Node::tree(&re_extract(&cap, "expression"))?]
            )
        )
    }
    fn new_for(cap: Captures) -> Partial<Node>
    {  
        Ok(
            Node::branch(
                Token::For(re_extract(&cap, "index")),
                vec![Node::tree(&re_extract(&cap, "iterator"))?]
            )
        )
    }
    fn new_return(cap: Captures) -> Partial<Node>
    {
        Ok(
            Node::branch(
                Token::Return,
                match cap.name("expression") {
                    Some(expression) => vec![Node::tree(expression.into())?],
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
        let mut namespace: Namespace = namespace::new();
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
                        Token::Module => head.nodes.last().unwrap().register.clone(),
                        _ => head.register.clone()
                    };
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
