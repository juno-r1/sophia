use crate::std_mod;

std_mod!
{
	add: {
		use malachite::num::arithmetic::traits::Abs;
	};
	std_fn!
	{
		Number add_u(Number x0)
		{
			x0.abs()
		}
	}
	std_fn!
	{
		Range add_r(Range x0)
		{
			x0.abs()
		}
	}
	std_fn!
	{
		Number add_b(Number x0, Number x1)
		{
			x0 + x1
		}
	}
	std_fn!
	{
		Range add_rn(Range x0, Number x1)
		{
			x0 + x1
		}
	}
	std_fn!
	{
		String add_ss(String x0, String x1)
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
		Number div_b(Number x0, Number x1)
		{
			if x1 == 0 {
				return Value::new_none();
			};
			x0 / x1
		}
	}
	std_fn!
	{
		Range div_rn(Range x0, Number x1)
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
		Boolean eql_b(Any x0, Any x1)
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
		Number exp_b(Number x0, Number x1)
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
		Boolean gql_b(Number x0, Number x1)
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
		Boolean gtn_b(Number x0, Number x1)
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
		String idx_si(String x0, Number x1)
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
		String idx_sr(String x0, Range x1)
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
		Number idx_ri(Range x0, Number x1)
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
		Range idx_rr(Range x0, Range x1)
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
		String ins_ss(String x0, String x1)
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
		Boolean lnd_b(Boolean x0, Boolean x1)
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
		Boolean lnt_u(Boolean x0)
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
		Boolean lor_b(Boolean x0, Boolean x1)
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
		Boolean lql_b(Number x0, Number x1)
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
		Boolean ltn_b(Number x0, Number x1)
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
		Boolean lxr_b(Boolean x0, Boolean x1)
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
		Number mdl_b(Number x0, Number x1)
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
		Number mul_b(Number x0, Number x1)
		{
			x0 * x1
		}
	}
	std_fn!
	{
		Range mul_rn(Range x0, Number x1)
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
		Boolean nql_b(Any x0, Any x1)
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
		Boolean sbs_ss(String x0, String x1)
		{
			x1.contains(&x0)
		}
	}
	std_fn!
	{
		Boolean sbs_nr(Number x0, Range x1)
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
		type sfe_u(Any x0)
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
		Number sub_u(Number x0)
		{
			-x0
		}
	}
	std_fn!
	{
		Range sub_r(Range x0)
		{
			-x0
		}
	}
	std_fn!
	{
		Number sub_b(Number x0, Number x1)
		{
			x0 - x1
		}
	}
	std_fn!
	{
		Range sub_rn(Range x0, Number x1)
		{
			x0 - x1
		}
	}
	std_fn!
	{
		String sub_ss(String x0, String x1)
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
		String uni_ss(String x0, String x1)
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
