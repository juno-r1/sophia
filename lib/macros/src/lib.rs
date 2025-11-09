extern crate proc_macro;
use proc_macro::{TokenStream, TokenTree};

extern crate utils;
use utils::re::re_const;

#[proc_macro]
pub fn std_fn(stream: TokenStream) -> TokenStream
// Wraps a Rust function in the standard library interface.
// This macro expects an input with the format <type> <name> (<params>) {<block>},
// where each parameter takes the form <type> <name>.
{
	let mut iter = stream.into_iter();
	let last = match iter.next() {
		Some(TokenTree::Ident(x)) => x.to_string(),
		_ => panic!("Invalid return type for std_fn")
	};
	let name = match iter.next() {
		Some(TokenTree::Ident(x)) => x.to_string(),
		_ => panic!("Invalid name for std_fn")
	};
	let params: String = match iter.next() {
		Some(TokenTree::Group(x)) => x.to_string(),
		_ => panic!("Invalid parameters for std_fn")
	};
	// Remove parentheses from params.
	let substring = re_const(r"[^\(\)]+").find(&params);
	let signature = match substring {
		Some(sub) => re_const(r"\s*,\s*")
			.split(sub.into())
			.fold(
				String::new(),
				|mut acc, param| {
					let mut split = param.split(" ");
					let left = split.next().unwrap();
					let right = split.next().unwrap();
					acc.push_str(
						// Capture concrete data types but not abstract.
						match left {
							"Any" 		=> format!("_,"),
							"Boolean" 	=> format!("Value::Boolean({right}),"),
							"Number" 	=> format!("Value::Number({right}),"),
							"String" 	=> format!("Value::String({right}),"),
							"Range"		=> format!("Value::Range({right}),"),
							"List" 		=> format!("Value::List({right}),"),
							"Record" 	=> format!("Value::Record({right}),"),
							"Function" 	=> format!("Value::Function({right}),"),
							"Type" 		=> format!("Value::Type({right}),"),
							"Sum"		=> format!("Value::Sum({right}),"),
							_ 			=> panic!("Invalid signature for std_fn: {left} {right}")
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
		Some(sub) => re_const(r"\s*,\s*")
			.split(sub.into())
			.fold(
				vec![],
				|mut acc, param| {
					let mut split = param.split(" ");
					let index = acc.len();
					let left = split.next().unwrap();
					let right = split.next().unwrap();
					acc.push(
						match left {
							"Any" => format!("let {right} = args[{index}].clone();"),
							_ => format!("let {right} = *{right}.clone();")
						}
					);
					acc
				}
			)
			.join("\n"),
		None => String::new()
	};
	let block = match iter.next() {
		Some(TokenTree::Group(x)) => x,
		_ => panic!("Invalid body for std_fn")
	};
	let result = format!("Value::new_{}({block})", last.to_lowercase());
	format!(
		"
		impl Task
		{{
			pub fn {name}(&mut self, args: Vec<Value>) -> Value
			{{
				match &args[..] {{
					[{signature}] => {{{bindings}{result}}},
					_ => unreachable!()
				}}
			}}
		}}
		"
	)
	.parse()
	.unwrap()
}
