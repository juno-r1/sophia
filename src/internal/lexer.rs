use std::str::FromStr;

use malachite::Rational;
use regex::CaptureMatches;
use utils::coerce::Coerce;

use crate::internal::nodes::Node;
use crate::internal::tokens::Token;

#[derive(Debug)]
pub struct Lexer<'a> {
    iterator: CaptureMatches<'a, 'a>,
    pub token: Token,
    pub peek: Token,
}

impl <'a> Lexer<'a>
{
    pub fn new(iterator: CaptureMatches<'a, 'a>) -> Lexer
    // Implements a Pratt parser for expressions.
    // These sources helped with expression parsing:
    // https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
    // https://abarker.github.io/typped/pratt_parsing_intro.html
    // https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
    // https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html
    {
        Lexer{
            iterator,
            token: Token::EOL,
            peek: Token::EOL
        }
    }
    pub fn parse(&mut self, lbp: usize) -> Node
    // LBP: left-binding power.
    // NUD: null denotation (prefixes).
    // LED: left denotation (infixes).
    {
        self.next();
        if let Token::EOL = self.token {return Node::leaf(self.token.clone())}; // End of line.
        let mut left = self.token.clone().nud(self); // Executes null denotation of current token.
        while lbp < self.peek.lbp() { // Collect all tokens under this one.
            self.next();
            left = self.token.clone().led(self, left); // Executes left denotation of current token.
            if let Token::EOL = self.token {return Node::leaf(self.token.clone())}; // End of line.
        };
        left
    }
    pub fn next(&mut self)
    // Gets the next token, ignoring whitespace.
    {
        (self.token, self.peek) = (
            self.peek.clone(), 
            match self.iterator.next() {
                Some(cap) => {
                    if let Some(x) = cap.name("number") {
                        Token::Number(
                            Rational::from_str(x.into())
                            .unwrap()
                        )
                    } else if let Some(x) = cap.name("string") {
                        Token::String(
                            x
                            .as_str()[1..x.len() - 1] // Would be nice if indexing was isize, not going to lie.
                            .into()
                        )
                    } else if let Some(x) = cap.name("name") {
                        match x.as_str() {
                            "and" | "or" | "xor" | "in" => Token::Infix(x.to_string()),
                            "not" | "new" => Token::Prefix(x.to_string()),
                            "true" | "false" => Token::Boolean(
                                x
                                .as_str()
                                .parse()
                                .unwrap()
                            ),
                            "null" => Token::Null,
                            "if" => Token::LeftConditional,
                            "else" => Token::RightConditional,
                            _ => Token::Name(x.to_string())
                        }
                    } else if let Some(_) = cap.name("env") {
                        Token::Env(String::new())
                    } else if let Some(x) = cap.name("receive") {
                        Token::Receive(x.to_string())
                    } else if let Some(x) = cap.name("l_parens") {
                        if self.prefix() {
                            match x.as_str() {
                                "(" => Token::Parenthesis(self.collect()),
                                "[" => Token::Sequence(self.collect()),
                                "{" => Token::Meta(self.collect()),
                                _ => Token::EOL
                            }
                        } else {
                            match x.as_str() {
                                "(" => Token::Call,
                                "[" => Token::Index,
                                _ => Token::EOL
                            }
                        }
                    } else if let Some(_) = cap.name("r_parens") {
                        Token::RightBracket
                    } else if let Some(x) = cap.name("operator") {
                        if self.prefix() {
                            Token::Prefix(x.to_string())
                        } else {
                            match x.as_str() {
                                "," => Token::Concatenator,
                                ":" => Token::Pair,
                                "^" | "->" | "=>" | "." => Token::InfixR(x.to_string()),
                                "<-" => Token::Bind,
                                _ => Token::Infix(x.to_string())
                            }
                        }
                    } else {
                        Token::EOL
                    }
                },
                None => Token::EOL
            }
        )
    }
    fn prefix(&self) -> bool
    // Determines whether the next token is a prefix.
    {
        match self.peek {
            Token::Prefix(_) 		=> true,
            Token::Infix(_) 		=> true,
            Token::Bind 			=> true,
            Token::LeftConditional 	=> true,
            Token::RightConditional => true,
            Token::InfixR(_) 		=> true,
            Token::Concatenator 	=> true,
            Token::Pair 			=> true,
            Token::Call 			=> true,
            Token::Index 			=> true,
            Token::EOL 				=> true,
            _ 						=> false
        }
    }
    fn collect(&mut self) -> String
    // Collects the contents of a set of parentheses.
    // This consumes an arbitrary length of the iterator.
    // This may panic if the iterator is fully consumed, but this doesn't happen in a correct implementation.
    {
        let mut acc: String = String::new();
        let mut count: usize = 1;
        while count != 0 {
            let value: &str = self
                .iterator
                .next()
                .unwrap()
                .get(0)
                .unwrap()
                .as_str();
            match value { // Parentheses are guaranteed to be balanced and matched.
                "(" | "[" | "{" => {
                    count += 1;
                },
                ")" | "]" | "}" => {
                    count -= 1;
                    if count == 0 {break}
                }
                _ => {}
            };
            acc.push(' ');
            acc.push_str(value)
        };
        acc
        .trim()
        .into()
    }
}