use std::env::current_dir;
use std::path::PathBuf;
use std::thread;

use crate::datatypes::range::Range;
use crate::datatypes::record::Record;
use crate::error;
use crate::datatypes::types::TypeDef;
use crate::internal::instructions::Instruction;
use crate::stdlib::std::{infer_namespace, stdlib, Namespace, Typespace};

use super::arche::Value;
use super::hemera::Partial;
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
    pub fn run(file: &str) -> Partial<Value>
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
    pub fn open(&self, file: &str) -> Partial<String>
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
    pub fn spawn(file: &str) -> Partial<Task>
    {
        // Parse input source.
        let (instructions, namespace) = parse(file)?;
        for item in &instructions {
            println!("{:?}", item)
        };
        // Build standard library.
        let lib = stdlib(namespace);
        let types = infer_namespace(&lib);
        // Initialise task.
        Ok(Task::new(instructions, lib, types))
    }
    pub fn execute(&mut self) -> Partial<Value>
    // Task exception layer.
    // Catches runtime errors and terminates the task safely.
    {
        let value = self.run();
        println!("{:?}", value);
        value
    }
    pub fn run(&mut self) -> Partial<Value>
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
                        .collect::<Partial<Vec<Value>>>()?;
                    self.signature = args
                        .iter()
                        .map(|arg| self.describe(arg))
                        .collect::<Partial<Vec<TypeDef>>>()?;
                    let command: Value = self.read(&name)?;
                    match command {
                        Value::Function(function) => {
                            let method = function.dispatch(&self.signature)?;
                            let value: Value = method.call(self, values)?;
                            let last: TypeDef = match value {
                                Value::None if method.partial => TypeDef::std_none(),
                                _ => method.last.clone()
                            };
                            self.write(&address, value, last)
                        },
                        Value::Type(check) => {
                            let value: bool = match &values[..] {
                                [x] => check.call(&x),
                                _ => return error!(DISP, self.signature)
                            };
                            self.write(&address, Value::new_boolean(value), TypeDef::std_boolean())
                        },
                        _ => return error!(CALL, command)
                    }
                },
                Instruction::Bind{args, params, types} => {
                    let values: Vec<Value> = args
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect::<Partial<Vec<Value>>>()?;
                    self.signature = args
                        .iter()
                        .map(|arg| self.describe(arg))
                        .collect::<Partial<Vec<TypeDef>>>()?;
                    for (index, (name, typename)) in Iterator::zip(params.iter(), types.iter()).enumerate() {
                        let value = values[index].clone();
                        match typename.as_str() {
                            "?" => {
                                self.write(&name, value, self.signature[index].clone());
                            },
                            _ => {
                                let typedef = self.read(typename)?;
                                let Value::Type(check) = typedef else {return error!(CALL, typedef)};
                                if check.call(&value) {
                                    self.write(&name, value, *check);
                                } else {
                                    return error!(TYPE, typename, value);
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
                        .collect::<Partial<Vec<Value>>>()?;
                    self.write(
                        &address,
                        Value::new_list(values),
                        TypeDef::std_list()
                    );
                    Value::new_none()
                },
                Instruction::Range{address, start, end, step} => {
                    let start = self.read(&start)?;
                    let end = self.read(&end)?;
                    let step = self.read(&step)?;
                    match (start, end, step) {
                        (Value::Number(start), Value::Number(end), Value::Number(step)) => {
                            self.write(
                                &address,
                                Value::new_range(Range::new(*start, *end, *step)),
                                TypeDef::std_range()
                            );
                            Value:: new_none()
                        },
                        _ => return error!(IMPL)
                    }
                }
                Instruction::Record{address, keys, values} => {
                    let keys: Vec<Value> = keys
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect::<Partial<Vec<Value>>>()?;
                    let values: Vec<Value> = values
                        .iter()
                        .map(|arg| self.read(arg))
                        .collect::<Partial<Vec<Value>>>()?;
                    self.write(
                        &address,
                        Value::new_record(Record::new(keys, values)),
                        TypeDef::std_record()
                    );
                    Value::new_none()
                },
                Instruction::Return(register) => {
                    let value = self.read(&register)?;
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
                _ => return error!(IMPL)
            };
        } Ok(value)
    }
    fn read(&mut self, address: &str) -> Partial<Value>
    // Reads a value and returns a copy.
    {
        match self.values.get(address) {
            Some(x) => Ok(x.clone()),
            None => error!(FIND, address)
        }
    }
    fn describe(&mut self, address: &str) -> Partial<TypeDef>
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