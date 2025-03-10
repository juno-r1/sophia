use crate::std_mod;

std_mod!
{
	sfe;
	std_fn!
	{
		type sfe_u(any x0)
		{
			self.signature[0].clone()
		}
	}
}

std_mod!
{
	eql;
	std_fn!
	{
		boolean eql_b(any x0, any x1)
		{
			x0 == x1
		}
	}
}

std_mod!
{
	nql;
	std_fn!
	{
		boolean nql_b(any x0, any x1)
		{
			x0 != x1
		}
	}
}

std_mod!
{
	ltn;
	std_fn!
	{
		boolean ltn_b(number x0, number x1)
		{
			x0 < x1
		}
	}
}

std_mod!
{
	gtn;
	std_fn!
	{
		boolean gtn_b(number x0, number x1)
		{
			x0 > x1
		}
	}
}

std_mod!
{
	lql;
	std_fn!
	{
		boolean lql_b(number x0, number x1)
		{
			x0 <= x1
		}
	}
}

std_mod!
{
	gql;
	std_fn!
	{
		boolean gql_b(number x0, number x1)
		{
			x0 >= x1
		}
	}
}

std_mod!
{
	add: {
		use malachite::num::arithmetic::traits::Abs;
	};
	std_fn!
	{
		number add_u(number x0)
		{
			x0.abs()
		}
	}
	std_fn!
	{
		number add_b(number x0, number x1)
		{
			x0 + x1
		}
	}
	std_fn!
	{
		range add_r(range x0)
		{
			x0.abs()
		}
	}
	std_fn!
	{
		range add_rn(range x0, number x1)
		{
			x0 + x1
		}
	}
}

// std_mod!
// {
// 	sub;
// 	std_fn!
// 	{
// 		number u_sub(number x0)
// 		{
// 			-x0
// 		}
// 	}
// 	std_fn!
// 	{
// 		number b_sub(number x0, number x1)
// 		{
// 			x0 - x1
// 		}
// 	}
// 	std_fn!
// 	{
// 		range range_u_sub(range x0)
// 		{
// 			-x0
// 		}
// 	}
// 	std_fn!
// 	{
// 		range range_b_sub(range x0, number x1)
// 		{
// 			x0 - x1
// 		}
// 	}
// }

// std_mod!
// {
// 	mul;
// 	std_fn!
// 	{
// 		number b_mul(number x0, number x1)
// 		{
// 			x0 * x1
// 		}
// 	}
// 	std_fn!
// 	{
// 		range range_b_mul(range x0, number x1)
// 		{
// 			x0 * x1
// 		}
// 	}
// }

// std_mod!
// {
// 	div;
// 	std_fn!
// 	{
// 		number b_div(number x0, number x1)
// 		{
// 			x0 / x1
// 		}
// 	}
// 	std_fn!
// 	{
// 		range range_b_div(range x0, number x1)
// 		{
// 			x0 / x1
// 		}
// 	}
// }

// std_mod!
// {
// 	exp: {
// 		use malachite::Rational;
// 		use malachite::num::basic::traits::One;
// 	};
// 	std_fn!
// 	{
// 		number b_exp(number x0, number x1)
// 		{
// 			let mut acc = Rational::ONE;
// 			let mut i = x1;
// 			if i > 0 {
// 				while i != 0 {
// 					acc *= &x0;
// 					i -= Rational::ONE;
// 				};
// 			} else if i < 0 {
// 				while i != 0 {
// 					acc /= &x0;
// 					i -= Rational::ONE;
// 				};
// 			};
// 			acc
// 		}
// 	}
// }

// std_mod!
// {
// 	mdl: {
// 		use malachite::Rational;
// 	};
// 	std_fn!
// 	{
// 		number b_mdl(number x0, number x1)
// 		// Implementation borrowed from Python's Rational module.
// 		{
// 			let (nx, dx) = x0.into_numerator_and_denominator();
// 			let (ny, dy) = x1.into_numerator_and_denominator();
// 			let (a, b) = (nx * &dy, ny * &dx);
// 			Rational::from_naturals(
// 				((a % &b) + &b) % &b, // Rust doesn't have the modulo operator!
// 				&dx * &dy
// 			)
// 		}
// 	}
// }

// std_mod!
// {
// 	sbs;
// 	std_fn!
// 	{
// 		boolean b_sbs_string(string x0, string x1)
// 		{
// 			x1.contains(&x0)
// 		}
// 	}
// 	std_fn!
// 	{
// 		boolean b_sbs_range(number x0, range x1)
// 		{
// 			x1.contains(&x0)
// 		}
// 	}
// }

// std_mod!
// {
// 	lnt;
// 	std_fn!
// 	{
// 		boolean u_lnt(boolean x0)
// 		{
// 			!x0
// 		}
// 	}
// }

// std_mod!
// {
// 	lnd;
// 	std_fn!
// 	{
// 		boolean b_lnd(boolean x0, boolean x1)
// 		{
// 			x0 & x1
// 		}
// 	}
// }

// std_mod!
// {
// 	lor;
// 	std_fn!
// 	{
// 		boolean b_lor(boolean x0, boolean x1)
// 		{
// 			x0 | x1
// 		}
// 	}
// }

// std_mod!
// {
// 	lxr;
// 	std_fn!
// 	{
// 		boolean b_lxr(boolean x0, boolean x1)
// 		{
// 			x0 != x1
// 		}
// 	}
// }