# stdlib

This specification describes Sophia's standard library.

## Types

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