use std::collections::{BTreeMap, VecDeque};
use std::ops::Not;

use regex::{Captures, Regex};

use crate::internal::lexer::Lexer;
use crate::internal::patterns;
use crate::internal::tokens::Token;

#[derive(Debug, Clone)]
pub struct Node {
    pub token: Token,
    pub nodes: Vec<Node>,
    pub scope: usize,
    pub branch: bool,
	pub register: String,
}

impl Node
{
	pub fn tree(source: Vec<String>) -> Node
	// Creates an AST from a list of logical lines.
	{
		// Parse lines into statement nodes.
		let mut lines: VecDeque<Node> = source
        .into_iter()
        .filter( // Ignore empty lines.
            |line: &String| -> bool {
                Regex::new(patterns::WHITESPACE)
                .unwrap()
                .is_match(line)
                .not()
            }
        )
        .map( // Parse lines as nodes.
            |line: String| -> Node {
                let scope = patterns::count(&line, '\t');
                let (pattern, branch) =
                    if let Some(branch) = Regex::new(patterns::BRANCH)
                    .unwrap()
                    .captures(&line[scope..]) {
                        (
                            branch
                            .name("branch")
                            .unwrap()
                            .as_str()
                            .to_string(),
                            true
                        )
                    } else {
                        (
                            line[scope..].to_string(),
                            false
                        )
                    };
                let mut node = Node::statement(pattern.trim());
                node.scope = scope + 1;
                node.branch = branch;
                node
            }
        ).collect();
		// Link nodes into singly linked AST.
		let mut acc: VecDeque<Node> = VecDeque::from([Node::module()]); // Create head node.
        while let Some(line) = lines.pop_front() {
            while line.scope <= acc
            .back()
            .unwrap()
            .scope { // While not below the scope of the last node:
                let last = acc
                    .pop_back()
                    .unwrap(); // Pop last node.
                acc
                .back_mut()
                .unwrap()
                .nodes
                .push(last); // Push last node to the nodes of its head.
            };
            acc.push_back(line); // Push line to accumulator.
        };
        loop { // Fold remaining nodes.
            let last = acc
                .pop_back()
                .unwrap();
            match acc.front_mut() {
                Some(head) => {
                    head.nodes.push(last)
                },
                None => break last // Return module node.
            }
        }
	}
    pub fn module() -> Node
    // Creates the head node of a module.
    {
        Node{
            token: Token::Module,
            nodes: vec![],
            scope: 0,
            branch: false,
			register: String::from("0")
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
			register: String::from("0")
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
			register: String::from("0")
        }
    }
    pub fn expression(pattern: &str) -> Node
    // Creates a filled expression.
    // The node takes ownership of the token.
    // The lexer must remain in this scope because CaptureMatches is horrible to work with.
    {
        let re = Regex::new(&[
            patterns::NUMBER,
            patterns::STRING,
            patterns::NAME,
            patterns::ENV,
            patterns::RECEIVE,
            patterns::L_PARENS,
            patterns::R_PARENS,
            patterns::OPERATOR
        ].join("|"))
            .unwrap();
        let mut lexer = Lexer::new(re.captures_iter(pattern));
        lexer.next();
        lexer.parse(0)
    }
    pub fn statement(pattern: &str) -> Node
    // Creates a filled statement.
    {
		if let Some(cap) = Regex::new(patterns::TYPE)
		.unwrap()
		.captures(&pattern) {
			Node::new_type(cap)
		// } else if let Some(cap) = Regex::new(patterns::EVENT)
		// .unwrap()
		// .captures(&pattern) {
		// 	Node::new_event(cap)
		} else if let Some(cap) = Regex::new(patterns::FUNCTION)
		.unwrap()
		.captures(&pattern) {
			Node::new_function(cap)
		} else if Regex::new(patterns::ASSIGN)
		.unwrap()
		.is_match(&pattern) {
			Node::new_assign(&pattern)
        } else if let Some(cap) = Regex::new(patterns::IF)
        .unwrap()
        .captures(&pattern) {
            Node::new_if(cap)    
        } else if let Some(cap) = Regex::new(patterns::WHILE)
        .unwrap()
        .captures(&pattern) {
            Node::new_while(cap)
        } else if let Some(cap) = Regex::new(patterns::FOR)
        .unwrap()
        .captures(&pattern) {
            Node::new_for(cap)
        } else if let Some(cap) = Regex::new(patterns::RETURN)
        .unwrap()
        .captures(&pattern) {
            Node::new_return(cap)
        } else if let Some(cap) = Regex::new(patterns::LINK)
        .unwrap()
        .captures(&pattern) {
            Node::new_link(cap)
        } else if let Some(cap) = Regex::new(patterns::USE)
        .unwrap()
        .captures(&pattern) {
            Node::new_use(cap)
		}else if Regex::new(patterns::CONTINUE)
		.unwrap()
		.is_match(&pattern) {
			Node::new_continue()
		} else if Regex::new(patterns::BREAK)
		.unwrap()
		.is_match(&pattern) {
			Node::new_break()
        } else if Regex::new(patterns::START)
        .unwrap()
        .is_match(&pattern) {
            Node::new_start()
        } else if Regex::new(patterns::ELSE)
        .unwrap()
        .is_match(&pattern) {
            Node::new_else()
        } else {
            Node::expression(&pattern)
        }
    }
    fn new_type(cap: Captures) -> Node
    {
        let name = cap
            .name("name")
            .unwrap()
            .as_str()
            .to_string();
        let supertype: String = match cap.name("supertype") {
            Some(supertype) => supertype
                .as_str()
                .to_string(),
            None => String::from("any")
        };
		match cap.name("prototype") {
			Some(prototype) => Node::branch(
				Token::Type{
					name,
					supertype,
					prototype: true
				},
				match cap.name("expression") {
					Some(expression) => [
						Node::expression(prototype.as_str()),
						Node::expression(expression.as_str())
					].into(),
					None => [
						Node::expression(prototype.as_str())
					].into()
				}
			),
			None => Node::branch(
				Token::Type{
					name,
					supertype,
					prototype: false
				},
				match cap.name("expression") {
					Some(expression) => [
						Node::expression(expression.as_str())
					].into(),
					None => vec![],
				}
			)
		}
    }
    // fn new_event(cap: Captures) -> Node
    // {
    //     let funname = cap
    //         .name("name")
    //         .unwrap()
    //         .as_str()
    //         .to_string();
    //     let funtype = match cap.name("final") {
    //         Some(x) => x
    //         .as_str()
    //         .to_string(),
    //         None => String::from("any")
    //     };
    //     let message = cap
    //         .name("message")
    //         .unwrap()
    //         .as_str()
    //         .to_string();
    //     let check = match cap.name("check") {
    //         Some(x) => x
    //         .as_str()
    //         .trim()
    //         .to_string(),
    //         None => String::from("any")
    //     };
    //     let params = cap
    //         .name("params")
    //         .unwrap()
    //         .as_str();
    //     let signature: BTreeMap<String, String> = if params.is_empty() {
    //         BTreeMap::from(
    //             [
	// 				(funname.clone(), funtype.clone()),
    //                 (message, check)
    //             ]
    //         )
    //     } else {
    //         Regex::new(r"\s*,\s*")
    //         .unwrap()
    //         .split(params)
    //         .fold(
    //             BTreeMap::from(
    //                 [
    //                     (message, check)
    //                 ]
    //             ),
    //             |mut acc, param| {
    //                 let mut split = param.split(" ");
    //                 let left = split.next().unwrap();
    //                 match split.next() {
    //                     Some(right) => acc.insert(
    //                         right.to_string(),
    //                         left.to_string()
    //                     ),
    //                     None => acc.insert(
    //                         left.to_string(),
    //                         String::from("any")
    //                     )
    //                 };
    //                 acc
    //             }
    //         )
    //     };
    //     Node::branch(
    //         Token::Event{
	// 			name: funname,
	// 			signature
	// 		},
    //         match cap.name("expression") {
    //             Some(expression) => [
    //                 Node::expression(expression.as_str())
    //             ].into(),
    //             None => vec![]
    //         }
    //     )
    // }
    fn new_function(cap: Captures) -> Node
    {
        let funname = cap
            .name("name")
            .unwrap()
            .as_str()
            .to_string();
        let funtype = match cap.name("final") {
            Some(x) => x
            .as_str()
            .to_string(),
            None => String::from("any")
        };
        let params = cap
            .name("params")
            .unwrap()
            .as_str();
        let signature: BTreeMap<String, String> = if params.is_empty() {
            BTreeMap::from(
				[
					(funname.clone(), funtype.clone())
				]
			)
        } else {
            Regex::new(r"\s*,\s*")
            .unwrap()
            .split(params)
            .fold(
                BTreeMap::new(),
                |mut acc, param| {
                    let mut split = param.split(" ");
                    let left = split.next().unwrap();
                    match split.next() {
                        Some(right) => acc.insert(
                            right.to_string(),
                            left.to_string()
                        ),
                        None => acc.insert(
                            left.to_string(),
                            String::from("any")
                        )
                    };
                    acc
                }
            )
        };
        Node::branch(
            Token::Function{
				name: funname,
				signature
			},
            match cap.name("expression") {
                Some(expression) => [
                    Node::expression(expression.as_str())
                ].into(),
                None => vec![]
            }
        )
    }
    fn new_assign(pattern: &str) -> Node
    {
        let (signature, nodes) = Regex::new(patterns::BIND)
        .unwrap()
        .captures_iter(pattern)
        .fold(
            (
                BTreeMap::new(),
                vec![]
            ),
            |mut acc: (BTreeMap<String, String>, Vec<Node>), cap| {
                let name = cap
                    .name("name")
                    .unwrap()
                    .as_str()
                    .to_string();
                match cap.name("type") {
                    Some(x) => {
                        acc.0.insert(
                            x
                            .as_str()
                            .to_string(),
                            name
                        )    
                    },
                    None => {
                        acc.0.insert(name, String::from("any"))
                    }
                };
                acc.1.push(
                    Node::expression(
                        cap
                        .name("expression")
                        .unwrap()
                        .as_str()
                    )
                );
                acc
            }
        );
        Node::branch(
            Token::Assign(signature),
            nodes
        )
    }
    fn new_if(cap: Captures) -> Node
    {
        Node::branch(
            Token::If,
            [
                Node::expression(
                    cap
                    .name("expression")
                    .unwrap()
                    .as_str()
                )
            ].into()
        )
    }
    fn new_while(cap: Captures) -> Node
    {
        Node::branch(
            Token::While,
            [
                Node::expression(
                    cap
                    .name("expression")
                    .unwrap()
                    .as_str()
                )
            ].into()
        )
    }
    fn new_for(cap: Captures) -> Node
    {
        Node::branch(
            Token::For(
                cap
                .name("index")
                .unwrap()
                .as_str()
                .to_string()
			),
            [
                Node::expression(
                    cap
                    .name("iterator")
                    .unwrap()
                    .as_str()
                )
            ].into()
        )
    }
    fn new_return(cap: Captures) -> Node
    {
        Node::branch(
            Token::Return,
            match cap.name("expression") {
                Some(expression) => 
                    [
                        Node::expression(
                            expression
                            .as_str()
                        )
                    ].into(),
                None => vec![]
            }
        )
    }
    fn new_link(cap: Captures) -> Node
    {
        Node::branch(
            Token::Link(
                Regex::new(r"\s*,\s*")
                .unwrap()
                .split(
                    cap
                    .name("names")
                    .unwrap()
                    .as_str()
                )
                .fold(
                    vec![],
                    |mut acc, name| {
                        acc.push(name.to_string());
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
                names: Regex::new(r"\s*,\s*")
                .unwrap()
                .split(
                    cap
                    .name("names")
                    .unwrap()
                    .as_str()
                )
                .fold(
                    vec![],
                    |mut acc, name| {
                        acc.push(name.to_string());
                        acc
                    }
                ),
                source: match cap.name("source") {
                    Some(x) => Some(x
                        .as_str()
                        .to_string()
                    ),
                    None => None
                }
			},
            vec![]
        )
    }
    fn new_start() -> Node
    {
        Node::branch(
            Token::Start,
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