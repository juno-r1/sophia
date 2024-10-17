#![allow(dead_code)]
#![forbid(unsafe_code)]
#![recursion_limit="1024"]

extern crate macros;
extern crate utils;

mod sophia;
use sophia::kadmos::Parser;
use sophia::runtime::{Supervisor, Task};

mod datatypes;

mod internal;

mod stdlib;

fn main()
{
    let supervisor = Supervisor::new();
    let source: String = supervisor
        .open("main.sph")
        .expect("Couldn't find source file");
    let mut parser = Parser::new();
	parser.parse(&source);
	for item in parser.analyse(){
		println!("{}", item.to_string())
	};
	let mut task = Task::new(
		&parser.analyse(),
		parser.namespace
	);
	println!("{:?}", task.run());
}