#[cfg(test)]
mod integration
{
    use std::str::FromStr;

    use malachite::num::conversion::traits::FromSciString;
    use malachite::Rational;

    use crate::sophia::arche::Value;
    use crate::sophia::runtime::Runtime;

    #[test]
    fn si_1()
    {
        assert_eq!(
            Runtime::run("integration/SI-1/0.sph"),
            Ok(Value::new_none())
        );
    }
    #[test]
    fn si_2()
    {
        assert_eq!(
            Runtime::run("integration/SI-2/0.sph"),
            Ok(Value::new_none())
        );
        assert_eq!(
            Runtime::run("integration/SI-2/1.sph"),
            Ok(Value::new_none())
        );
    }
    #[test]
    fn si_3()
    {
        assert_eq!(
            Runtime::run("integration/SI-3/0.sph"),
            Ok(Value::new_number(Rational::from_str("0").unwrap()))
        );
        assert_eq!(
            Runtime::run("integration/SI-3/1.sph"),
            Ok(Value::new_number(Rational::from_str("1").unwrap()))
        );
        assert_eq!(
            Runtime::run("integration/SI-3/2.sph"),
            Ok(Value::new_number(Rational::from_str("-1").unwrap()))
        );
        assert_eq!(
            Runtime::run("integration/SI-3/3.sph"),
            Ok(Value::new_number(Rational::from_sci_string("1.2").unwrap()))
        );
        assert_eq!(
            Runtime::run("integration/SI-3/4.sph"),
            Ok(Value::new_number(Rational::from_str("1/2").unwrap()))
        );
        assert_eq!(
            Runtime::run("integration/SI-3/5.sph"),
            Ok(Value::new_number(Rational::from_sci_string("1e1111").unwrap()))
        );
        assert_eq!(
            Runtime::run("integration/SI-3/6.sph"),
            Ok(Value::new_number(Rational::from_str("-1/2").unwrap()))
        );
        assert_eq!(
            Runtime::run("integration/SI-3/7.sph"),
            Ok(Value::new_number(Rational::from_sci_string("-1.2e-2").unwrap()))
        );
    }
    #[test]
    fn si_4()
    {
        assert_eq!(
            Runtime::run("integration/SI-4/0.sph"),
            Ok(Value::new_string(format!("Hello world!")))
        );
        assert_eq!(
            Runtime::run("integration/SI-4/1.sph"),
            Ok(Value::new_string(format!("Hello world!")))
        );
        assert_eq!(
            Runtime::run("integration/SI-4/2.sph"),
            Ok(Value::new_string(format!("'")))
        );
        assert_eq!(
            Runtime::run("integration/SI-4/3.sph"),
            Ok(Value::new_string(format!("\"")))
        );
        assert_eq!(
            Runtime::run("integration/SI-4/4.sph"),
            Ok(Value::new_string(format!("\0\t\n\r\"\'\\")))
        );
        assert_eq!(
            Runtime::run("integration/SI-4/5.sph"),
            Ok(Value::new_string(format!("\0\0")))
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