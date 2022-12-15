from fractions import Fraction as real

class definition: # Created by assignment

	def __init__(self, name, value, type_name, reserved = False):

		self.name = name
		self.value = value
		self.type = type_name
		self.reserved = reserved

	def __str__(self): # Overrides print() representation

		name = type(self.value).__name__
		if name == 'process':
			return ' '.join((self.name, self.type, self.value.name, str([item.value for item in self.value.namespace])))
		elif name == 'function_definition':
			return ' '.join((self.name, self.type, str([item.type + ' ' + item.value for item in self.value.value[1:]])))
		else:
			return ' '.join((self.name, self.type, repr(self.value)))

def types(): # Yeah, there's some name mangling going on here

	def _untyped(value):

		return value

	def _integer(value):

		if (not isinstance(value, bool)) and (isinstance(value, int) or isinstance(value, (float, real)) and int(value) == value):
			return int(value)

	def _float(value):

		if (not isinstance(value, bool)) and (isinstance(value, float) or isinstance(value, (int, real)) and float(value) == value):
			return float(value)

	def _real(value):

		if (not isinstance(value, bool)) and (isinstance(value, real) or isinstance(value, (int, float)) and real(str(value)) == value):
			return real(str(value)) # String conversion necessary because Python is extremely weird about precision

	def _boolean(value):
		
		if value is True or value is False:
			return value

	def _string(value):

		if isinstance(value, str):
			return value

	def _list(value):

		if isinstance(value, list):
			return value

	def _record(value):

		if isinstance(value, dict):
			return value

	return [(name[1:], value, 'type', True) for name, value in locals().items()]

def functions():

	def _input(value):

		return input(value)

	def _print(*value):

		return print(*value, flush = True)

	def _error(value):
		
		raise Exception(value)
		
	return [(name[1:], value, 'untyped', True) for name, value in locals().items()]

def operators():
	
	add = ('+',                 # Symbol
		   lambda x: x,			# Unary operator
		   lambda x, y: x + y)  # Binary operator
	sub = ('-',
		   lambda x: -x,
		   lambda x, y: x - y)
	mul = ('*',
		   None,
		   lambda x, y: x * y)
	div = ('/',
		   None,
		   lambda x, y: x / y if y != 0 else None) # Null return on division-by-zero
	exp = ('^',
		   None,
		   lambda x, y: x ** y)
	mod = ('%',
		   None,
		   lambda x, y: x % y if y != 0 else None) # Null return on modulo-by-zero
	ins = ('&',
		   None,
		   lambda x, y: type(x)([i for i in x if i in y])) # Order of list dependent on order of operators
	uni = ('|',
		   None,
		   lambda x, y: x + y)
	bnt = ('~',
		   lambda x: ~x,
		   None)
	bnd = ('&&',
		   None,
		   lambda x, y: x & y)
	bor = ('||',
		   None,
		   lambda x, y: x | y)
	bxr = ('^^',
		   None,
		   lambda x, y: x ^ y)
	eql = ('=',
		   None,
		   lambda x, y: x == y)
	ltn = ('<',
		   None,
		   lambda x, y: x < y)
	gtn = ('>',
		   None,
		   lambda x, y: x > y)
	neq = ('!=',
		   None,
		   lambda x, y: x != y)
	leq = ('<=',
		   None,
		   lambda x, y: x <= y)
	geq = ('>=',
		   None,
		   lambda x, y: x >= y)
	sbs = ('in',
		   None,
		   lambda x, y: x in y)
	lnt = ('not',
		   lambda x: not x,
		   None)
	lnd = ('and',
		   None,
		   lambda x, y: x and y)
	lor = ('or',
		   None,
		   lambda x, y: x or y)
	lxr = ('xor',
		   None,
		   lambda x, y: x is not y)

	return [(value[0], (value[1], value[2]), 'operator', True) for value in locals().values()]

builtins = tuple(definition(*item) for item in types() + functions() + operators()) # Forbidden tuple comprehension [NOT CLICKBAIT]