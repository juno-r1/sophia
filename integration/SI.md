# Sophia Integrations

## SI-0

Sophia Integrations, abbreviated as SIs, are internal tickets used to implement the specification of the Sophia interpreter. SIs are numbered in order of creation: this one is SI-0. The ordering is permanent.

SIs are associated with a description of their requirements, an integration test, and the unit tests used for the components associated with the SI. Unit tests may be changed and reordered as is necessary.

## SI-1: Initialisation

Initialise the Sophia runtime.

## SI-2: Return statement

`return`
`return <E>`

Ends execution of the current routine and returns null to the calling routine.
It is possible to return from the main routine.
The returned value may be used by external utilities in future.

## SI-3: Numeric literals

`1`
`+1`
`-1`
`1.2`
`1/2`
`1e2`

Sophia has one numeric data type: arbitrary-precision rationals.
It should be able to parse as constant with the sign and either a solidus or a decimal point and an exponent.

# SI-4: String literals

`"Hello world!"`
`'Hello world!'`
`"'"`
`'"'`

String literals are indicated with single or double quotes.
One can be used inside the other.
Strings are encoded in UTF-8.

The following escape characters are available:
\0  U+0000 (NUL)
\t	U+0009 (HT)
\n	U+000A (LF)
\r	U+000D (CR)
\"	U+0022 (QUOTATION MARK)
\'	U+0027 (APOSTROPHE)
\\	U+005C (REVERSE SOLIDUS)

ASCII characters can be specified with \x and then 2 hex digits:
\x00

Unicode characters can be specified with \u and then up to 6 hex digits in curly brackets:
\u{000000}

# SI-5: Boolean literals

`true`
`false`

Sophia has no concept of truthiness.
Any expression in a boolean context (if statements, while statements) must evaluate to these values.

# SI-6: Assignment

`<N>: <E>`
`<N>: <E>; <N>: <E; ...>`

Assign a value to a name. Referencing the name yields the value.
The name and the bound value persist until the end of scope, or until the name is reassigned.
Multiple assignment requires all expressions to be evaluated from left to right, and then all names to be assigned simultaneously.

# SI-7: Sequence constructors

`[]`
`[<E>]`
`[<E>, <E>, ...]`

`[:]`
`[<E>: <E>]`
`[<E>: <E>, <E>: <E>, ...]`

Sequences are data types that contain data. When the key is unspecified, a list is constructed. When the key is specified, a record is constructed.
The constructor `[]` creates an empty list, equivalent to `new list`.
The constructor `[:]` creates an empty record, equivalent to `new record`.
Constructors cannot be mixed: either all or none of the keys must be specified.

# SI-8: Ranges

`[::]`
`[<E>:<E>:<E>]`

Ranges represent arithmetic sequences between two rationals.
The constructor `[::]` creates an empty range, equivalent to `new range`.
Using a step value of 0 also creates an empty range, since otherwise it would generate an infinite range.
In Sophia, ranges are inclusive-inclusive. This means that both bounds are included in the sequence.
For instance, a range of 0:10:1 generates numbers from 0 to 10.
This approach is preferred because it is useful to reference only those numbers that actually exist within the range.
This helps to minimise confusion since ranges are also used for indexing, so there aren't any unexpected omissions.
The start, the end, and the step must all be specified. This is to prevent incorrect assumptions about implict values.

# SI-9: Typing

`<T>(<E>)`

Sophia is structurally typed.
Types are conceptualised as a set of values for which a set of predicates hold true.
Types with the same predicates are considered to be equal.
Subtypes have the predicates of their supertypes.

Types can be passed a value to perform a type check that returns boolean.

This integration implements Sophia's basic non-capturing types.

any
none
some
number (num)
integer (int)
boolean (bool)
string (str)
range

# SI-10: Type operator

`?<E>`

While values have no nominal type in Sophia, all expressions have a final type.
Using the type operator yields the type of the expression as a first-class value.

# SI-11: Typed assignment

`<T> <N>: <E>`

Typed assignments determine the type of a name.
The assignment performs a type check. If the value does not match the stated type, an error is thrown.
The name is assigned exactly the stated type, and not more or less specific.

# SI-12: Equality operators

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

# SI-13: Boolean operators

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

# SI-14: Arithmetic operators

`+<E>`
`-<E>`
`<E> + <E>`
`<E> - <E>`
`<E> * <E>`
`<E> / <E>`
`<E> ^ <E>`
`<E> % <E>`

The arithmetic operators implement basic arithmetic operations.
Sophia has by default:
- Modulus and addition (+);
- Negation and subtraction (-);
- Multiplication (*);
- Division (/);
- Exponentiation (^);
- Modulo (%);

All of these operations can also be applied to ranges.

Some of these operations are partial: there are some inputs in the input type that do not map to an output (for example, division by 0). In these cases, these operations return null, to indicate the absence of a return value.