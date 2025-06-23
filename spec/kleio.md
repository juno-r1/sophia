# kleio

This specification describes the JSON data format for internal function type information.

## Naming conventions

Methods are named with the canonical name of their associated function, and then a string of letters describing their parameter types. The types are as follows:

a	any
_	none
_	some
n	number
i	integer
b	boolean
s	string
r	range
l	list
m	record (map)
f	function
t	type

For example, the name of the record type constructor is `record_tt`.

Operators are named with a three-letter abbreviation of the operation that they implement. For example, the name of the string index method is `idx_si`.