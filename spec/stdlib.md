# stdlib

This specification describes Sophia's standard library.

## Types

Sophia is structurally typed.
Types are conceptualised as a set of values for which a set of predicates hold true.
Types with the same predicates are considered to be equal.
Subtypes have the predicates of their supertypes.

Types can be passed a value to perform a type check that returns boolean.

### Non-capturing types

These types do not capture any values.
They are available in the standard namespace as-is.

**Any**
- Any

The universal supertype (top type).

true

**Number** *num*
- Any
- Number

The set of rationals. Implemented with arbitrary precision.

`Number` => true
_ => false

**Integer** *int*
- Any
- Number
- Integer

The set of integers.

`Number` where x % 1 = 0 => true
_ => false

**String** *str*
- Any
- String

The set of UTF-8 strings.

`String` => true
_ => false

**Range**
- Any
- Range

Bounded arithmetic sequences between 2 rationals.

`Range` => true
_ => false

**Type**
- Any
- Type

Types.
Types are composed of a set of predicates that are true for a set of values.

`Type` => true
_ => false

### Capturing types

These types capture values.
They are available in the standard namespace via type constructors.

**List(T)**
- Any
- List(T)

A list of element type T.
Lists are 0-indexed in Sophia.

`List` where T(n) for n in x => true
_ => false

**Record(K, V)**
- Any
- Record(K, V)

A record of key type K and value type V. Records maintain insertion order.

`Record` where K(n) and V(m) for n, m in x => true
_ => false

**Function**
- Any
- Function

Functions.

`Function` => true
_ => false

### Enum types

These types represent enums.
A value matches an enum type if it matches any of the variants of the type.

**Boolean** *bool*
- Any
- Boolean

The booleans, `true` and `false`.
The boolean type is a special-case enum type that is not interchangeable with other enum types.
Sophia does not permit "truthy" and "falsy" values in boolean contexts.

true | false => true
_ => false

**Option(T)**
- Any
- Option(T)

Enum representing the presence or absence of a value.

Some(T) | None => true
_ => false

**Result(T, E)**
- Any
- Result(T, E)

Enum representing the success or failure of an operation.

Ok(T) | Error(E) => true
_ => false

``

## SI-9: Type operator

`?<E>`

While values have no nominal type in Sophia, all expressions have a final type.
Using the type operator yields the type of the expression as a first-class value.

## SI-10: Equality operators

`<E> = <E>`
`<E> != <E>`
`<E> < <E>`
`<E> > <E>`
`<E> <= <E>`
`<E> >= <E>`

The equality and comparison operators compare two values and return boolean.
Sophia has by default:
- Equality;
- Inequality;
- Less than;
- Greater than;
- Less than or equal to;
- Greater than or equal to.

Equality requires values to be the same data type. There is no loose equality in Sophia.
Overloading these operators does not change their internal implementation.

## SI-11: Boolean operators

`not <E>`
`<E> and <E>`
`<E> or <E>`
`<E> xor <E>`

The boolean operators implement basic logical connectives.
Sophia has by default:
- Negation (NOT);
- Conjunction (AND);
- Disjunction (OR);
- Non-equivalence (XOR).

Logical XOR is equivalent to inequality. It is included here to indicate a semantic distinction.

## SI-12: Numeric operators

`+<E>`
`-<E>`
`<E> + <E>`
`<E> - <E>`
`<E> * <E>`
`<E> / <E>`
`<E> ^ <E>`
`<E> % <E>`

The numeric operators implement basic arithmetic operations on numbers.
Sophia has by default:
- Modulus and addition (+);
- Negation and subtraction (-);
- Multiplication (*);
- Division (/);
- Exponentiation (^);
- Modulo (%).

Some of these operations are partial: there are some inputs in the input type that do not map to an output (for example, division by 0). In these cases, these operations return null, to indicate the absence of a return value.

## SI-13: Range operators

`+<E>`
`-<E>`
`<E> + <E>`
`<E> - <E>`
`<E> * <E>`
`<E> / <E>`

`<E>[<E>]`
`<E> in <E>`
`<E> | <E>`
`<E> & <E>`

The range operators implement basic arithmetic operations on ranges.
Sophia has by default:
- Modulus and addition (+);
- Negation and subtraction (-);
- Multiplication (*);
- Division (/).

Where a range is represented as a linear sequence mx + c:
- Modulus reverses the range if m is negative.
- Negation reverses the range.
- Addition and subtraction add and subtract from the sequence.
- Multiplication and division multiply and divide the sequence.

Ranges also implement sequence operations:
- Index ([]);
- Membership (in);
- Union (|);
- Intersection (&).

## SI-14: String operators

`<E>[<E>]`
`<E> in <E>`
`<E> + <E>`
`<E> - <E>`
`<E> | <E>`
`<E> & <E>`

The string operators implement basic string operations.
Sophia has by default:
- Index ([]);
- Membership (in);
- Concatenation (+);
- Difference (-);
- Union (|);
- Intersection (&).