#[cfg(test)]
mod integration
{
    use std::str::FromStr;

    use malachite::Rational;
    use utils::coerce::Coerce;

    use crate::datatypes::{Range, Record, TypeDef};
    use crate::sophia::{Runtime, Value};

    fn test(integration: usize, file: usize) -> Value
    {
        Runtime::run(format!("integration/SI-{integration:}/{file:}.sph").as_str()).unwrap()
    }
    fn assert_true(test: Value)
    {
        assert_eq!(test, Value::new_boolean(true))
    }
    fn assert_false(test: Value)
    {
        assert_eq!(test, Value::new_boolean(false))
    }
    fn assert_null(test: Value)
    {
        assert_eq!(test, Value::new_none())
    }
    fn assert_number(test: Value, value: &str)
    {
        assert_eq!(test, Value::new_number(value.to_rational().unwrap()));
    }
    fn assert_string(test: Value, value: &str)
    {
        assert_eq!(test, Value::new_string(value.into()));
    }
    fn assert_type(test: Value, typedef: TypeDef)
    {
        assert_eq!(test, Value::new_type(typedef))
    }

    #[test]
    fn si_1()
    {
        // Empty file.
        assert_null(test(1, 0));
    }
    #[test]
    fn si_2()
    {
        // False.
        assert_false(test(2, 0));
        // True.
        assert_true(test(2, 1));
    }
    #[test]
    fn si_3()
    {
        // Simple integer.
        assert_number(test(3, 0), "0");
        // Integer with positive sign.
        assert_number(test(3, 1), "1");
        // Integer with negative sign.
        assert_number(test(3, 2), "-1");
        // Rational with decimal point.
        assert_number(test(3, 3), "1.2");
        // Rational with solidus.
        assert_number(test(3, 4), "0.5");
        // Large integer in exponential notation.
        assert_number(test(3, 5), "1e1111");
        // Complex rational with solidus.
        assert_number(test(3, 6), "-0.5");
        // Complex rational with decimal point and exponential notation.
        assert_number(test(3, 7), "-1.2e-2");
    }
    #[test]
    fn si_4()
    {
        // Double quotes.
        assert_string(test(4, 0), "Hello world!");
        // Single quotes.
        assert_string(test(4, 1), "Hello world!");
        // Double quotes containing unmatched single quotes.
        assert_string(test(4, 2), "'");
        // Single quotes containing unmatched double quotes.
        assert_string(test(4, 3), "\"");
        // Escape characters.
        assert_string(test(4, 4), "\0\t\n\r\"\'\\");
        // Unicode escapes.
        assert_string(test(4, 5), "\0\0");
    }
    #[test]
    fn si_5()
    {
        // Empty list.
        assert_eq!(
            test(5, 0),
            Value::new_list(vec![])
        );
        // Single-element list.
        assert_eq!(
            test(5, 1),
            Value::new_list(vec![
                Value::new_number(Rational::from_str("0").unwrap()),
            ])
        );
        // Multiple-element list.
        assert_eq!(
            test(5, 2),
            Value::new_list(vec![
                Value::new_number(Rational::from_str("0").unwrap()),
                Value::new_number(Rational::from_str("1").unwrap()),
                Value::new_number(Rational::from_str("2").unwrap()),
            ])
        );
        // Nested list.
        assert_eq!(
            test(5, 3),
            Value::new_list(vec![
                Value::new_list(vec![]),
                Value::new_list(vec![
                    Value::new_number(Rational::from_str("0").unwrap()),
                ]),
                Value::new_list(vec![
                    Value::new_number(Rational::from_str("1").unwrap()),
                    Value::new_number(Rational::from_str("2").unwrap()),
                ])
            ])
        );
    }
    #[test]
    fn si_6()
    {
        // Empty record.
        assert_eq!(
            test(6, 0),
            Value::new_record(Record::new(vec![], vec![]))
        );
        // Single-element record.
        assert_eq!(
            test(6, 1),
            Value::new_record(Record::new(vec![
                Value::new_string(format!("0")),
            ], vec![
                Value::new_string(format!("0")),
            ]))
        );
        // Multiple-element record.
        assert_eq!(
            test(6, 2),
            Value::new_record(Record::new(vec![
                Value::new_string(format!("0")),
                Value::new_string(format!("1")),
                Value::new_string(format!("2")),
            ], vec![
                Value::new_string(format!("0")),
                Value::new_string(format!("1")),
                Value::new_string(format!("2")),
            ]))
        );
        // Nested record.
        assert_eq!(
            test(6, 3),
            Value::new_record(Record::new(vec![
                Value::new_string(format!("0")),
                Value::new_string(format!("1")),
                Value::new_string(format!("3")),
            ], vec![
                Value::new_record(Record::new(vec![], vec![])),
                Value::new_record(Record::new(vec![
                    Value::new_string(format!("2")),
                ], vec![
                    Value::new_string(format!("2")),
                ])),
                Value::new_record(Record::new(vec![
                    Value::new_string(format!("4")),
                    Value::new_string(format!("5")),
                ], vec![
                    Value::new_string(format!("4")),
                    Value::new_string(format!("5")),
                ])),
            ]))
        );
    }
    #[test]
    fn si_7()
    {
        // Empty range.
        assert_eq!(
            test(7, 0),
            Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
            ))
        );
        // Zero-step range.
        assert_eq!(
            test(7, 1),
            Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
            ))
        );
        // Ascending range.
        assert_eq!(
            test(7, 2),
            Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("2").unwrap(),
                Rational::from_str("1").unwrap(),
            ))
        );
        // Descending range.
        assert_eq!(
            test(7, 3),
            Value::new_range(Range::new(
                Rational::from_str("-1").unwrap(),
                Rational::from_str("-5").unwrap(),
                Rational::from_str("-2").unwrap(),
            ))
        );
    }
    #[test]
    fn si_8()
    {
        // Any type.
        assert_true(test(8, 0));
        assert_true(test(8, 1));
        // None type.
        assert_true(test(8, 2));
        assert_false(test(8, 3));
        // Some type.
        assert_true(test(8, 4));
        assert_false(test(8, 5));
        // Number type.
        assert_true(test(8, 6));
        assert_false(test(8, 7));
        // Integer type.
        assert_true(test(8, 8));
        assert_false(test(8, 9));
        // Boolean type.
        assert_true(test(8, 10));
        assert_false(test(8, 11));
        // String type.
        assert_true(test(8, 12));
        assert_false(test(8, 13));
        // Range type.
        assert_true(test(8, 14));
        assert_false(test(8, 15));
    }
    #[test]
    fn si_9()
    {
        // Type operator.
        assert_type(test(9, 0), TypeDef::std_none());
        // Type inferral.
        assert_type(test(9, 1), TypeDef::std_integer());
    }
    #[test]
    fn si_10()
    {
        // Equality.
        assert_true(test(10, 0));
        // Inequality.
        assert_true(test(10, 1));
        // Less than.
        assert_true(test(10, 2));
        // Greater than.
        assert_true(test(10, 3));
        // Less than or equal to.
        assert_true(test(10, 4));
        // Greater than or equal to.
        assert_true(test(10, 5));
    }
    #[test]
    fn si_11()
    {
        // NOT.
        assert_true(test(11, 0));
        // AND.
        assert_true(test(11, 1));
        // OR.
        assert_true(test(11, 2));
        // XOR.
        assert_true(test(11, 3));
    }
    #[test]
    fn si_12()
    {
        // Modulus.
        assert_true(test(12, 0));
        // Addition.
        assert_true(test(12, 1));
        // Negation.
        assert_true(test(12, 2));
        // Subtraction.
        assert_true(test(12, 3));
        // Multiplication.
        assert_true(test(12, 4));
        // Division.
        assert_true(test(12, 5));
        // Division by zero.
        assert_true(test(12, 6));
        // Exponentiation.
        assert_true(test(12, 7));
        // Modulo.
        assert_true(test(12, 8));
        // Modulo by zero.
        assert_true(test(12, 9));
    }
    #[test]
    fn si_13()
    {
        // Modulus.
        assert_true(test(13, 0));
        // Addition.
        assert_true(test(13, 1));
        // Negation.
        assert_true(test(13, 2));
        // Subtraction.
        assert_true(test(13, 3));
        // Multiplication.
        assert_true(test(13, 4));
        // Division.
        assert_true(test(13, 5));
        // Division by zero.
        assert_true(test(13, 6));
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
