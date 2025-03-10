#[cfg(test)]
mod integration
{
    use std::str::FromStr;

    use malachite::num::conversion::traits::FromSciString;
    use malachite::Rational;

    use crate::datatypes::range::Range;
    use crate::datatypes::sequence::Sequence;
    use crate::datatypes::types::TypeDef;
    use crate::sophia::arche::Value;
    use crate::sophia::runtime::Runtime;

    fn test(integration: usize, file: usize) -> Result<Value, String>
    {
        Runtime::run(format!("integration/SI-{integration:}/{file:}.sph").as_str())
    }
    fn assert_true(test: Result<Value, String>)
    {
        assert_eq!(test, Ok(Value::new_boolean(true)))
    }
    fn assert_false(test: Result<Value, String>)
    {
        assert_eq!(test, Ok(Value::new_boolean(false)))
    }
    fn assert_null(test: Result<Value, String>)
    {
        assert_eq!(test, Ok(Value::new_none()))
    }
    fn assert_number(test: Result<Value, String>, value: &str)
    {
        assert_eq!(test, Ok(Value::new_number(Rational::from_sci_string(value).unwrap())));
    }
    fn assert_string(test: Result<Value, String>, value: &str)
    {
        assert_eq!(test, Ok(Value::new_string(value.into())));
    }
    fn assert_type(test: Result<Value, String>, typedef: TypeDef)
    {
        assert_eq!(test, Ok(Value::new_type(typedef)))
    }
    fn assert_error(test: Result<Value, String>, error: &str)
    {
        assert_eq!(test, Err(error.into()));
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
        // Empty return.
        assert_null(test(2, 0));
        // Return with null constant.
        assert_null(test(2, 1));
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
        // False.
        assert_false(test(5, 0));
        // True.
        assert_true(test(5, 1));
    }
    #[test]
    fn si_6()
    {
        // Single assignment.
        assert_number(test(6, 0), "0");
        // Multiple assignment with assignment order check.
        assert_number(test(6, 1), "0");
    }
    #[test]
    fn si_7()
    {
        // Empty list.
        assert_eq!(
            test(7, 0),
            Ok(Value::new_list(Sequence::new_list(vec![])))
        );
        // Single-element list.
        assert_eq!(
            test(7, 1),
            Ok(Value::new_list(Sequence::new_list(vec![
                Value::new_number(Rational::from_str("0").unwrap()),
            ])))
        );
        // Multiple-element list.
        assert_eq!(
            test(7, 2),
            Ok(Value::new_list(Sequence::new_list(vec![
                Value::new_number(Rational::from_str("0").unwrap()),
                Value::new_number(Rational::from_str("1").unwrap()),
                Value::new_number(Rational::from_str("2").unwrap()),
            ])))
        );
        // Empty record.
        assert_eq!(
            test(7, 3),
            Ok(Value::new_record(Sequence::new_record(vec![], vec![])))
        );
        // Single-element record.
        assert_eq!(
            test(7, 4),
            Ok(Value::new_record(Sequence::new_record(vec![
                Value::new_string(format!("0")),
            ], vec![
                Value::new_string(format!("0")),
            ])))
        );
        // Multiple-element record.
        assert_eq!(
            test(7, 5),
            Ok(Value::new_record(Sequence::new_record(vec![
                Value::new_string(format!("0")),
                Value::new_string(format!("1")),
                Value::new_string(format!("2")),
            ], vec![
                Value::new_string(format!("0")),
                Value::new_string(format!("1")),
                Value::new_string(format!("2")),
            ])))
        );
        // Nested list.
        assert_eq!(
            test(7, 6),
            Ok(Value::new_list(Sequence::new_list(vec![
                Value::new_number(Rational::from_str("0").unwrap()),
                Value::new_list(Sequence::new_list(vec![
                    Value::new_number(Rational::from_str("1").unwrap()),
                ])),
                Value::new_record(Sequence::new_record(vec![
                    Value::new_string(format!("2")),
                ], vec![
                    Value::new_string(format!("2")),
                ])),
            ])))
        );
        // Nested record.
        assert_eq!(
            test(7, 7),
            Ok(Value::new_record(Sequence::new_record(vec![
                Value::new_string(format!("0")),
                Value::new_string(format!("1")),
                Value::new_string(format!("2")),
            ], vec![
                Value::new_number(Rational::from_str("0").unwrap()),
                Value::new_list(Sequence::new_list(vec![
                    Value::new_number(Rational::from_str("1").unwrap()),
                ])),
                Value::new_record(Sequence::new_record(vec![
                    Value::new_string(format!("2")),
                ], vec![
                    Value::new_string(format!("2")),
                ])),
            ])))
        );
    }
    #[test]
    fn si_8()
    {
        // Empty range.
        assert_eq!(
            test(8, 0),
            Ok(Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
            )))
        );
        // Zero-step range.
        assert_eq!(
            test(8, 1),
            Ok(Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
            )))
        );
        // Ascending range.
        assert_eq!(
            test(8, 2),
            Ok(Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("2").unwrap(),
                Rational::from_str("1").unwrap(),
            )))
        );
        // Descending range.
        assert_eq!(
            test(8, 3),
            Ok(Value::new_range(Range::new(
                Rational::from_str("-1").unwrap(),
                Rational::from_str("-5").unwrap(),
                Rational::from_str("-2").unwrap(),
            )))
        );
    }
    #[test]
    fn si_9()
    {
        // Any type.
        assert_true(test(9, 0));
        assert_true(test(9, 1));
        // None type.
        assert_true(test(9, 2));
        assert_false(test(9, 3));
        // Some type.
        assert_true(test(9, 4));
        assert_false(test(9, 5));
        // Number type.
        assert_true(test(9, 6));
        assert_false(test(9, 7));
        // Integer type.
        assert_true(test(9, 8));
        assert_false(test(9, 9));
        // Boolean type.
        assert_true(test(9, 10));
        assert_false(test(9, 11));
        // String type.
        assert_true(test(9, 12));
        assert_false(test(9, 13));
        // Range type.
        assert_true(test(9, 14));
        assert_false(test(9, 15));
    }
    #[test]
    fn si_10()
    {
        // Type operator.
        assert_type(test(10, 0), TypeDef::std_none());
        // Type inferral.
        assert_type(test(10, 1), TypeDef::std_integer());
    }
    #[test]
    fn si_11()
    {
        // Type assignment.
        assert_type(test(11, 0), TypeDef::std_number());
        // Downcasting.
        assert_type(test(11, 1), TypeDef::std_integer());
        // Invalid assignment.
        assert_error(test(11, 2), "Invalid value for type string: Number(1)");
    }
    #[test]
    fn si_12()
    {
        // Equality.
        assert_true(test(12, 0));
        // Inequality.
        assert_true(test(12, 1));
        // Less than.
        assert_true(test(12, 2));
        // Greater than.
        assert_true(test(12, 3));
        // Less than or equal to.
        assert_true(test(12, 4));
        // Greater than or equal to.
        assert_true(test(12, 5));
    }
}
// #[cfg(test)]
// mod arche
// {
//     use crate::sophia::arche;
// }
// #[cfg(test)]
// mod kadmos
// {
//     use crate::sophia::kadmos;
// }
// #[cfg(test)]
// mod runtime
// {
//     use crate::sophia::runtime;
// }