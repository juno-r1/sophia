// #[cfg(test)]
// mod instructions
// {
//     use crate::internal::instructions;
// }
// #[cfg(test)]
// mod lexer
// {
//     use crate::internal::lexer;
// }
// #[cfg(test)]
// mod nodes
// {
//     use crate::internal::nodes;
// }
#[cfg(test)]
mod patterns
{
    use crate::internal::patterns;
    
    #[test]
    fn is_empty()
    {
        const FILE: [&str; 6] = [
            "",
            "\t",
            "\n",
            "// test",
            " \t \n \t // test\n // test",
            "test",
        ];
        // Rejects empty files.
        assert_eq!(patterns::is_empty(FILE[0]), true);
        // Rejects files consisting only of whitespace.
        assert_eq!(patterns::is_empty(FILE[1]), true);
        // Rejects files consisting only of newlines.
        assert_eq!(patterns::is_empty(FILE[2]), true);
        // Rejects files consisting only of comments.
        assert_eq!(patterns::is_empty(FILE[3]), true);
        // Rejects files with no significant content.
        assert_eq!(patterns::is_empty(FILE[4]), true);
        // Accepts files with any significant content.
        assert_eq!(patterns::is_empty(FILE[5]), false);
    }
    #[test]
    fn is_unquoted()
    {
        const FILE: [&str; 6] = [
            r#"'"#,
            r#"''"#,
            r#"""#,
            r#""""#,
            r#"'"'"#,
            r#""'""#,
        ];
        // Rejects unmatched '.
        assert_eq!(patterns::is_unquoted(FILE[0]), true);
        // Accepts matched ''.
        assert_eq!(patterns::is_unquoted(FILE[1]), false);
        // Rejects unmatched ".
        assert_eq!(patterns::is_unquoted(FILE[2]), true);
        // Accepts matched "".
        assert_eq!(patterns::is_unquoted(FILE[3]), false);
        // Permits unmatched " inside ''.
        assert_eq!(patterns::is_unquoted(FILE[4]), false);
        // Permits unmatched ' inside "".
        assert_eq!(patterns::is_unquoted(FILE[5]), false);
    }
    #[test]
    fn is_unmatched()
    {
        const FILE: [&str; 8] = [
            "(",
            "()",
            "[",
            "[]",
            "{",
            "{}",
            "([{)]}",
            "([{}{}])",
        ];
        // Rejects unmatched (.
        assert_eq!(patterns::is_unmatched(FILE[0]), true);
        // Accepts matched ().
        assert_eq!(patterns::is_unmatched(FILE[1]), false);
        // Rejects unmatched [.
        assert_eq!(patterns::is_unmatched(FILE[2]), true);
        // Accepts matched [].
        assert_eq!(patterns::is_unmatched(FILE[3]), false);
        // Rejects unmatched {.
        assert_eq!(patterns::is_unmatched(FILE[4]), true);
        // Accepts matched {}.
        assert_eq!(patterns::is_unmatched(FILE[5]), false);
        // Rejects nested unmatched brackets.
        assert_eq!(patterns::is_unmatched(FILE[6]), true);
        // Accepts nested matched brackets.
        assert_eq!(patterns::is_unmatched(FILE[7]), false);
    }
    #[test]
    fn normalise()
    {
        const FILE: [&str; 4] = [
            "// test",
            "    ",
            "bool int num str",
            "'bool' 'int' 'num' 'str'",
        ];
        // Replaces comments with newlines.
        assert_eq!(patterns::normalise(FILE[0]), "\n");
        // Replaces sequences of 4 spaces with \t.
        assert_eq!(patterns::normalise(FILE[1]), "\t");
        // Replaces aliased names with their canonical forms.
        assert_eq!(patterns::normalise(FILE[2]), "boolean integer number string");
        // Does not replace aliased names in string literals.
        assert_eq!(patterns::normalise(FILE[3]), "'bool' 'int' 'num' 'str'");
    }
    #[test]
    fn split()
    {
        const FILE: [&str; 2] = [
            "function(\nargs\n),\nvalue",
            "x\ny\nz",
        ];
        // Groups logical lines with trailing symbols.
        assert_eq!(
            patterns::split(FILE[0]),
            vec![
                "function(args),value"
            ]
        );
        // Splits logical lines with terminating symbols.
        assert_eq!(
            patterns::split(FILE[1]),
            vec![
                "x",
                "y",
                "z"
            ]
        );
    }
}
// #[cfg(test)]
// mod tokens
// {
//     use crate::internal::tokens;
// }