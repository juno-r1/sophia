//use std::thread;
use std::env::current_dir;
use std::path::PathBuf;

use crate::internal::instructions::Instruction;

use crate::sophia::arche::Namespace;

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
	instructions: Vec<Instruction>,
	values: Namespace,
}

impl Task
{
	pub fn new(instructions: Vec<Instruction>, values: Namespace) -> Task
	{
		Task{
			instructions,
			values
		}
	}
}