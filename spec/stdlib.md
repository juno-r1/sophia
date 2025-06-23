# stdlib

This specification describes Sophia's standard library.

## Types

Sophia is structurally typed.
Types are conceptualised as a set of values for which a set of predicates hold true.
Types with the same predicates are considered to be equal.
Subtypes have the predicates of their supertypes.

Types can be passed a value to perform a type check that returns boolean.

**any**
- any

Every value and `null`.

**none**
- any
- none

`null`. This type is the return type of partial functions when the input values do not map to an output value.

**some**
- any
- some

Every value. Total functions must map all input values to an output value.

**number** *num*
- any
- some
- number

The set of rationals. Implemented with arbitrary precision.

**integer** *int*
- any
- some
- number
- integer

The set of integers.

**boolean** *bool*
- any
- some
- boolean

The booleans, `true` and `false`. Sophia does not permit "truthy" and "falsy" values in boolean contexts.

**string** *str*
- any
- some
- string

The set of UTF-8 strings.

**range**
- any
- some
- range

Bounded arithmetic sequences between 2 rationals.

**list(T)**
- any
- some
- list(T)

A list of element type T. Lists are 0-indexed in Sophia.

**record(K, V)**
- any
- some
- record(K, V)

A record of key type K and value type V. Records maintain insertion order.

## Functions

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