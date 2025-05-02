use malachite::Rational;
use malachite::num::basic::traits::Zero;

use crate::datatypes::{Range, Record};
use crate::error;
use crate::sophia::{Partial, Value};

use super::{Lexer, Node};

const LBP_MAP: [(&str, usize); 29] = [
    ("RIGHT_BRACKET", 1),
    (",", 2),
    (":", 3),
    ("->", 4),
    ("if", 5),
    ("else", 6),
    ("or", 7),
    ("and", 8),
    ("xor", 9),
    ("=", 10),
    ("!=", 10),
    ("in", 10),
    ("<", 11),
    (">", 11),
    ("<=", 11),
    (">=", 11),
    ("&", 12),
    ("|", 12),
    ("+", 13),
    ("-", 13),
    ("*", 14),
    ("/", 14),
    ("%", 14),
    ("^", 15),
    ("?", 16),
    ("<-", 17),
    ("PREFIX", 18),
    ("LEFT_BRACKET", 19),
    (".", 20)
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Token {
    // Statements.
    Module,
    Group(String),
	Type{
		name: String,
		supertype: String,
		prototype: bool,
	},
    Function{
		name: String,
		params: Vec<String>,
        types: Vec<String>,
	},
    Assign{
        params: Vec<String>,
        types: Vec<String>,
    },
    If,
    While,
    For(String),
    Return,
    Link(Vec<String>),
    Use{
		names: Vec<String>,
		source: Option<String>
	},
    Else,
    Continue,
    Break,
    // Expression literals.
    Number(Rational),
    String(String),
    Boolean(bool),
    Range,
    List,
    Record,
    Null,
    Env(String),
    Name(String),
    Receive(String),
    Parenthesis(String),
    Sequence(String),
    // Expression groups.
    Prefix(String),
    Infix(String),
    Bind,
    LeftConditional,
    RightConditional,
    InfixR(String),
    Concatenator,
    Pair,
    Call,
    Index,
    RightBracket,
    // End-of-file.
    EOL,
}

impl Token
{
    pub fn nud(&self, lex: &mut Lexer) -> Partial<Node>
    // Creates the node for the null denotation of the token.
    // Creating the node consumes the token.
    {
        // Construct node.
        let node: Node = match self {
            Token::Parenthesis(expr) => {
                // if let Some(cap) = re_const(patterns::TYPE_EXPR).captures(&expr) {
                //     let name = format!("@");
                //     let supertype: String = re_extract(&cap, "supertype");
                //     let expression: Node = Node::expression(&re_extract(&cap, "expression"));
				// 	match cap.name("prototype") {
				// 		Some(prototype) => Node::branch(
				// 			Token::Type{
				// 				name,
				// 				supertype,
				// 				prototype: true
				// 			},
                //          	vec![
                //                 Node::expression(prototype.as_str()),
                //                 expression
                //             ]
				// 		),
                //         None => Node::branch(
				// 			Token::Type{
				// 				name,
				// 				supertype,
				// 				prototype: false
				// 			},
				// 			vec![expression]
				// 		)
                //     }
                // } else if let Some(cap) = re_const(patterns::FUNC_EXPR).captures(&expr) {
                //     let funname: String = format!("@");
                //     let funtype: String = match cap.name("final") {
                //         Some(x) => x.to_string(),
                //         None => format!("any")
                //     };
                //     let signature = &cap_to_string(&cap, "params");
                //     let (params, types) = (vec![funname.clone()], vec![funtype.clone()]);
                //     let signature: IndexMap<String, String> = if params.is_empty() {
                //         IndexMap::from(
				// 			[
				// 				(funname.clone(), funtype.clone())
				// 			]
				// 		)
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
                //     let expression: Node = Node::expression(&cap_to_string(&cap, "expression"));
                //     Node::branch(
                //         Token::Function{
				// 			name: funname,
				// 			signature
				// 		},
                //         vec![expression]
                //     )
                Node::branch(
                    Token::Parenthesis(expr.clone()),
                    if expr.is_empty() {
                        vec![]
                    } else {
                        vec![Node::tree(&expr)?]
                    }
                )
            },
            Token::Sequence(expr) => Node::branch(
                Token::Sequence(expr.clone()),
                {
                    let contents = Node::tree(&expr)?;
                    match contents.token {
                        Token::Concatenator => contents.nodes,
                        _ => vec![contents]
                    }
                }
            ),
            // Token::Meta(expr) => Node::branch(
            //     Token::Meta(expr.clone()),
            //     vec![Node::expression(&expr)]
            // ),
            Token::Prefix(_) => {
                Node::branch(
                    self.clone(),
                    vec![lex.parse(self.lbp())?]
                )
            },
            | Token::Number(_)
            | Token::String(_)
            | Token::Boolean(_)
            | Token::Range
            | Token::List
            | Token::Record
            | Token::Null
            | Token::Env(_)
            | Token::Name(_)
            | Token::Receive(_)
            => Node::leaf(self.clone()),
            Token::EOL => error!(SNTX, "Reached end of expression"),
            _ => error!(SNTX, format!("Invalid token: {self:?}"))
        };
        Ok(node)
    }
    pub fn led(&self, lex: &mut Lexer, left: Node) -> Partial<Node>
    // Creates the node for the left denotation of the token.
    // Creating the node consumes the token.
    {
        // Construct node.
        let node: Node = match self {
            Token::Infix(symbol) => Node::branch(
                Token::Infix(symbol.clone()),
                vec![
                    left.clone(),
                    lex.parse(self.lbp())?
                ]
            ),
            Token::Bind => {
                let right = lex.parse(self.lbp())?;
                Node::branch(
                    self.clone(),
                    if right.nodes.is_empty() {
                        vec![]
                    } else if let Token::Concatenator = right.nodes[0].token {
                        let mut nodes: Vec<Node> = vec![left];
                        nodes.extend(right.nodes[0].nodes.clone());
                        nodes
                    } else {
                        let mut nodes: Vec<Node> = vec![left];
                        nodes.push(right.nodes[0].clone());
                        nodes
                    }
                )
            },
            Token::LeftConditional => {
                let right = lex.parse(self.lbp())?;
                // println!("{left:?} {right:?}");
                let mut nodes: Vec<Node> = vec![left.clone()];
                if right.nodes.len() > 1 {
                    nodes.extend(
                        right.nodes[1..]
						.iter()
                        .cloned()
                    );
                };
                Node::branch(
                    self.clone(),
                    vec![
                        right.nodes[0].clone(),
                        Node::branch(
                            right.token.clone(),
                            nodes
                        )
                    ]
                )
            },
            Token::RightConditional => Node::branch(
                self.clone(),
                vec![
                    left.clone(),
                    lex.parse(self.lbp())?
                ]
            ),
            Token::InfixR(symbol) => Node::branch(
                Token::InfixR(symbol.clone()),
                vec![
                    left.clone(),
                    lex.parse(self.lbp() - 1)?
                ]
            ),
            Token::Concatenator => {
                let right = lex.parse(self.lbp() - 1)?;
                let mut nodes: Vec<Node> = vec![left.clone()];
                Node::branch(
                    self.clone(),
                    if let Token::Concatenator = right.token {
                        nodes.extend(right.nodes.clone());
                        nodes
                    } else {
                        nodes.push(right.clone());
                        nodes
                    }
                )
            },
            Token::Pair => {
                let right = lex.parse(self.lbp() - 1)?;
                let mut nodes: Vec<Node> = vec![left.clone()];
                Node::branch(
                    self.clone(),
                    if let Token::Pair = right.token {
                        nodes.extend(right.nodes.clone());
                        nodes
                    } else {
                        nodes.push(right.clone());
                        nodes
                    }
                )
            },
            Token::Call => {
                let mut nodes: Vec<Node> = vec![left.clone()];
                Node::branch(
                    self.clone(),
                    if let Token::RightBracket = lex.peek {
                        lex.next();
                        nodes
                    } else {
                        let right = lex.parse(1)?;
                        if let Token::Concatenator = right.token {
                            nodes.extend(right.nodes.clone());
                            lex.next();
                            nodes
                        } else {
                            nodes.push(right.clone());
                            lex.next();
                            nodes
                        }
                    }
                )
            },
            Token::Index => {
                let mut nodes: Vec<Node> = vec![left.clone()];
                Node::branch(
                    self.clone(),
                    if let Token::RightBracket = lex.peek {
                        lex.next();
                        nodes
                    } else {
                        let right = lex.parse(1)?;
                        if let Token::Concatenator = right.token {
                            nodes.extend(right.nodes.clone());
                            lex.next();
                            nodes
                        } else {
                            nodes.push(right.clone());
                            lex.next();
                            nodes
                        }
                    }
                )
            },
            Token::EOL => error!(SNTX, "Reached end of expression"),
            _ => error!(SNTX, format!("Invalid token: {self:?}"))
        };
        Ok(node)
    }
    pub fn lbp(&self) -> usize
    // Get left-binding power of token.
    {
        let index: &str = match self {
            Token::Prefix(_) 		=> "PREFIX",
            Token::Infix(x)         |
            Token::InfixR(x)        => x,
            Token::Bind 			=> "<-",
            Token::LeftConditional 	=> "if",
            Token::RightConditional => "else",
            Token::Concatenator 	=> ",",
            Token::Pair 			=> ":",
            Token::Call             |
            Token::Index 			=> "LEFT_BRACKET",
            Token::RightBracket 	=> "RIGHT_BRACKET",
            _ 						=> {return 0}
        };
        for item in LBP_MAP {
            if item.0 == index {
                return item.1
            }
        };
        return 0
    } 
	pub fn constant(&self) -> Value
	// Map literals to constants.
	{
		match self {
			Token::Number(x) => Value::new_number(x.clone()),
			Token::Boolean(x) => Value::new_boolean(*x),
			Token::String(x) => Value::new_string(x.clone()),
			Token::Range => Value::new_range(Range::new(Rational::ZERO, Rational::ZERO, Rational::ZERO)),
			Token::List => Value::new_list(vec![]),
			Token::Record => Value::new_record(Record::new(vec![], vec![])),
			_ => Value::new_none()
		}
	}
}