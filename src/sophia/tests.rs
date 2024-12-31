#[cfg(test)]
mod integration
{
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