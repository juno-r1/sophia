use std::env::current_dir;
use std::path::PathBuf;
use std::thread;

use crate::error;
use crate::datatypes::types::TypeDef;
use crate::internal::instructions::Instruction;

use super::arche::{infer_namespace, stdlib, Namespace, Typespace, Value};
use super::kadmos::parse;

#[derive(Debug, Clone)]
pub struct Runtime {
    pool_size: usize,
    root: PathBuf,
}

impl Runtime
{
    pub fn new() -> Runtime
    {
        Runtime{
            pool_size: match thread::available_parallelism() {
                Ok(x) => x.into(),
                Err(_) => 1
            },
            root: current_dir().unwrap_or(PathBuf::from("~/"))
        }
    }
    pub fn run(file: &str) -> Result<Value, String>
    {
        // Construct runtime.
        let runtime = Runtime::new();
        // Read source file.
        let source = runtime.open(file)?;
        // Spawn main task.
        let mut main = Task::spawn(&source)?;
        // Execute main task.
        main.execute()
    }
}

impl Runtime
{
    pub fn open(&self, file: &str) -> Result<String, String>
    {
        std::fs::read_to_string(self.root.join(file)).or(error!(FILE, file))
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
    op: usize,
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
	fn new(instructions: Vec<Instruction>, values: Namespace, types: Typespace) -> Task
	{
		Task{
			instructions,
			values,
            types,
            signature: vec![],
            path: 1,
            op: 0
		}
	}
    pub fn spawn(file: &str) -> Result<Task, String>
    {
        // Parse input source.
        let (instructions, namespace) = parse(file)?;
        // for item in parser.analyse(){
        //     println!("{:?}", item)
        // };
        // Build standard library.
        let lib = stdlib(namespace);
        let types = infer_namespace(&lib);
        // let instructions = parser.analyse();
        // Initialise task.
        Ok(Task::new(instructions, lib, types))
    }
    pub fn execute(&mut self) -> Result<Value, String>
    // Task exception layer.
    // Catches runtime errors and terminates the task safely.
    {
        let value = self.run();
        println!("{:?}", value);
        value
    }
    pub fn run(&mut self) -> Result<Value, String>
    // Task runtime loop.
    // Performs dispatch and executes instructions.
    // Errors are returned immediately to the caller.
    {
		// debug_task = 'task' in self.handler.flags # Debug runtime loop
		// self.caller = None # Reset caller
        let mut value: Value = Value::new_none();
        while self.path != 0 {
            self.op = self.path;
			// if debug_task:
			// 	self.handler.debug_task(self)
            println!("{:?}", self.op);
            self.path += 1;
            value = match self.instructions[self.op].clone() {
                Instruction::Command{name, address, args, ..} => {
                    let values: Vec<Value> = args
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect::<Result<Vec<Value>, String>>()?;
                    self.signature = args
                        .iter()
                        .map(|arg| self.describe(arg))
                        .collect::<Result<Vec<TypeDef>, String>>()?;
                    match self.read(&name)? {
                        Value::Function(function) => {
                            let method = function.dispatch(&self.signature)?;
                            let value: Value = method.call(self, values)?;
                            self.write(&address, value, method.last.clone())
                        },
                        Value::Type(check) => {
                            let value: bool = match &values[..] {
                                [x] => check.call(&x),
                                _ => return error!(DISP, name, self.signature)
                            };
                            self.write(&address, Value::new_boolean(value), TypeDef::std_boolean())
                        },
                        _ => return error!(CALL, name)
                    }
                },
                Instruction::Bind{args, signature} => {
                    for (index, (name, typename)) in signature.iter().enumerate() {
                        let value = self.read(&args[index])?;
                        let typedef = match self.read(&typename)? {
                            Value::Type(x) => *x,
                            _ => return error!(FIND, typename)
                        };
                        self.write(&name, value, typedef);
                    };
                    Value::new_none()
                },
                // Instruction::Check{address, register, typename} => {
                //     match typename {
                //         Some(name) => {},
                //         None => {}
                //     };
                //     // let definition = match self.describe(&register) {
                //     //     Ok(x) => x,
                //     //     Err(x) => return x
                //     // };
                //     // match typename {

                //     // }
                //     // let check = match self.read(&typename) {
                //     //     Ok(Value::Type(x)) => *x,
                //     //     Err(x) => return x,
                //     //     _ => return error!(FIND, typename)
                //     // };
                //     Value::new_none()
                // },
                // address = self.op.address
                // self.values[address] = value if check(self, value, write = False) else self.handler.error('TYPE', check, value)
                // self.types[address] = typedef(check)
                // return value

                // address, definition = task.op.address, task.signature[0]
                // if definition < self: # Value is subtype
                //     check = True
                // else:
                //     known = typedef(definition) # Duplicate typedef
                //     for item in self.types:
                //         if item not in definition.types and not item.check(task, value, known):
                //             check = False
                //             break
                //         else:
                //             known = typedef(known, item) # Build typedef
                //     else:
                //         check = True
                // if write:
                //     task.values[address] = check
                //     task.types[address] = typedef(std_boolean)
                // return check

                // def intern_bind(
                //     self,
                //     *args: tuple
                //     ) -> None:

                //     for i, name in enumerate(self.op.label):
                //         self.values[name] = args[i]
                //         self.types[name] = self.signature[i]
                | Instruction::START
                | Instruction::ELSE
                | Instruction::BIND
                | Instruction::END
                => continue,
                _ => return error!(IMPL)
            };
        } Ok(value)
    }
    fn read(&mut self, address: &str) -> Result<Value, String>
    // Reads a value and returns a copy.
    {
        match self.values.get(address) {
            Some(x) => Ok(x.clone()),
            None => error!(FIND, address)
        }
    }
    fn describe(&mut self, address: &str) -> Result<TypeDef, String>
    // Reads a type and returns a copy.
    {
        match self.types.get(address) {
            Some(x) => Ok(x.clone()),
            None => error!(FIND, address)
        }
    }
    fn write(&mut self, address: &str, value: Value, typedef: TypeDef) -> Value
    // Writes the return value and type and returns a copy of the value.
    {
        self.values.insert(address.into(), value.clone());
        self.types.insert(address.into(), typedef.clone());
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