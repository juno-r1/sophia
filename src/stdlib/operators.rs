pub mod add
{
	use macros::std_fn;
	use malachite::num::arithmetic::traits::Abs;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		number u_add(number x0)
		{
			x0.abs()
		}
	}
	std_fn!
	{
		number b_add(number x0, number x1)
		{
			x0 + x1
		}
	}
}

pub mod sub
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		number u_sub(number x0)
		{
			-x0
		}
	}
	std_fn!
	{
		number b_sub(number x0, number x1)
		{
			x0 - x1
		}
	}
}

pub mod mul
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		number b_mul(number x0, number x1)
		{
			x0 * x1
		}
	}
}

pub mod div
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		number b_div(number x0, number x1)
		{
			x0 / x1
		}
	}
}

pub mod exp
{
	use macros::std_fn;
	use malachite::Rational;
	use malachite::num::basic::traits::One;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		number b_exp(number x0, number x1)
		{
			let mut acc = Rational::ONE;
			let mut i = x1.clone();
			if i > 0 {
				while i != 0 {
					acc *= x0.clone();
					i -= Rational::ONE;
				};
			} else if i < 0 {
				while i != 0 {
					acc /= x0.clone();
					i -= Rational::ONE;
				};
			};
			acc
		}
	}
}

pub mod mdl
{
	use malachite::Rational;
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	// Implementation borrowed from Python's Rational module.
	std_fn!
	{
		number b_mdl(number x0, number x1)
		{
			let (nx, dx) = x0.into_numerator_and_denominator();
			let (ny, dy) = x1.into_numerator_and_denominator();
			let a = nx * dy.clone();
			let b = ny * dx.clone();
			Rational::from_naturals(
				((a % b.clone()) + b.clone()) % b.clone(), // Rust doesn't have the modulo operator!
				dx.clone() * dy.clone()
			)
		}
	}
}

pub mod eql
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_eql(any x0, any x1)
		{
			x0 == x1
		}
	}
}

pub mod nql
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_nql(any x0, any x1)
		{
			x0 != x1
		}
	}
}

pub mod ltn
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_ltn(number x0, number x1)
		{
			x0 < x1
		}
	}
}

pub mod gtn
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_gtn(number x0, number x1)
		{
			x0 > x1
		}
	}
}

pub mod lql
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_lql(number x0, number x1)
		{
			x0 <= x1
		}
	}
}

pub mod gql
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_gql(number x0, number x1)
		{
			x0 >= x1
		}
	}
}

pub mod sbs
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_sbs_string(string x0, string x1)
		{
			x1.contains(x0.as_str())
		}
	}
}

pub mod lnt
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_lnt(boolean x0)
		{
			!x0
		}
	}
}

pub mod lnd
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_lnd(boolean x0, boolean x1)
		{
			x0 & x1
		}
	}
}

pub mod lor
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_lor(boolean x0, boolean x1)
		{
			x0 | x1
		}
	}
}

pub mod lxr
{
	use macros::std_fn;

	use crate::sophia::arche::Value;
	use crate::sophia::runtime::Task;

	std_fn!
	{
		boolean b_lxr(boolean x0, boolean x1)
		{
			x0 != x1
		}
	}
}