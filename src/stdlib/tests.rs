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
        // string (string, string)
        task.add_ss(vec![
            Value::test(r#"'abc'"#),
            Value::test(r#"'def'"#)
        ]).assert(r#"'abcdef'"#);
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
            Value::test("-2")
        ]).assert("0.25");
        task.exp_b(vec![
            Value::test("2"),
            Value::test("0")
        ]).assert("1");
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
    fn idx()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // string? (string, integer)
        task.idx_si(vec![
            Value::test(r#"'abc'"#),
            Value::test("0")
        ]).assert(r#"'a'"#);
        task.idx_si(vec![
            Value::test(r#"'abc'"#),
            Value::test("-1")
        ]).assert(r#"'c'"#);
        task.idx_si(vec![
            Value::test(r#"'abc'"#),
            Value::test("3")
        ]).assert("null");
        // string? (string, range)
        task.idx_sr(vec![
            Value::test(r#"'abcde'"#),
            Value::test("[0:4:2]")
        ]).assert(r#"'ace'"#);
        task.idx_sr(vec![
            Value::test(r#"'abcde'"#),
            Value::test("[4:0:-2]")
        ]).assert(r#"'eca'"#);
        task.idx_sr(vec![
            Value::test(r#"'abcde'"#),
            Value::test("[0:4:0.5]")
        ]).assert("null");
        // number? (range, integer)
        task.idx_ri(vec![
            Value::test("[0:4:2]"),
            Value::test("0")
        ]).assert("0");
        task.idx_ri(vec![
            Value::test("[0:4:2]"),
            Value::test("-1")
        ]).assert("4");
        task.idx_ri(vec![
            Value::test("[0:4:2]"),
            Value::test("3")
        ]).assert("null");
        // range? (range, range)
        task.idx_rr(vec![
            Value::test("[0:8:2]"),
            Value::test("[0:4:2]")
        ]).assert("[0:8:4]");
        task.idx_rr(vec![
            Value::test("[0:8:2]"),
            Value::test("[4:0:-2]")
        ]).assert("[8:0:-4]");
        task.idx_rr(vec![
            Value::test("[0:8:2]"),
            Value::test("[0:4:0.5]")
        ]).assert("null");
    }
    #[test]
    fn ins()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // string (string, string)
        task.ins_ss(vec![
            Value::test(r#"'abc'"#),
            Value::test(r#"'cde'"#)
        ]).assert(r#"'c'"#);
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
            Value::test("-5"),
            Value::test("2")
        ]).assert("1");
        task.mdl_b(vec![
            Value::test("5"),
            Value::test("-2")
        ]).assert("1");
        task.mdl_b(vec![
            Value::test("-5"),
            Value::test("-2")
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
    fn sbs()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // boolean (string, string)
        task.sbs_ss(vec![
            Value::test(r#"'a'"#),
            Value::test(r#"'abc'"#)
        ]).assert("true");
        task.sbs_ss(vec![
            Value::test(r#"'ab'"#),
            Value::test(r#"'abc'"#)
        ]).assert("true");
        task.sbs_ss(vec![
            Value::test(r#"'ac'"#),
            Value::test(r#"'abc'"#)
        ]).assert("false");
        task.sbs_ss(vec![
            Value::test(r#"'d'"#),
            Value::test(r#"'abc'"#)
        ]).assert("false");
        // boolean (number, range)
        task.sbs_nr(vec![
            Value::test("1"),
            Value::test("[1:5:2]")
        ]).assert("true");
        task.sbs_nr(vec![
            Value::test("0"),
            Value::test("[1:5:2]")
        ]).assert("false");
        task.sbs_nr(vec![
            Value::test("6"),
            Value::test("[1:5:2]")
        ]).assert("false");
        task.sbs_nr(vec![
            Value::test("2"),
            Value::test("[1:5:2]")
        ]).assert("false");
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
        // string (string, string)
        task.sub_ss(vec![
            Value::test(r#"'abcdef'"#),
            Value::test(r#"'ace'"#)
        ]).assert(r#"'bdf'"#);
    }
    #[test]
    fn uni()
    {
        let mut task = Task::new(vec![], BTreeMap::new());
        // string (string, string)
        task.uni_ss(vec![
            Value::test(r#"'abc'"#),
            Value::test(r#"'cde'"#)
        ]).assert(r#"'abcde'"#);
    }
}
