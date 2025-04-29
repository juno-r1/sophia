use std::env;
use std::io;
use std::panic;
use std::path;
use std::thread;

use crate::datatypes::{Range, Record, TypeDef};
use crate::error;
use crate::internal::Instruction;
use crate::stdlib::{namespace, Namespace, Typespace};

use super::arche::Value;
use super::hemera::Error;
use super::hemera::Partial;
use super::iris::Pool;
use super::kadmos::parse;

#[derive(Debug)]
pub struct Runtime {
    root: path::PathBuf,
    pool: Pool,
}

impl Runtime
{
    pub fn new() -> Runtime
    {
        Runtime{
            root: env::current_dir().unwrap_or(path::PathBuf::from("~/")),
            pool: Pool::new() 
        }
    }
    pub fn run(file: &str) -> Partial<Value>
    {
        // Construct runtime.
        let runtime = Runtime::new();
        // Spawn main task.
        let mut main = runtime.spawn(file)?;
        // Execute main task.
        let builder = thread::Builder::new().name(format!("sph_main"));
        let handler = builder.spawn(move || main.run()).unwrap();
        Ok(handler.join().unwrap())
    }
}

impl Runtime
{
    pub fn open(&self, file: &str) -> io::Result<String>
    {
        std::fs::read_to_string(self.root.join(file))
    }
    pub fn spawn(&self, file: &str) -> Partial<Task>
    {
        // Read source file.
        let source = self.open(file).or(Err(Error::FILE(file.into())))?;
        // Parse input source.
        let (instructions, namespace) = parse(&source)?;
        for item in &instructions {
            println!("{:?}", item)
        };
        // Initialise task.
        Ok(Task::new(instructions, namespace))
    }
}

#[derive(Debug, Clone)]
pub struct Task {
    // Namespace management.
	instructions: Vec<Instruction>,
	values: Namespace,
    types: Typespace,
    // Program state.
    pub signature: Vec<TypeDef>,
    path: usize,
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
	fn new(instructions: Vec<Instruction>, namespace: Namespace) -> Task
	{
        // Build standard library.
        let values = namespace::stdlib(namespace);
        let types = namespace::infer(&values);
        // Create new task.
		Task{
			instructions,
			values,
            types,
            signature: vec![],
            path: 1,
            op: 0
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
            self.op = self.path;
			// if debug_task:
			// 	self.handler.debug_task(self)
            // println!("{:?}", self.op);
            self.path += 1;
            value = match self.instructions[self.op].clone() {
                Instruction::Command{name, address, args, ..} => {
                    let values: Vec<Value> = args
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect();
                    self.signature = args
                        .iter()
                        .map(|arg| self.describe(arg))
                        .collect();
                    let command: Value = self.read(&name);
                    match command {
                        Value::Function(function) => {
                            let method = function.dispatch(&self.signature);
                            let value: Value = method.call(self, values);
                            let last: TypeDef = match value {
                                Value::None if method.partial => TypeDef::std_none(),
                                _ => method.last.clone()
                            };
                            self.write(&address, value, last)
                        },
                        Value::Type(check) => {
                            let value: bool = match &values[..] {
                                [x] => check.call(&x),
                                _ => error!(DISP, self.signature)
                            };
                            self.write(&address, Value::new_boolean(value), TypeDef::std_boolean())
                        },
                        _ => error!(CALL, command)
                    }
                },
                Instruction::Bind{args, params, types} => {
                    let values: Vec<Value> = args
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect();
                    self.signature = args
                        .iter()
                        .map(|arg| self.describe(arg))
                        .collect();
                    for (index, (name, typename)) in Iterator::zip(params.iter(), types.iter()).enumerate() {
                        let value = values[index].clone();
                        match typename.as_str() {
                            "?" => {
                                self.write(&name, value, self.signature[index].clone());
                            },
                            _ => {
                                let typedef = self.read(typename);
                                let Value::Type(check) = typedef else {error!(CALL, typedef)};
                                if check.call(&value) {
                                    self.write(&name, value, *check);
                                } else {
                                    error!(TYPE, typename, value);
                                };
                            }
                        }
                    };
                    Value::new_none()
                },
                Instruction::List{address, args} => {
                    let values: Vec<Value> = args
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect();
                    self.write(
                        &address,
                        Value::new_list(values),
                        TypeDef::std_list()
                    );
                    Value::new_none()
                },
                Instruction::Range{address, start, end, step} => {
                    let start = self.read(&start);
                    let end = self.read(&end);
                    let step = self.read(&step);
                    match (start, end, step) {
                        (Value::Number(start), Value::Number(end), Value::Number(step)) => {
                            self.write(
                                &address,
                                Value::new_range(Range::new(*start, *end, *step)),
                                TypeDef::std_range()
                            );
                            Value:: new_none()
                        },
                        _ => error!(IMPL)
                    }
                }
                Instruction::Record{address, keys, values} => {
                    let keys: Vec<Value> = keys
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect();
                    let values: Vec<Value> = values
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect();
                    self.write(
                        &address,
                        Value::new_record(Record::new(keys, values)),
                        TypeDef::std_record()
                    );
                    Value::new_none()
                },
                Instruction::Return(register) => {
                    let value = self.read(&register);
                    self.path = 0;
                    value

                    // def return_none(task):
	
                    // 	if task.caller:
                    // 		task.restore() # Restore namespace of calling routine
                    // 	else:
                    // 		task.path = 0 # End task
                    // 	return None # Returns null

                    // def return_any(task, sentinel):
                        
                    // 	task.properties = typedef(task.final)
                    // 	if task.caller:
                    // 		task.restore() # Restore namespace of calling routine
                    // 	else:
                    // 		task.path = 0 # End task
                    // 	task.values[task.op.address] = sentinel # Different return address
                    // 	return sentinel
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
                _ => error!(IMPL)
            };
        } value
    }
    fn read(&mut self, address: &str) -> Value
    // Reads a value and returns a copy.
    {
        match self.values.get(address) {
            Some(x) => x.clone(),
            None => error!(FIND, address)
        }
    }
    fn describe(&mut self, address: &str) -> TypeDef
    // Reads a type and returns a copy.
    {
        match self.types.get(address) {
            Some(x) => x.clone(),
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