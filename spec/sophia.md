# Sophia Integrations

## SI-0

Sophia Integrations, abbreviated as SIs, are internal tickets used to implement the specification of the Sophia interpreter. SIs are associated with a description of their requirements, an integration test, and the unit tests used for the components associated with the SI. Unit tests may be changed and reordered as is necessary.

## SI-1: Initialisation

Initialise the Sophia runtime.
The runtime returns the value from the main file, or null if the main file is empty. Null indicates the absence of a value.

A file consists of a group of expressions. Groups return the value of the last expression.

## SI-2: Boolean literals

`true`
`false`

Sophia has no concept of truthiness.
Any expression in a boolean context (if, while) must evaluate to these values.

## SI-3: Numeric literals

`1`
`+1`
`-1`
`1.2`
`1/2`
`1e2`

Sophia has one numeric data type: arbitrary-precision rationals.
It should be able to parse as constant with the sign and either a solidus or a decimal point and an exponent.

## SI-4: String literals

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

## SI-5: Lists

`[]`
`[<E>]`
`[<E>, <E>, ...]`

Lists are sequences whose keys are unspecified. The constructor `[]` creates an empty list, equivalent to `new list`.

## SI-6: Records

`[:]`
`[<E>: <E>]`
`[<E>: <E>, <E>: <E>, ...]`

Records are sequences whose keys are specified. The constructor `[:]` creates an empty record, equivalent to `new record`.

## SI-7: Ranges

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

## SI-?: Assignment

`<N>: <E>`
`<N>: <E>; <N>: <E>`
`<N>: <E[]>; <N>: <E[]>`

`<T> <N>: <E>`
`<T> <N>: <E>; <T> <N>: <E>`
`<T> <N>: <E[]>; <T> <N>: <E[]]`

Assign a value to a name. Referencing the name yields the value.
The name and the bound value persist until the end of scope, or until the name is reassigned.
Multiple assignment requires all expressions to be evaluated from left to right, and then all names to be assigned simultaneously.

Typed assignments determine the type of a name.
The assignment performs a type check. If the value does not match the stated type, an error is thrown.
The name is assigned exactly the stated type, and not more or less specific.

## SI-?: Return statement

`return`
`return <E>`
`return <E[]>`

Ends execution of the current routine and returns to the calling routine.
It is possible to return from the main routine.
The returned value may be used by external utilities in future.
