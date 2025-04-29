use std::collections::{BTreeMap, HashMap};
use std::env::current_dir;

use serde::Deserialize;
use serde_json;

use crate::datatypes::{FuncDef, Method, TypeDef};
use crate::sophia::{Task, Value};

use super::Namespace;

macro_rules! new_type
// Produces a key-value pair with a standard library type.
{
    ($name:expr, $method:ident) => {
        ($name.into(), Value::new_type(TypeDef::$method()))
    };
}

impl TypeDef
// Standard library types.
{
	pub fn stdlib() -> Namespace
    // Produces the standard type namespace.
	{
		BTreeMap::from(
			[
				new_type!("any", std_any),
				new_type!("none", std_none),
				new_type!("some", std_some),
				new_type!("boolean", std_boolean),
				new_type!("number", std_number),
				new_type!("integer", std_integer),
				new_type!("sequence", std_sequence),
				new_type!("string", std_string),
				new_type!("range", std_range),
				new_type!("list", std_list),
				new_type!("record", std_record),
				new_type!("function", std_function),
				new_type!("type", std_type),
			]
		)
	}
}

#[macro_export]
macro_rules! std_mod
// Defines a standard library function with its associated dependencies.
{
	($name:ident; $(std_fn!$method:tt)+) => {
		pub mod $name
		{
			use macros::std_fn;

			use crate::sophia::{Task, Value};

			$(std_fn!$method)+
		}
	};
	($name:ident: {$($statement:item)+}; $(std_fn!$method:tt)+) => {
		pub mod $name
		{
			use macros::std_fn;

			use crate::sophia::{Task, Value};

			$($statement)+
			$(std_fn!$method)+
		}
	};
}

#[derive(Debug, Deserialize)]
struct Metadata {
	name: String,
	methods: HashMap<String, Signature>,
}

#[derive(Debug, Deserialize)]
struct Signature {
	signature: Vec<String>,
	returns: String,
	partial: bool,
}

macro_rules! new_fn
// Creates a standard library function.
// Deserialises signature file, then constructs function from methods.
{
	($name:expr) => {
		($name.into(), Value::new_function(FuncDef::new(vec![])))
	};
	($name:expr, $($method:ident),*) => {{
		let metadata: Metadata = serde_json::from_str(
			&std::fs::read_to_string(
				std::fs::canonicalize(
					current_dir()
					.expect("Couldn't resolve working directory")
					.join(format!("src/stdlib/{:}.json", $name))
				).expect(&format!("Couldn't canonicalise signature file: {}", $name))
			).expect(&format!("Couldn't read signature file: {}", $name))
		).expect(&format!("Couldn't deserialise signature file: {}", $name));
		(metadata.name.into(), Value::new_function(FuncDef::new(vec![$({
			let data = &metadata.methods
				.get(stringify!($method))
				.expect(&format!("Couldn't find method: {}", stringify!($method)));
			Method::new_std(
				Task::$method,
				{
					let mut signature = vec![$name.into()];
					signature.extend(
						data.signature
						.iter()
						.map(|_| format!("_"))
					);
					signature
				},
				{
					let mut signature = vec![TypeDef::read(&data.returns)];
					signature.extend(
						data.signature
						.iter()
						.map(|x| TypeDef::read(x))
					);
					signature
				},
				true
			)
		}),*])))
	}};
}

// Standard library functions.
impl FuncDef
{
	pub fn stdlib() -> Namespace
	// Produces the standard function namespace.
	{
		BTreeMap::from(
			[
				// Operators.
				new_fn!(
					"op/sfe",
					sfe_u
				),
				new_fn!(
					"op/eql",
					eql_b
				),
				new_fn!(
					"op/nql",
					nql_b
				),
				new_fn!(
					"op/ltn",
					ltn_b
				),
				new_fn!(
					"op/gtn",
					gtn_b
				),
				new_fn!(
					"op/lql",
					lql_b
				),
				new_fn!(
					"op/gql",
					gql_b
				),
				new_fn!(
					"op/lnt",
					lnt_u
				),
				new_fn!(
					"op/lnd",
					lnd_b
				),
				new_fn!(
					"op/lor",
					lor_b
				),
				new_fn!(
					"op/lxr",
					lxr_b
				),
				new_fn!(
					"op/add",
					add_u,
					add_r,
					add_b,
					add_rn
				),
				new_fn!(
					"op/sub",
					sub_u,
					sub_r,
					sub_b,
					sub_rn
				),
				new_fn!(
					"op/mul",
					mul_b,
					mul_rn
				),
				new_fn!(
					"op/div",
					div_b,
					div_rn
				),
				new_fn!(
					"op/exp",
					exp_b
				),
				new_fn!(
					"op/mdl",
					mdl_b
				),
				// new_function!(
				// 	"in",
				// 	b_sbs_string,
				// 	b_sbs_range
				// ),
			]
		)
	}
}
