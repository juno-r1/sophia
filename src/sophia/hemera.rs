use crate::datatypes::types::TypeDef;

use super::arche::Value;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Error {
    CALL(Value),
    DISP(Vec<TypeDef>),
    FILE(String),
    FIND(String),
    IMPL,
    SNTX(String),
    TYPE(String, Value),
    USER(String),
}

pub type Partial<T> = Result<T, Error>;

#[macro_export]
macro_rules! error
// Defines a runtime error.
{
    // "Value {:?} is not callable"
	(CALL, $value:expr) => {
		panic!("{:?}", crate::sophia::hemera::Error::CALL($value.clone()))
	};
    // "Failed dispatch: {} has no signature {:?}"
    (DISP, $signature:expr) => {
        panic!("{:?}", crate::sophia::hemera::Error::DISP($signature.clone()))
	};
    // "Invalid file: {}"
    (FILE, $name:expr) => {
        panic!("{:?}", crate::sophia::hemera::Error::FILE($name.into()))
	};
    // "Undefined name: {}"
    (FIND, $name:expr) => {
        panic!("{:?}", crate::sophia::hemera::Error::FIND($name.into()))
	};
    // "Not implemented"
    (IMPL) => {
        panic!("{:?}", crate::sophia::hemera::Error::IMPL)
	};
    // "Invalid value for type {}: {:?}"
    (TYPE, $name:expr, $value:expr) => {
        panic!("{:?}", crate::sophia::hemera::Error::TYPE($name.into(), $value.clone()))
	};
    // Syntax error
    (SNTX, $message:expr) => {
        panic!("{:?}", crate::sophia::hemera::Error::SNTX($message.into()))
    };
    // User error
    (USER, $message:expr) => {
        panic!("{:?}", crate::sophia::hemera::Error::USER($message.into()))
    };
}