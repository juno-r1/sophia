#[cfg(test)]
mod integration
// Integration tests for Sophia.
{
    use crate::sophia::{Runtime, Value};

    fn test(integration: usize, file: usize) -> Value
    {
        Runtime::run(format!("integration/SI-{integration:}/{file:}.sph").as_str()).unwrap()
    }

    #[test]
    fn si_1()
    {
        // Empty file.
        test(1, 0).assert("null");
    }
    #[test]
    fn si_2()
    {
        // False.
        test(2, 0).assert("false");
        // True.
        test(2, 1).assert("true");
    }
    #[test]
    fn si_3()
    {
        // Simple integer.
        test(3, 0).assert("0");
        // Integer with positive sign.
        test(3, 1).assert("1");
        // Integer with negative sign.
        test(3, 2).assert("-1");
        // Rational with decimal point.
        test(3, 3).assert("1.2");
        // Rational with solidus.
        test(3, 4).assert("0.5");
        // Large integer in exponential notation.
        test(3, 5).assert("1e1111");
        // Complex rational with solidus.
        test(3, 6).assert("-0.5");
        // Complex rational with decimal point and exponential notation.
        test(3, 7).assert("-1.2e-2");
    }
    #[test]
    fn si_4()
    {
        // Double quotes.
        test(4, 0).assert(r#"'Hello world!'"#);
        // Single quotes.
        test(4, 1).assert(r#"'Hello world!'"#);
        // Double quotes containing unmatched single quotes.
        test(4, 2).assert(r#""'""#);
        // Single quotes containing unmatched double quotes.
        test(4, 3).assert(r#"'\"'"#);
        // Escape characters.
        test(4, 4).assert(r#"'\0\t\n\r\"\'\\'"#);
        // Unicode escapes.
        test(4, 5).assert(r#"'\0\0'"#);
    }
    #[test]
    fn si_5()
    {
        // Empty list.
        test(5, 0).assert("[]");
        // Single-element list.
        test(5, 1).assert("[0]");
        // Multiple-element list.
        test(5, 2).assert("[0, 1, 2]");
        // Nested list.
        test(5, 3).assert("[[], [0], [1, 2]]");
    }
    #[test]
    fn si_6()
    {
        // Empty record.
        test(6, 0).assert("[:]");
        // Single-element record.
        test(6, 1).assert("['0': '0']");
        // Multiple-element record.
        test(6, 2).assert("['0': '0', '1': '1', '2': '2']");
        // Nested record.
        test(6, 3).assert("['0': [:], '1': ['2': '2'], '3': ['4': '4', '5': '5']]");
    }
    #[test]
    fn si_7()
    {
        // Empty range.
        test(7, 0).assert("[::]");
        // Zero-step range.
        test(7, 1).assert("[0:0:0]");
        // Ascending range.
        test(7, 2).assert("[0:2:1]");
        // Descending range.
        test(7, 3).assert("[-1:-5:-2]");
    }
    // #[test]
    // fn si_2()
    // {
    //     // Empty return.
    //     assert_null(test(2, 0));
    //     // Return with null constant.
    //     assert_null(test(2, 1));
    // }
    // #[test]
    // fn si_6()
    // {
    //     // Single assignment.
    //     assert_number(test(6, 0), "0");
    //     // Multiple assignment with assignment order check.
    //     assert_number(test(6, 1), "0");
    // }
    // #[test]
    // fn si_11()
    // {
    //     // Type assignment.
    //     assert_type(test(11, 0), TypeDef::std_number());
    //     // Downcasting.
    //     assert_type(test(11, 1), TypeDef::std_integer());
    //     // Invalid assignment.
    //     assert_error(test(11, 2), error!(TYPE, "string", Value::new_number(Rational::from_str("1").unwrap())));
    // }
}
