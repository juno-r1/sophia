#[cfg(test)]
mod types
// Unit tests for Sophia's standard types.
{
    use crate::datatypes::TypeDef;
    use crate::sophia::Value;

    #[test]
    fn any()
    {
        let test = TypeDef::std_any();
        assert_eq!(test.call(&Value::test("null")), true);
        assert_eq!(test.call(&Value::test("0")), true);
    }
    #[test]
    fn none()
    {
        let test = TypeDef::std_none();
        assert_eq!(test.call(&Value::test("null")), true);
        assert_eq!(test.call(&Value::test("0")), false);
    }
    #[test]
    fn some()
    {
        let test = TypeDef::std_some();
        assert_eq!(test.call(&Value::test("0")), true);
        assert_eq!(test.call(&Value::test("null")), false);
    }
    #[test]
    fn number()
    {
        let test = TypeDef::std_number();
        assert_eq!(test.call(&Value::test("0")), true);
        assert_eq!(test.call(&Value::test("''")), false);
    }
    #[test]
    fn integer()
    {
        let test = TypeDef::std_integer();
        assert_eq!(test.call(&Value::test("0")), true);
        assert_eq!(test.call(&Value::test("0.5")), false);
    }
    #[test]
    fn boolean()
    {
        let test = TypeDef::std_boolean();
        assert_eq!(test.call(&Value::test("true")), true);
        assert_eq!(test.call(&Value::test("1")), false);
    }
    #[test]
    fn string()
    {
        let test = TypeDef::std_string();
        assert_eq!(test.call(&Value::test("''")), true);
        assert_eq!(test.call(&Value::test("0")), false);
    }
    #[test]
    fn range()
    {
        let test = TypeDef::std_range();
        assert_eq!(test.call(&Value::test("[::]")), true);
        assert_eq!(test.call(&Value::test("0")), false);
    }
}

