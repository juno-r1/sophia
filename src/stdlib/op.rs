use crate::std_mod;

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
	std_fn!
	{
		string add_ss(string x0, string x1)
		{
			format!("{x0}{x1}")
		}
	}
}

std_mod!
{
	div;
	std_fn!
	{
		number div_b(number x0, number x1)
		{
			if x1 == 0 {
				return Value::new_none();
			};
			x0 / x1
		}
	}
	std_fn!
	{
		range div_rn(range x0, number x1)
		{
			if x1 == 0 {
				return Value::new_none();
			};
			x0 / x1
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
	exp: {
		use malachite::Rational;
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
					i += Rational::ONE;
				};
			};
			acc
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
	idx: {
		use malachite::Rational;
		use malachite::num::basic::traits::Zero;
		use utils::coerce::Coerce;

		use crate::datatypes::Range;
	};
	std_fn!
	{
		string idx_si(string x0, number x1)
		{
			let i: usize = if x1 >= 0 {x1.to_usize()} else {x0.len() - x1.to_usize()};
			match x0
			.chars()
			.collect::<Vec<char>>()
			.get(i) {
				Some(c) => c.to_string(),
				None => return Value::new_none()
			}
		}
	}
	std_fn!
	{
		string idx_sr(string x0, range x1)
		{
			let chars = x0
				.chars()
				.collect::<Vec<char>>();
			match x1.clone().try_fold(
				String::new(),
				|mut acc, n| {
					if *n.denominator_ref() != 1 {
						return None;
					}
					let i: usize = if n >= 0 {n.to_usize()} else {x0.len() - n.to_usize()};
					match chars.get(i) {
						Some(c) => {acc.push(c.clone()); Some(acc)},
						None => None
					}
				}
			) {
				Some(x) => x,
				None => return Value::new_none()
			}
		}
	}
	std_fn!
	{
		number idx_ri(range x0, number x1)
		{
			let i: usize = if x1 >= 0 {x1.to_usize()} else {x0.len() - x1.to_usize()};
			match x0.get(i) {
				Some(x) => x,
				None => return Value::new_none()
			}
		}
	}
	std_fn!
	{
		range idx_rr(range x0, range x1)
		{
			match x1.clone().try_fold(
				Vec::new(),
				|mut acc, n| {
					if *n.denominator_ref() != 1 {
						return None;
					}
					let i: usize = if n >= 0 {n.to_usize()} else {x0.len() - n.to_usize()};
					match x0.get(i) {
						Some(c) => {acc.push(c); Some(acc)},
						None => None
					}
				}
			) {
				Some(x) => {
					let start = x.get(0).unwrap_or(&Rational::ZERO).clone();
					let end = x.last().unwrap_or(&Rational::ZERO).clone();
					let step = (&end - &start) / Rational::from(x.len() - 1);
					Range::new(start, end, step)
				},
				None => return Value::new_none()
			}
		}
	}
	// let length = x0.len();
	// if (x1 >= 0 && x1 >= length) || -length < x1 {
	// 	return Ok(Value::new_none());
	// };
	// x0[x1]
}

std_mod!
{
	ins;
	std_fn!
	{
		string ins_ss(string x0, string x1)
		{
			x0.chars().fold(
				String::new(),
				|mut acc, c| {
					if x1.contains(c) && !acc.contains(c) {acc.push(c); acc} else {acc}
				}
			)
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
	mdl: {
		use utils::number::modulo;
	};
	std_fn!
	{
		number mdl_b(number x0, number x1)
		{
			if x1 == 0 {
				return Value::new_none();
			};
			modulo(x0, x1)
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
	sbs;
	std_fn!
	{
		boolean sbs_ss(string x0, string x1)
		{
			x1.contains(&x0)
		}
	}
	std_fn!
	{
		boolean sbs_nr(number x0, range x1)
		{
			x1.contains(&x0)
		}
	}
}

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
	std_fn!
	{
		string sub_ss(string x0, string x1)
		{
			x1.chars().fold(
				x0.clone(),
				|acc, c| acc.replace(c, "")
			)
		}
	}
}

std_mod!
{
	uni;
	std_fn!
	{
		string uni_ss(string x0, string x1)
		{
			format!("{x0}{x1}").chars().fold(
				String::new(),
				|mut acc, c| {
					if !acc.contains(c) {acc.push(c); acc} else {acc}
				}
			)
		}
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
