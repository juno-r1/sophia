// Implements multimethods.
// Multimethods enable multiple dispatch on functions. Functions dispatch for
// the arity and types of their arguments. The precedence for dispatch is
// left-to-right, then most to least specific type.
// Dispatch is implemented using a singly linked binary search
// tree. It is only ever necessary to traverse downward.

use std::collections::{HashMap, BTreeMap};
use std::env::current_dir;

use serde::Deserialize;
use serde_json;

use crate::sophia::arche::{Namespace, Value};
use crate::sophia::hemera::Error;
use crate::sophia::runtime::Task;

use super::methods::{Method, Predicate};
use super::types::TypeDef;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FuncDef {
	// Branch node.
	Node{
		truepath: Box<FuncDef>,
		falsepath: Box<FuncDef>,
		property: Predicate,
		index: usize,
	},
	// Leaf node containing method.
	Leaf(Method),
	// Leaf node indicating that dispatch failed.
	Undefined,
}

impl FuncDef
{
	pub fn new(methods: Vec<Method>) -> FuncDef
	// 	Creates a new built-in method from zero or more callables.
	{
		let mut funcdef = FuncDef::Undefined;
		for method in methods {
			funcdef = funcdef.extend(method);
		};
		funcdef
	}
	fn new_arity(truepath: FuncDef, falsepath: FuncDef, arity: usize) -> FuncDef
	// Constructs a node where the methods have different arities.
	{
		FuncDef::Node{
			truepath: Box::new(truepath),
			falsepath: Box::new(falsepath),
			property: Predicate::new_any(),
			index: arity
		}
	}
	fn new_node(truepath: FuncDef, falsepath: FuncDef, property: Predicate, index: usize) -> FuncDef
	// Constructs a node where the methods are distinguished by minimum dispatch criteria.
	{
		FuncDef::Node{
			truepath: Box::new(truepath),
			falsepath: Box::new(falsepath),
			property,
			index
		}
	}
	fn extend(&self, new: Method) -> FuncDef
	// Add a node to the tree.
	{
		match self {
			Self::Node{truepath, falsepath, property, index} => {
				if new.arity == 0 {
					match *falsepath.clone() {
						// Null method already exists.
						FuncDef::Leaf(x) if x.arity == 0 => FuncDef::new_arity(*truepath.clone(), FuncDef::Leaf(new), 0),
						// Null method does not already exist.
						_ => FuncDef::new_arity(self.clone(), FuncDef::Leaf(new), 0)
					}
				} else if *index < new.arity && new.signature[*index].check(property) {
					FuncDef::new_node(
						truepath.extend(new),
						*falsepath.clone(),
						property.clone(),
						*index
					)
				} else {
					FuncDef::new_node(
						*truepath.clone(),
						falsepath.extend(new),
						property.clone(),
						*index
					)
				}
			},
			Self::Leaf(old) => {
				if new.signature == old.signature {
					FuncDef::Leaf(new)
				} else if new.arity > old.arity {
					FuncDef::new_arity(
						FuncDef::Leaf(new.clone()),
						FuncDef::Leaf(old.clone()),
						old.arity
					)
				} else if new.arity < old.arity {
					FuncDef::new_arity(
						FuncDef::Leaf(old.clone()),
						FuncDef::Leaf(new.clone()),
						new.arity
					)
				} else {
					for i in 0..new.arity {
						let (x, y): (TypeDef, TypeDef) = (new.signature[i].clone(), old.signature[i].clone());
						match x.criterion(&y) {
							Some(crit) => return FuncDef::new_node(
								FuncDef::Leaf(new),
								FuncDef::Leaf(old.clone()),
								crit.clone(),
								i
							),
							None => {}
						};
						match y.criterion(&x) {
							Some(crit) => return FuncDef::new_node(
								FuncDef::Leaf(old.clone()),
								FuncDef::Leaf(new),
								crit.clone(),
								i
							),
							None => {}
						};
					};
					// Whoops!
					panic!("How did we get here?\n{:?}\n{:?}", new, old)
				}
			},
			// Empty function.
			Self::Undefined => {
				FuncDef::Leaf(new)
			}
		}
	}
	pub fn dispatch(&self, signature: &Vec<TypeDef>) -> Result<&Method, Error>
	// Multiple dispatch algorithm, with help from Julia:
	// https://github.com/JeffBezanson/phdthesis
	// Binary search tree yields closest key for method, then key is verified.
	{
		match self { // Traverse tree, terminate upon reaching leaf node.
			FuncDef::Node{truepath, falsepath, property, index} => {
				if signature.len() != 0 &&
				match signature.get(*index) {
					Some(x) => x.check(property),
					None => return Err(Error::DISP)
				}
				{truepath.dispatch(signature)} else
				{falsepath.dispatch(signature)}
			},
			FuncDef::Leaf(method) => Ok(method),
			FuncDef::Undefined => Err(Error::DISP)
		}
	}
}

// class multimethod:

// 	def __call__(
// 		self,
// 		task,
// 		*args: tuple
// 		) -> None:

