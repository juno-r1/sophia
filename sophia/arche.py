class slice: # Initialised during execution

	def __init__(self, slice_list):
		
		if slice_list[1] >= 0: # Correction for inclusive range
			slice_list[1] = slice_list[1] + 1
		else:
			slice_list[1] = slice_list[1] - 1
		self.value, self.nodes = range(*slice_list), slice_list # Stores slice and iterator

	def __iter__(self): # Enables loop syntax

		return iter(self.value) # Enables iteration over range without expanding slice

	def execute(self): # Returns expansion of slice

		return [i for i in self.value]

def functions():

	def _input(value):

		return input(value)

	def _print(*value):

		return print(*value)

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

#builtins = tuple(definition(*item) for item in types() + functions() + operators()) # Forbidden tuple comprehension [NOT CLICKBAIT]