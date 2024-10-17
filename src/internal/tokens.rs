use std::collections::BTreeMap;

use malachite::Rational;
use regex::Regex;
use utils::coerce::Coerce;

use crate::internal::lexer::Lexer;
use crate::internal::nodes::Node;
use crate::internal::patterns;

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

#[derive(Debug, Clone)]
pub enum Token {
    // Statements.
    Module,
	Type{
		name: String,
		supertype: String,
		prototype: bool,
	},
    // Event{
	// 	name: String,
	// 	signature: BTreeMap<String, String>
	// },
    Function{
		name: String,
		signature: BTreeMap<String, String>
	},
    Assign(BTreeMap<String, String>),
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
    Null,
    Env(String),
    Name(String),
    Receive(String),
    Parenthesis(String),
    Sequence(String),
    Meta(String),
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
    pub fn nud(self, lex: &mut Lexer) -> Node
    // Creates the node for the null denotation of the token.
    // Creating the node consumes the token.
    {
        match self {
            Token::Parenthesis(expr) => {
                if let Some(cap) = Regex::new(patterns::TYPE_EXPR)
                    .unwrap()
                    .captures(&expr) {
                    let name = format!("@");
                    let supertype: String = cap
                        .name("supertype")
                        .unwrap()
                        .to_string();
                    let expression: Node = Node::expression(
                        cap
                        .name("expression")
                        .unwrap()
                        .as_str()
                    );
					match cap.name("prototype") {
						Some(prototype) => Node::branch(
							Token::Type{
								name,
								supertype,
								prototype: true
							},
                         	vec![
                                Node::expression(prototype.as_str()),
                                expression
                            ]
						),
                        None => Node::branch(
							Token::Type{
								name,
								supertype,
								prototype: false
							},
							vec![expression]
						)
                    }
                } else if let Some(cap) = Regex::new(patterns::FUNC_EXPR)
                    .unwrap()
                    .captures(&expr) {
                    let funname: String = format!("@");
                    let funtype: String = match cap.name("final") {
                        Some(x) => x.to_string(),
                        None => format!("any")
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
                                        right.into(),
                                        left.into()
                                    ),
                                    None => acc.insert(
                                        left.into(),
                                        format!("any")
                                    )
                                };
                                acc
                            }
                        )
                    };
                    let expression: Node = Node::expression(
                        cap
                        .name("expression")
                        .unwrap()
                        .as_str()
                    );
                    Node::branch(
                        Token::Function{
							name: funname,
							signature
						},
                        vec![expression]
                    )
                } else {
                    Node::branch(
                        Token::Parenthesis(expr.clone()),
                        if expr.is_empty() {
                            vec![]
                        } else {
                            vec![Node::expression(&expr)]
                        }
                    )
                }
            },
            Token::Sequence(expr) => Node::branch(
                Token::Sequence(expr.clone()),
                if expr.is_empty() {
                    vec![]
                } else {
                    let contents = Node::expression(&expr);
                    match contents.token {
                        Token::Concatenator => contents.nodes,
                        _ => vec![contents]
                    }
                }
            ),
            Token::Meta(expr) => Node::branch(
                Token::Meta(expr.clone()),
                vec![Node::expression(&expr)]
            ),
            Token::Prefix(_) => {
                Node::branch(
                    self.clone(),
                    vec![lex.parse(self.lbp())]
                )
            },
            _ => Node::leaf(self)
        }
    }
    pub fn led(self, lex: &mut Lexer, left: Node) -> Node
    // Creates the node for the left denotation of the token.
    // Creating the node consumes the token.
    {
        match self {
            Token::Infix(symbol) => Node::branch(
                Token::Infix(symbol.clone()),
                vec![
                    left.clone(),
                    lex.parse(Token::Infix(symbol.clone()).lbp())
                ]
            ),
            Token::Bind => {
                let right = lex.parse(self.lbp());
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
                let right = lex.parse(self.lbp());
                println!("{left:?} {right:?}");
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
                    lex.parse(self.lbp())
                ]
            ),
            Token::InfixR(symbol) => Node::branch(
                Token::InfixR(symbol.clone()),
                vec![
                    left.clone(),
                    lex.parse(Token::InfixR(symbol.clone()).lbp() - 1)
                ]
            ),
            Token::Concatenator => {
                let right = lex.parse(self.lbp() - 1);
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
            }
            Token::Pair => {
                let right = lex.parse(self.lbp() - 1);
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
            }
            Token::Call => {
                let mut nodes: Vec<Node> = vec![left.clone()];
                Node::branch(
                    self.clone(),
                    if let Token::RightBracket = lex.peek {
                        lex.next();
                        nodes
                    } else {
                        let right = lex.parse(1);
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
            }
            Token::Index => {
                let mut nodes: Vec<Node> = vec![left.clone()];
                Node::branch(
                    self.clone(),
                    if let Token::RightBracket = lex.peek {
                        lex.next();
                        nodes
                    } else {
                        let right = lex.parse(1);
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
            }
            _ => Node::leaf(self)
        }
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
}