// 		address, signature, arity = task.op.address, task.signature, task.op.arity
// 		instance = self.true if signature else self.false
// 		while instance: # Traverse tree; terminates upon reaching leaf node
// 			instance = instance.true if instance.index < arity and instance.check(signature) else instance.false
// 		if instance is None or instance.arity != arity:
// 			task.handler.error('DISP', instance.name, signature)
// 		for i, item in enumerate(signature): # Verify type signature
// 			if item > instance.signature[i]:
// 				task.handler.error('DISP', instance.name, signature)
// 		final = instance.final
// 		"""
// 		Execute method and write result to registers.
// 		"""
// 		value = instance.routine(task, *args)
// 		if instance.instructions:
// 			task.values[instance.name] = self
// 			task.types[instance.name] = task.types[task.op.name]
// 		task.values[address] = value
// 		if value is None: # Null return override
// 			task.types[address] = std_none
// 		elif final.types:
// 			task.types[address] = task.properties or final
// 		else:
// 			task.types[address] = task.properties or infer(value)
// 		task.properties = None
// 		return value

// 	def __add__(
// 		self,
// 		other
// 		) -> Self:
// 		"""
// 		Multimethod composition.
// 		This operator is right-binding; self comes before x.
// 		"""
// 		new = funcdef()
// 		for method in self.collect(): # Methods of 1st function
// 			"""
// 			Dispatch to link between self's methods and x's methods.
// 			"""
// 			signature, arity = [method.final], 1
// 			instance = other.true if signature else other.false
// 			while instance: # Traverse tree; terminates upon reaching leaf node
// 				instance = instance.true if instance.index < arity and instance.check(signature) else instance.false
// 			if instance is None or instance.arity != arity:
// 				continue
// 			for i, item in enumerate(signature): # Verify type signature
// 				if item > instance.signature[i]:
// 					continue
// 			"""
// 			Rewrite instructions and create composed method.
// 			"""
// 			left = method.instructions if method.instructions else instruction.left(method, instance)
// 			right = instance.instructions if instance.instructions else instruction.right(instance)
// 			instructions = [
// 				instruction('.skip', instance.params[0], item.args, label = item.label)
// 				if item.name == 'return'
// 				else instruction(item.name, item.address, item.args, label = item.label)
// 				for item in left
// 			] + right
// 			names = ['{0}.{1}'.format(instance.name, method.name)] + method.params
// 			types = [instance.final] + method.signature
// 			new.extend(function_method(instructions, names, types, user = True))
// 		return None if new.true is None and new.false is None else new

// 	def collect(self) -> list[method]:
// 		"""
// 		Collect all methods.
// 		The order of the methods is not guaranteed.
// 		"""
// 		x, y = self.true, self.false
// 		x = x.collect() if x else ([] if x is None else [x])
// 		y = y.collect() if y else ([] if y is None else [y])
// 		return x + y

// 	def debug(
// 		self,
// 		level: int = 0
// 		) -> None:
	
// 		print(('. ' * level) + str(self), file = stderr)
// 		if self:
// 			if self.true is not None:
// 				self.true.debug(level + 1)
// 			if self.false is not None:
// 				self.false.debug(level + 1)

#[derive(Debug, Deserialize)]
pub struct Signature {
	name: String,
	signature: Vec<String>,
	last: String,
	total: bool,
}

// Standard library functions.
impl FuncDef
{
		// for item in methods:
		// 	data = metadata[item.__name__] # Retrieve method signature from Kleio
		// 	names = [data['name']] + [str(i) for i in range(len(data['signature']))]
		// 	types = [typedef.read(data['final'])] + [typedef.read(i) for i in data['signature']]
		// 	self.extend(function_method(item, names, types))
	pub fn stdlib() -> Namespace
	{
		// Deserialise signature file.
		let signatures: HashMap<String, Signature> = serde_json::from_str(
			&std::fs::read_to_string(
				current_dir()
				.expect("Couldn't find signature file")
				.join("src/stdlib/kleio.json")
			).expect("Couldn't read signature file")
		).expect("Couldn't deserialise signature file");
		// Produces a key-value pair with a standard library function.
		macro_rules! new_function
		{
			($name:expr) => {
				($name.into(), Value::new_function(FuncDef::new(vec![])))
			};
			($name:expr, $($method:ident),*) => {
				($name.into(), Value::new_function(FuncDef::new(vec![$(
					Method::new_method_std(
						Task::$method,
						{
							let data = &signatures
								.get(stringify!($method))
								.unwrap();
							let mut signature = BTreeMap::from(
								[
									(
										$name.into(),
										TypeDef::read(&data.last)
									)
								]
							);
							signature.extend(
								BTreeMap::from_iter(
									data.signature
									.iter()
									.map(
										|x|
										(
											format!("_"),
											TypeDef::read(x)
										)
									)
								)
							);
							signature
						}
					)
				),*])))
			};
		}
		// Produces the standard function namespace.
		HashMap::from(
			[
				// Built-ins.
				new_function!(
					"return",
					return_none,
					return_any
				),
				// Operators.
				new_function!(
					"+",
					u_add,
					b_add
				),
				new_function!(
					"-",
					u_sub,
					b_sub
				),
				new_function!(
					"*",
					b_mul
				),
				new_function!(
					"/",
					b_div
				),
				new_function!(
					"^",
					b_exp
				),
				new_function!(
					"%",
					b_mdl
				),
				new_function!(
					"=",
					b_eql
				),
				new_function!(
					"!=",
					b_nql
				),
				new_function!(
					"<",
					b_ltn
				),
				new_function!(
					">",
					b_gtn
				),
				new_function!(
					"<=",
					b_lql
				),
				new_function!(
					">=",
					b_gql
				),
				new_function!(
					"in",
					b_sbs_string,
					b_sbs_range
				),
				new_function!(
					"not",
					u_lnt
				),
				new_function!(
					"and",
					b_lnd
				),
				new_function!(
					"or",
					b_lor
				),
				new_function!(
					"xor",
					b_lxr
				),
			]
		)
	}
}