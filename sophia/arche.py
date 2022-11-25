def init_types(): # Yeah, there's some name mangling going on here

	def _untyped(value):

		return value

	def _integer(value):

		if (not isinstance(value, bool)) and (isinstance(value, int) or isinstance(value, float) and int(value) == value):
			return int(value)

	def _float(value):

		if (not isinstance(value, bool)) and (isinstance(value, float) or isinstance(value, int) and float(value) == value):
			return float(value)

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

def init_functions():

	def _input(value):

		return input(value)

	def _print(*value):

		return print(*value)

	def _error(value):
		
		raise Exception(value)
		
	return [(name[1:], value, 'untyped', True) for name, value in locals().items()]

def init_operators():
	
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
		   lambda x, y: [i for i in x if i in y])
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