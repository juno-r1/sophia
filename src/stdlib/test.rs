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