#[cfg(test)]
mod integration
{
    use std::str::FromStr;

    use malachite::num::conversion::traits::FromSciString;
    use malachite::Rational;

    use crate::datatypes::range::Range;
    use crate::datatypes::sequence::Sequence;
    use crate::sophia::arche::Value;
    use crate::sophia::runtime::Runtime;

    #[test]
    fn si_1()
    {
        // Empty file.
        assert_eq!(
            Runtime::run("integration/SI-1/0.sph"),
            Ok(Value::new_none())
        );
    }
    #[test]
    fn si_2()
    {
        // Empty return.
        assert_eq!(
            Runtime::run("integration/SI-2/0.sph"),
            Ok(Value::new_none())
        );
        // Return with null constant.
        assert_eq!(
            Runtime::run("integration/SI-2/1.sph"),
            Ok(Value::new_none())
        );
    }
    #[test]
    fn si_3()
    {
        // Simple integer.
        assert_eq!(
            Runtime::run("integration/SI-3/0.sph"),
            Ok(Value::new_number(Rational::from_str("0").unwrap()))
        );
        // Integer with positive sign.
        assert_eq!(
            Runtime::run("integration/SI-3/1.sph"),
            Ok(Value::new_number(Rational::from_str("1").unwrap()))
        );
        // Integer with negative sign.
        assert_eq!(
            Runtime::run("integration/SI-3/2.sph"),
            Ok(Value::new_number(Rational::from_str("-1").unwrap()))
        );
        // Rational with decimal point.
        assert_eq!(
            Runtime::run("integration/SI-3/3.sph"),
            Ok(Value::new_number(Rational::from_sci_string("1.2").unwrap()))
        );
        // Rational with solidus.
        assert_eq!(
            Runtime::run("integration/SI-3/4.sph"),
            Ok(Value::new_number(Rational::from_str("1/2").unwrap()))
        );
        // Large integer in exponential notation.
        assert_eq!(
            Runtime::run("integration/SI-3/5.sph"),
            Ok(Value::new_number(Rational::from_sci_string("1e1111").unwrap()))
        );
        // Complex rational with solidus.
        assert_eq!(
            Runtime::run("integration/SI-3/6.sph"),
            Ok(Value::new_number(Rational::from_str("-1/2").unwrap()))
        );
        // Complex rational with decimal point and exponential notation.
        assert_eq!(
            Runtime::run("integration/SI-3/7.sph"),
            Ok(Value::new_number(Rational::from_sci_string("-1.2e-2").unwrap()))
        );
    }
    #[test]
    fn si_4()
    {
        // Double quotes.
        assert_eq!(
            Runtime::run("integration/SI-4/0.sph"),
            Ok(Value::new_string(format!("Hello world!")))
        );
        // Single quotes.
        assert_eq!(
            Runtime::run("integration/SI-4/1.sph"),
            Ok(Value::new_string(format!("Hello world!")))
        );
        // Double quotes containing unmatched single quotes.
        assert_eq!(
            Runtime::run("integration/SI-4/2.sph"),
            Ok(Value::new_string(format!("'")))
        );
        // Single quotes containing unmatched double quotes.
        assert_eq!(
            Runtime::run("integration/SI-4/3.sph"),
            Ok(Value::new_string(format!("\"")))
        );
        // Escape characters.
        assert_eq!(
            Runtime::run("integration/SI-4/4.sph"),
            Ok(Value::new_string(format!("\0\t\n\r\"\'\\")))
        );
        // Unicode escapes.
        assert_eq!(
            Runtime::run("integration/SI-4/5.sph"),
            Ok(Value::new_string(format!("\0\0")))
        );
    }
    #[test]
    fn si_5()
    {
        // False.
        assert_eq!(
            Runtime::run("integration/SI-5/0.sph"),
            Ok(Value::new_boolean(false))
        );
        // True.
        assert_eq!(
            Runtime::run("integration/SI-5/1.sph"),
            Ok(Value::new_boolean(true))
        );
    }
    #[test]
    fn si_6()
    {
        // Single assignment.
        assert_eq!(
            Runtime::run("integration/SI-6/0.sph"),
            Ok(Value::new_number(Rational::from_str("0").unwrap()))
        );
        // Multiple assignment with assignment order check.
        assert_eq!(
            Runtime::run("integration/SI-6/1.sph"),
            Ok(Value::new_number(Rational::from_str("0").unwrap()))
        );
    }
    #[test]
    fn si_7()
    {
        // Empty list.
        assert_eq!(
            Runtime::run("integration/SI-7/0.sph"),
            Ok(Value::new_list(Sequence::new_list(vec![])))
        );
        // Single-element list.
        assert_eq!(
            Runtime::run("integration/SI-7/1.sph"),
            Ok(Value::new_list(Sequence::new_list(vec![
                Value::new_number(Rational::from_str("0").unwrap()),
            ])))
        );
        // Multiple-element list.
        assert_eq!(
            Runtime::run("integration/SI-7/2.sph"),
            Ok(Value::new_list(Sequence::new_list(vec![
                Value::new_number(Rational::from_str("0").unwrap()),
                Value::new_number(Rational::from_str("1").unwrap()),
                Value::new_number(Rational::from_str("2").unwrap()),
            ])))
        );
        // Empty record.
        assert_eq!(
            Runtime::run("integration/SI-7/3.sph"),
            Ok(Value::new_record(Sequence::new_record(vec![], vec![])))
        );
        // Single-element record.
        assert_eq!(
            Runtime::run("integration/SI-7/4.sph"),
            Ok(Value::new_record(Sequence::new_record(vec![
                Value::new_string(format!("0")),
            ], vec![
                Value::new_string(format!("0")),
            ])))
        );
        // Multiple-element record.
        assert_eq!(
            Runtime::run("integration/SI-7/5.sph"),
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
            Runtime::run("integration/SI-7/6.sph"),
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
            Runtime::run("integration/SI-7/7.sph"),
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
            Runtime::run("integration/SI-8/0.sph"),
            Ok(Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
            )))
        );
        // Zero-step range.
        assert_eq!(
            Runtime::run("integration/SI-8/1.sph"),
            Ok(Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
                Rational::from_str("0").unwrap(),
            )))
        );
        // Ascending range.
        assert_eq!(
            Runtime::run("integration/SI-8/2.sph"),
            Ok(Value::new_range(Range::new(
                Rational::from_str("0").unwrap(),
                Rational::from_str("2").unwrap(),
                Rational::from_str("1").unwrap(),
            )))
        );
        // Descending range.
        assert_eq!(
            Runtime::run("integration/SI-8/3.sph"),
            Ok(Value::new_range(Range::new(
                Rational::from_str("-1").unwrap(),
                Rational::from_str("-5").unwrap(),
                Rational::from_str("-2").unwrap(),
            )))
        );
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