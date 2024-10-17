//use std::thread;
use std::env::current_dir;
use std::path::PathBuf;

use crate::datatypes::methods::Method;
use crate::datatypes::types::TypeDef;
use crate::internal::instructions::Instruction;

use super::hemera::Error;
use super::arche::{infer_namespace, stdlib, Function, Namespace, Typespace, Value};

#[derive(Debug, Clone)]
pub struct Supervisor {
    //pool_size: usize,
    root: PathBuf,
}

impl Supervisor
{
    pub fn new() -> Supervisor
    {
        Supervisor{
            // pool_size: match thread::available_parallelism() {
            //     Ok(x) => x.into(),
            //     Err(_) => 1
            // },
            root: match current_dir() {
                Ok(x) => x,
                Err(_) => PathBuf::from("~/")
            }.join("user/")
        }
    }
    pub fn open(&self, file: &str) -> Result<String, std::io::Error>
    {
        std::fs::read_to_string(self.root.join(file))
    }
}

#[derive(Debug, Clone)]
pub struct Task {
    // Namespace management.
	instructions: Vec<Instruction>,
	values: Namespace,
    types: Typespace,
    signature: Vec<TypeDef>,
    // Program state.
    pub path: usize,
    op: Instruction,
}

// def __init__( # God objects? What is she objecting to?
//     self,
//     handler: handler,
//     instructions: list[instruction],
//     namespace: dict,
//     types: dict | None = None
//     ) -> None:
//     """
//     Task identifiers.
//     """
//     self.name = instructions[0].label[0]
//     self.pid = id(self) # Guaranteed not to collide with other task PIDs in CPython
//     """
//     Namespace management.
//     """
//     self.values = arche.stdvalues | namespace
//     self.types = {k: aletheia.infer(v) for k, v in self.values.items()} if types is None else arche.stdtypes | types
//     self.signature = [] # Current type signature
//     self.properties = None # Final type override
//     """
//     Instruction execution data.
//     """
//     self.instructions = instructions # Guaranteed to be non-empty
//     self.op = instructions[0] # Current instruction
//     self.path = 1 # Instruction index
//     """
//     Program state management.
//     """
//     self.caller = None # State of the calling routine
//     self.final = aletheia.std_any # Return type of routine
//     self.handler = handler # Error handler

impl Task
{
	pub fn new(instructions: &Vec<Instruction>, values: Namespace) -> Task
	{
        let mut lib: Namespace = stdlib();
        lib.extend(values);
        let types = infer_namespace(&lib);
		Task{
			instructions: instructions.clone(),
			values: lib,
            types,
            signature: vec![],
            path: 1,
            op: instructions[0].clone()
		}
	}
    pub fn run(&mut self) -> Value
    // Task runtime loop.
    // Performs dispatch and executes instructions.
    // Errors are returned immediately to the caller.
    {
		// debug_task = 'task' in self.handler.flags # Debug runtime loop
		// self.caller = None # Reset caller
        let mut value: Value = Value::new_none();
        while self.path != 0 {
            self.op = self.instructions[self.path].clone();
			// if debug_task:
			// 	self.handler.debug_task(self)
            println!("{:?}", self.op);
            self.path += 1;
            let (address, args) = match self.op.clone() {
                Instruction::Command{address, args, ..} => (address, args),
                Instruction::Internal{address, args, ..} => (address, args),
                Instruction::Label(_) => continue
            };
            let values: Vec<Value> = match args
                .iter()
                .map(|register| self.read(register))
                .collect() {
                    Ok(x) => x,
                    Err(x) => return x
                };
            self.signature = match args
                .iter()
                .map(|register| self.describe(register))
                .collect() {
                    Ok(x) => x,
                    Err(x) => return x
                };
            value = match self.op.clone() {
                Instruction::Command{name, ..} => {
                    match self.read(&name) {
                        Ok(Value::Function(function)) => {
                            let method: &Method = match (*function).dispatch(&self.signature) {
                                Ok(x) => x,
                                Err(_) => return Value::Err(Error::DISP)
                            };
                            let value: Value = method.call(self, values);
                            self.write(&address, value, method.last.clone())
                        },
                        Err(x) => return x,
                        _ => return Value::Err(Error::CALL)
                    }
                },
                Instruction::Internal{name, ..} => {
                    match name.as_str() {
                        ".bind" => Task::intern_bind(self, values),
                        _ => return Value::Err(Error::IMPL)
                    }
                },
                _ => return Value::Err(Error::IMPL)
            };
        } value
    }
    fn read(&mut self, address: &str) -> Result<Value, Value>
    // Reads a value and returns a copy.
    {
        match self.values.get(address) {
            Some(x) => Ok(x.clone()),
            None => Err(Value::Err(Error::READ))
        }
    }
    fn describe(&mut self, address: &str) -> Result<TypeDef, Value>
    // Reads a type and returns a copy.
    {
        match self.types.get(address) {
            Some(x) => Ok(x.clone()),
            None => Err(Value::Err(Error::DESC))
        }
    }
    fn write(&mut self, address: &str, value: Value, typedef: TypeDef) -> Value
    // Writes the return value and type and returns a copy of the value.
    {
        self.values.insert(address.into(), value.clone());
        self.types.insert(address.into(), typedef);
        value
    }
}

// def execute(self) -> Any:
// 		"""
// 		Target of task.pool.apply_async().
// 		Executes flags and runtime loop.
// 		"""
// 		self.handler.debug_initial(self)
// 		try:
// 			value = self.run()
// 			return self.handler.debug_final(self, value)
// 		except SystemExit:
// 			return self.handler.debug_final(self, None)

impl Task
// Internal functions.
{
    fn intern_bind(&mut self, args: Vec<Value>) -> Value
    {
        Value::new_none()
    }
}

// def intern_bind(
//     self,
//     *args: tuple
//     ) -> None:

//     for i, name in enumerate(self.op.label):
//         self.values[name] = args[i]
//         self.types[name] = self.signature[i]