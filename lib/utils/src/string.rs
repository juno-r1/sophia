use regex::Regex;

pub fn count(pattern: &str, symbol: char) -> usize
// Counts occurences of a character in a string.
{
    pattern
    .chars()
    .fold(
        0,
        |mut acc: usize, ch: char| {
            acc += (ch == symbol) as usize;
            acc
        }
    )
}
pub fn unescape(pattern: &str) -> String
// Converts unicode escape characters to their canonical forms.
{
    Regex::new(r#"\\u\{(?<code>.+?)\}"#)
    .unwrap()
    .replace_all(
        pattern,
        |cap: &regex::Captures| -> String {
            match cap.name("code") {
                Some(x) => char::from_u32(
                    u32::from_str_radix(x.as_str(), 16).unwrap()
                ).unwrap().into(),
                None => panic!("Invalid unicode escape")
            }
        }
    ).to_string()
}