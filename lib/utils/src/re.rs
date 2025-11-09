use regex::{Captures, Regex};

pub fn re_const(re: &str) -> Regex
{
    Regex::new(re).unwrap()
}

pub fn re_extract(cap: &Captures, name: &str) -> String
{
    cap
    .name(name)
    .unwrap()
    .as_str()
    .to_string()
}