#[cfg(test)]
mod functions
// Unit tests for Sophia's standard functions.
{
    use std::collections::BTreeMap;

    use crate::datatypes::TypeDef;
    use crate::sophia::{Task, Value};

    #[test]
    fn add()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // number (number)
        task.add_u(vec![
            Value::test("-1")
        ]).assert("1");
        // range (range)
        task.add_r(vec![
            Value::test("[5:1:-1]")
        ]).assert("[1:5:1]");
        // number (number, number)
        task.add_b(vec![
            Value::test("1"),
            Value::test("1")
        ]).assert("2");
        // range (range, number)
        task.add_rn(vec![
            Value::test("[1:5:1]"),
            Value::test("1")
        ]).assert("[2:6:1]");
    }
    #[test]
    fn div()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // number? (number, number)
        task.div_b(vec![
            Value::test("2"),
            Value::test("2")
        ]).assert("1");
        task.div_b(vec![
            Value::test("1"),
            Value::test("0")
        ]).assert("null");
        // range? (range, number)
        task.div_rn(vec![
            Value::test("[2:10:2]"),
            Value::test("2")
        ]).assert("[1:5:1]");
        task.div_rn(vec![
            Value::test("[1:5:1]"),
            Value::test("0")
        ]).assert("null");
    }
    #[test]
    fn eql()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (any, any)
        task.eql_b(vec![
            Value::test("0"),
            Value::test("0")
        ]).assert("true");
        task.eql_b(vec![
            Value::test("0"),
            Value::test("1")
        ]).assert("false");
    }
    #[test]
    fn exp()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // number (number, number)
        task.exp_b(vec![
            Value::test("2"),
            Value::test("3")
        ]).assert("8");
        task.exp_b(vec![
            Value::test("2"),
            Value::test("-1")
        ]).assert("0.5");
    }
    #[test]
    fn gql()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (number, number)
        task.gql_b(vec![
            Value::test("1"),
            Value::test("0")
        ]).assert("true");
        task.gql_b(vec![
            Value::test("1"),
            Value::test("1")
        ]).assert("true");
        task.gql_b(vec![
            Value::test("1"),
            Value::test("2")
        ]).assert("false");
    }
    #[test]
    fn gtn()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (number, number)
        task.gtn_b(vec![
            Value::test("1"),
            Value::test("0")
        ]).assert("true");
        task.gtn_b(vec![
            Value::test("1"),
            Value::test("1")
        ]).assert("false");
        task.gtn_b(vec![
            Value::test("1"),
            Value::test("2")
        ]).assert("false");
    }
    #[test]
    fn lnd()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (boolean, boolean)
        task.lnd_b(vec![
            Value::test("false"),
            Value::test("false")
        ]).assert("false");
        task.lnd_b(vec![
            Value::test("false"),
            Value::test("true")
        ]).assert("false");
        task.lnd_b(vec![
            Value::test("true"),
            Value::test("false")
        ]).assert("false");
        task.lnd_b(vec![
            Value::test("true"),
            Value::test("true")
        ]).assert("true");
    }
    #[test]
    fn lnt()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (boolean)
        task.lnt_u(vec![
            Value::test("false")
        ]).assert("true");
        task.lnt_u(vec![
            Value::test("true")
        ]).assert("false");
    }
    #[test]
    fn lor()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (boolean, boolean)
        task.lor_b(vec![
            Value::test("false"),
            Value::test("false")
        ]).assert("false");
        task.lor_b(vec![
            Value::test("false"),
            Value::test("true")
        ]).assert("true");
        task.lor_b(vec![
            Value::test("true"),
            Value::test("false")
        ]).assert("true");
        task.lor_b(vec![
            Value::test("true"),
            Value::test("true")
        ]).assert("true");
    }
    #[test]
    fn lql()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (number, number)
        task.lql_b(vec![
            Value::test("1"),
            Value::test("0")
        ]).assert("false");
        task.lql_b(vec![
            Value::test("1"),
            Value::test("1")
        ]).assert("true");
        task.lql_b(vec![
            Value::test("1"),
            Value::test("2")
        ]).assert("true");
    }
    #[test]
    fn ltn()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (number, number)
        task.ltn_b(vec![
            Value::test("1"),
            Value::test("0")
        ]).assert("false");
        task.ltn_b(vec![
            Value::test("1"),
            Value::test("1")
        ]).assert("false");
        task.ltn_b(vec![
            Value::test("1"),
            Value::test("2")
        ]).assert("true");
    }
    #[test]
    fn lxr()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (boolean, boolean)
        task.lxr_b(vec![
            Value::test("false"),
            Value::test("false")
        ]).assert("false");
        task.lxr_b(vec![
            Value::test("false"),
            Value::test("true")
        ]).assert("true");
        task.lxr_b(vec![
            Value::test("true"),
            Value::test("false")
        ]).assert("true");
        task.lxr_b(vec![
            Value::test("true"),
            Value::test("true")
        ]).assert("false");
    }
    #[test]
    fn mdl()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // number? (number, number)
        task.mdl_b(vec![
            Value::test("5"),
            Value::test("2")
        ]).assert("1");
        task.mdl_b(vec![
            Value::test("1"),
            Value::test("0")
        ]).assert("null");
    }
    #[test]
    fn mul()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // number (number, number)
        task.mul_b(vec![
            Value::test("2"),
            Value::test("2")
        ]).assert("4");
        // range (range, number)
        task.mul_rn(vec![
            Value::test("[1:5:1]"),
            Value::test("2")
        ]).assert("[2:10:2]");
    }
    #[test]
    fn nql()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (any, any)
        task.nql_b(vec![
            Value::test("0"),
            Value::test("0")
        ]).assert("false");
        task.nql_b(vec![
            Value::test("0"),
            Value::test("1")
        ]).assert("true");
    }
    #[test]
    fn sfe()
    {
        // type (any)
        let mut task = Task::new(vec![], BTreeMap::new());
        task.signature = vec![TypeDef::std_none()];
        task.sfe_u(vec![
            Value::test("null"),
        ]).assert_type(TypeDef::std_none());
    }
    #[test]
    fn sub()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // number (number)
        task.sub_u(vec![
            Value::test("1")
        ]).assert("-1");
        // range (range)
        task.sub_r(vec![
            Value::test("[1:5:1]")
        ]).assert("[5:1:-1]");
        // number (number, number)
        task.sub_b(vec![
            Value::test("1"),
            Value::test("1")
        ]).assert("0");
        // range (range, number)
        task.sub_rn(vec![
            Value::test("[1:5:1]"),
            Value::test("1")
        ]).assert("[0:4:1]");
    }
}

// pub fn safe_index(&self, index: Rational) -> Option<Value>
// // Index list without panic.
// {
//     match self {
//         Record{k: None, v, l} => {
//             // Integer indices only!
//             if index.denominator_ref() != &Natural::ONE {
//                 return None;
//             };
//             // Convert index to usize to play nice with Rust.
//             let i: usize = if index >= 0 {
//                 index.to_usize()
//             } else if -(&index) > *l {
//                 *l - index.to_usize()
//             } else {
//                 return None;
//             };
//             // Use normalised index.
//             // Rust is smart enough to know that usize can't be less than 0.
//             if &i < l {
//                 Some(v[i].clone())
//             } else {
//                 None
//             }
//         },
//         Record{..} => None,
//     }
// }
