extern crate proc_macro;
use proc_macro::{TokenStream, TokenTree};

extern crate regex;
use regex::Regex;

#[proc_macro]
pub fn std_fn(stream: TokenStream) -> TokenStream
// Wraps a Rust function in the standard library interface.
// This macro expects an input with the format <type> <name> (<params>) {<block>},
// where each parameter takes the form <type> <name>.
{
	let mut iter = stream
		.clone()
		.into_iter();
	let last = match iter
	.next()
	.expect("Invalid format for std_fn") {
		TokenTree::Ident(x) => x
			.clone()
			.to_string(),
		_ => panic!("Invalid format for std_fn")
	};
	let name = match iter
	.next()
	.expect("Invalid format for std_fn") {
		TokenTree::Ident(x) => x.to_string(),
		_ => panic!("Invalid format for std_fn")
	};
	let params: String = match iter
		.next()
		.expect("Invalid format for std_fn") {
			TokenTree::Group(x) => x.to_string(),
			_ => panic!("Invalid format for std_fn")
		};
	// Remove parentheses from params.
	let substring = Regex::new(r"[^\(\)]+")
		.expect("Parentheses required for arguments of std_fn")
		.find(params.as_str());
	let signature = match substring {
		Some(sub) => Regex::new(r"\s*,\s*")
			.unwrap()
			.split(sub.as_str())
			.fold(
				String::new(),
				|mut acc, param| {
					let mut split = param.split(" ");
					let left = split.next().unwrap();
					let right = split.next().unwrap();
					acc.push_str(
						// Capture concrete data types but not abstract.
						match left {
							"any" 		=> "_,".into(),
							"none" 		=> "Value::None,".into(),
							"boolean" 	=> format!("Value::Boolean({right}),"),
							"number" 	=> format!("Value::Number({right}),"),
							"string" 	=> format!("Value::String({right}),"),
							"list" 		=> format!("Value::List({right}),"),
							"record" 	=> format!("Value::Record({right}),"),
							"function" 	=> format!("Value::Function({right}),"),
							"type" 		=> format!("Value::Type({right}),"),
							_ 			=> panic!("Invalid type signature for std_fn: {left} {right}")
						}
						.as_str()
					);
					acc
				}
			),
		None => String::new()
	};
	// Bring borrowed values into local scope.
	let bindings = match substring {
		Some(sub) => Regex::new(r"\s*,\s*")
			.unwrap()
			.split(sub.as_str())
			.fold(
				String::new(),
				|mut acc, param| {
					let mut split = param.split(" ");
					let index = acc.len();
					let left = split.next().unwrap();
					let right = split.next().unwrap();
					acc.push_str(
						match left {
							"any" => format!("let {right} = args[{index}].clone();"),
							"none" => format!("let {right} = Value::None;"),
							_ => format!("let {right} = *{right}.clone();")
						}
						.as_str()
					);
					acc
				}
			),
		None => String::new()
	};
	let block = match iter
	.next()
	.expect("Invalid format for std_fn") {
		TokenTree::Group(x) => x,
		_ => panic!("Invalid format for std_fn")
	};
	let result = match last.as_str() {
		"none" => format!("{{{block}; Value::None}}"),
		_ => format!("Value::new_{last}({block})")
	};
	format!(
		"
		impl Task
		{{
			pub fn {name}(self, args: Vec<Value>) -> Value
			{{
				match &args[..] {{
					[{signature}] => {{{bindings}{result}}},
					_ => Value::Err
				}}
			}}
		}}
		"
	)
	.parse()
	.unwrap()
}