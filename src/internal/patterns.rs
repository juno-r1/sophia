use regex::Regex;
use utils::coerce::Coerce;

// Regex line patterns.
pub const EMPTY:        &str = r#"^((?:\s*\n?)|(?:\s*//.*\n?))*$"#;
pub const UNQUOTED:     &str = r#"(?<closed>(?:'.*?')|(?:".*?"))|(?<open>(?:'[^']*?$)|(?:"[^"]*?$))"#;
pub const COMMENT:      &str = r#"(\s*//.*?(?:\n|$))"#;
pub const TRAILING:     &str = r#"(?<start>\n\s*[,;'"\)\]\}])|(?<end>[,;'"\(\[\{]\n\s*)|(?<empty>\s*\n)|(?<sentinel>\s*$)"#;
pub const WHITESPACE:   &str = r#"^\s*$"#;
pub const TABSPACE:		&str = r#"    "#;

// Regex statement patterns.
pub const BRANCH:       &str = r#"^else (?<branch>.+)$"#;
pub const TYPE:         &str = r#"^type (?<name>\w+)( extends (?<supertype>\w+))?( with (?<prototype>.*))?((:$)|(\s*=>\s*(?<expression>.+)))"#;
pub const FUNCTION:     &str = r#"^(?<name>\w+)( (?<final>\w+))?\s*\((?<params>(\w+( \w+)?(\s*,\s*)?)*)\)((:$)|(\s*=>\s*(?<expression>.+)))"#;
pub const ASSIGN:       &str = r#"^(\w+( \w+)?:\s*.+(\s*;\s*)?)+$"#;
pub const BIND:         &str = r#"(?<name>\w+)( (?<type>\w+))?\:\s*(?<expression>.+?)(;|$)"#;
pub const IF:           &str = r#"^if (?<expression>.+):$"#;
pub const WHILE:        &str = r#"^while (?<expression>.+):$"#;
pub const FOR:          &str = r#"^for (?<index>\w+) in (?<iterator>.+):$"#;
pub const RETURN:       &str = r#"^return( (?<expression>.+))?$"#;
pub const LINK:         &str = r#"^link (?<names>(\w+(\s*,\s*)?)+)$"#;
pub const USE:          &str = r#"^use (?<names>(\w+(\s*,\s*)?)+)(\s*from\s+(?<source>\w+))?"#;
pub const CONTINUE:     &str = r#"^continue$"#;
pub const BREAK:        &str = r#"^break$"#;
pub const ELSE:         &str = r#"^else:$"#;

// Regex expression patterns.
pub const TYPE_EXPR:    &str = r#"^extends (?<supertype>\w+)( with (?<prototype>.*))?\s*=>\s*(?<expression>.+)$"#;
pub const FUNC_EXPR:    &str = r#"^(?<params>(\w+( \w+)?(\s*,\s*)?)*)\s*=>\s*(?<expression>.+?)(\s*=>\s*(?<final>\w+)$)?"#;
pub const NUMBER:       &str = r#"(?<number>[+-]?\d+([\./]\d*)?)"#; // Any number of the format x(.y) or x(/y).
pub const STRING:       &str = r#"(?<string>('.*?')|(".*?"))"#; // Any symbols between single or double quotes.
pub const NAME:         &str = r#"(?<name>\w+)"#; // Any word.
pub const ENV:          &str = r#"(?<env>@)"#;
pub const RECEIVE:      &str = r#"(?<receive>\>\w+)"#;
pub const L_PARENS:     &str = r#"(?<l_parens>[\(\[\{])"#;
pub const R_PARENS:     &str = r#"(?<r_parens>[\)\]\}])"#;
pub const OPERATOR:     &str = r#"(?<operator>[^\s\d\w\(\[\{\'\"\@]+)"#; // Any other symbol.

pub fn is_empty(source: &str) -> bool
{
    Regex::new(EMPTY)
    .unwrap()
    .is_match(source)
}
pub fn is_unquoted(source: &str) -> bool
{
    Regex::new(UNQUOTED)
    .unwrap()
    .captures_iter(source)
    .fold(false, |acc, cap| acc || cap.name("open").is_some())
}
pub fn is_unmatched(source: &str) -> bool
{
    match Regex::new(&[
        STRING,
        L_PARENS,
        R_PARENS
    ].join("|"))
    .unwrap()
    .captures_iter(source)
    .try_fold(
        vec![],
        |mut acc, cap| {
            if let Some(_) = cap.name("string") {
                Some(acc)
            } else if let Some(x) = cap.name("l_parens") {
                acc.push(x); Some(acc)
            } else if let Some(x) = cap.name("r_parens") {
                if let Some(y) = acc.pop() {
                    match y.as_str() {
                        "(" if x.as_str() == ")" => Some(acc),
                        "[" if x.as_str() == "]" => Some(acc),
                        "{" if x.as_str() == "}" => Some(acc),
                        _ => None
                    }
                } else {
                    None
                }
            } else {
                None
            }
        }
    ) {
        Some(x) => !x.is_empty(),
        None => true
    }
}
pub fn normalise(source: &str) -> String
{
	let mut source: String = Regex::new(COMMENT) // Remove comments.
		.unwrap()
		.replace_all(source, "\n")
		.into();
	source = Regex::new(TABSPACE) // Replace sequences of 4 spaces with tabs.
		.unwrap()
		.replace_all(&source, "\t")
		.into();
    Regex::new(&[
        STRING,
        NAME
    ].join("|"))
    .unwrap()
    .replace_all(
        &source,
        |cap: &regex::Captures| -> String {
            if let Some(x) = cap.name("string") {
                x.as_str()
            } else if let Some(x) = cap.name("name") {
                match x.as_str() {
                    "bool" => "boolean",
                    "int" => "integer",
                    "num" => "number",
                    "str" => "string",
                    _ => x.as_str()
                }
            } else {
                ""
            }.into()
        }
    ).into()
}
pub fn split(source: &str) -> Vec<String>
{
    Regex::new(TRAILING)
    .unwrap()
    .replace_all(
        source,
        |cap: &regex::Captures| -> String {
            if let Some(x) = cap.name("start") { // Trailing after a newline.
                x
                .as_str()
                .chars()
                .last()
                .unwrap()
                .into()
            }
            else if let Some(x) = cap.name("end") { // Trailing before a newline.
                x
                .as_str()
                .chars()
                .nth(0)
                .unwrap()
                .into()
            }
            else {
                cap
                .get(0)
                .unwrap()
                .to_string()
            }
        }
    )
    .to_string()
    .split("\n")
    .map(|line| line.into())
    .collect()
}