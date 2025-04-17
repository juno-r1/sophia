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
	lnt;
	std_fn!
	{
		boolean lnt_u(boolean x0)
		{
			!x0
		}
	}
}

std_mod!
{
	lnd;
	std_fn!
	{
		boolean lnd_b(boolean x0, boolean x1)
		{
			x0 & x1
		}
	}
}

std_mod!
{
	lor;
	std_fn!
	{
		boolean lor_b(boolean x0, boolean x1)
		{
			x0 | x1
		}
	}
}

std_mod!
{
	lxr;
	std_fn!
	{
		boolean lxr_b(boolean x0, boolean x1)
		{
			x0 != x1
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
		range add_r(range x0)
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
		range add_rn(range x0, number x1)
		{
			x0 + x1
		}
	}
}

std_mod!
{
	sub;
	std_fn!
	{
		number sub_u(number x0)
		{
			-x0
		}
	}
	std_fn!
	{
		range sub_r(range x0)
		{
			-x0
		}
	}
	std_fn!
	{
		number sub_b(number x0, number x1)
		{
			x0 - x1
		}
	}
	std_fn!
	{
		range sub_rn(range x0, number x1)
		{
			x0 - x1
		}
	}
}

std_mod!
{
	mul;
	std_fn!
	{
		number mul_b(number x0, number x1)
		{
			x0 * x1
		}
	}
	std_fn!
	{
		range mul_rn(range x0, number x1)
		{
			x0 * x1
		}
	}
}

std_mod!
{
	div: {
		use malachite::Rational;
		use malachite::num::basic::traits::Zero;
	};
	std_fn!
	{
		number div_b(number x0, number x1)
		{
			if x1 == Rational::ZERO {
				return Ok(Value::new_none());
			};
			x0 / x1
		}
	}
	std_fn!
	{
		range div_rn(range x0, number x1)
		{
			if x1 == Rational::ZERO {
				return Ok(Value::new_none());
			};
			x0 / x1
		}
	}
}

std_mod!
{
	exp: {
		use malachite::Rational;
		// use malachite::num::arithmetic::traits::Pow;
		use malachite::num::basic::traits::One;
	};
	std_fn!
	{
		number exp_b(number x0, number x1)
		{
			let mut acc = Rational::ONE;
			let mut i = x1;
			if i > 0 {
				while i != 0 {
					acc *= &x0;
					i -= Rational::ONE;
				};
			} else if i < 0 {
				while i != 0 {
					acc /= &x0;
					i -= Rational::ONE;
				};
			};
			acc
		}
	}
	// std_fn!
	// {
	// 	range exp_rn(range x0, number x1)
	// 	{
	// 		x0.pow(x1)
	// 	}
	// }
}

std_mod!
{
	mdl: {
		use malachite::Rational;
		use malachite::num::basic::traits::Zero;
	};
	// std_fn!
	// {
	// 	number mdl_r(range x0)
	// 	{
	// 		x0.rem()
	// 	}
	// }
	std_fn!
	{
		number mdl_b(number x0, number x1)
		// Implementation borrowed from Python's Rational module.
		// Rust doesn't have the modulo operator!
		{
			if x1 == Rational::ZERO {
				return Ok(Value::new_none());
			};
			let (nx, dx) = x0.into_numerator_and_denominator();
			let (ny, dy) = x1.into_numerator_and_denominator();
			let (a, b) = (nx * &dy, ny * &dx);
			Rational::from_naturals(
				((a % &b) + &b) % &b,
				&dx * &dy
			)
		}
	}
}

std_mod!
{
	idx: {
		use malachite::Natural;
		use malachite::num::basic::traits::One;

		use utils::coerce::Coerce;
	};
	std_fn!
	{
		string idx_si(string x0, number x1)
		{
			// Integer indices only!
			if x1.denominator_ref() != &Natural::ONE {
				return Ok(Value::new_none());
			};
			// Convert index to usize to play nice with Rust.
			let i: usize = if x1 >= 0 {
				x1.to_usize()
			} else {
				x0.len() - x1.to_usize()
			};
			// Use normalised index.
			// Rust is smart enough to know that usize can't be less than 0.
			match x0
			.chars()
			.collect::<Vec<char>>()
			.get(i) {
				Some(c) => c.to_string(),
				None => return Ok(Value::new_none())
			}
			// let length = x0.len();
			// if (x1 >= 0 && x1 >= length) || -length < x1 {
			// 	return Ok(Value::new_none());
			// };
			// x0[x1]
		}
	}
}

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
