# Sophia Integrations

## SI-0

Sophia Integrations, abbreviated as SIs, are internal tickets used to implement the specification of the Sophia interpreter. SIs are numbered in order of creation: this one is SI-0. The ordering is permanent.

SIs are associated with a description of their requirements, an integration test, and the unit tests used for the components associated with the SI. Unit tests may be changed and reordered as is necessary.

## SI-1

Initialise the Sophia runtime.

## SI-2

Return statement.

`return`
`return <E>`

Ends execution of the current routine and returns null to the calling routine.
It is possible to return from the global routine.
The returned value may be used by external utilities in future.

## SI-3

Numeric literals.

`1`
`+1`
`-1`
`1.2`
`1/2`
`1e2`

Sophia has one numeric data type: arbitrary-precision rationals.
It should be able to parse as constant with the sign and either a fraction sign or a decimal point and an exponent.

# SI-4

String literals.

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

ASCII characters can be specified with \x and then 2 digits:
\x00

Unicode charaacters can be specified with \u and then up to 6 digits in curly brackets:
\u{000000}