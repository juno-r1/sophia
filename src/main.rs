#![allow(dead_code)]
#![recursion_limit="1024"]

extern crate macros;
extern crate utils;

mod sophia;
use sophia::Runtime;

mod datatypes;

mod parser;

mod stdlib;

fn main()
{
	println!("{:?}", Runtime::run("user/main.sph"))
}