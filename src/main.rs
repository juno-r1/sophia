#![allow(dead_code)]
#![recursion_limit="1024"]

extern crate macros;
extern crate utils;

mod sophia;
use sophia::runtime::Runtime;

mod datatypes;

mod internal;

mod stdlib;

fn main() -> Result<(), String>
{
	Runtime::run("user/main.sph").map(|_| ())
}