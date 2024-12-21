#[macro_export]
macro_rules! error
// Defines a runtime error.
{
	(CALL, $value:expr) => {
		Err(
            format!(
                "Value {:?} is not callable",
                $value,
            )
        )
	};
    (DISP, $name:expr, $signature:expr) => {
        Err(
            format!(
                "Failed dispatch: {} has no signature {:?}",
                $name,
                $signature,
            )
        )
	};
    (FILE, $name:expr) => {
        Err(
            format!(
                "Invalid file: {}",
                $name,
            )
        )
	};
    (FIND, $name:expr) => {
        Err(
            format!(
                "Undefined name: {}",
                $name,
            )
        )
	};
    (IMPL) => {
        Err(
            format!(
                "Not implemented",
            )
        )
	};
    (TYPE, $name:expr, $value:expr) => {
        Err(
            format!(
                "Invalid value for type {}: {:?}",
                $name,
                $value,
            )
        )
	};
    (UPRN) => {
        Err(
            format!(
                "Unmatched parentheses",
            )
        )
	};
    (UQTE) => {
        Err(
            format!(
                "Unmatched quotes",
            )
        )
	};
    (USER, $message:expr) => {
        Err(
            format!(
                "{}",
                $message,
            )
        )
	};
}