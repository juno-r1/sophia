from multiprocessing import current_process

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

class proxy: # Base proxy object

	def __init__(self, value):
		
		self.name = value.name
		self.type = value.type
		self.supertype = value.supertype
		self.pid = value.pid
		self.messages = None # Pipe to send messages
		self.end = None # Pipe for return value
		self.bound = False # Determines whether process is bound

class operator: # Base operator object

	def __init__(self, symbol, unary, binary, *types):

		self.symbol = symbol # Operator symbol
		self.unary = unary # Unary function
		self.binary = binary # Binary function
		self.types = types # Tuple of return type and input types

def u_add(x):

	return x

def b_add(x, y):

	return x + y

def u_sub(x):

	return -x

def b_sub(x, y):

	return x - y

def b_mul(x, y):

	return x * y

def b_div(x, y):

	if y != 0: # Null return on division-by-zero
		return x / y

def b_exp(x, y):

	return x ** y

def b_mod(x, y):

	if y != 0: # Null return on modulo-by-zero
		return x % y

def b_eql(x, y):

	return x == y

def b_neq(x, y):

	return x != y

def b_ltn(x, y):

	return x < y

def b_gtn(x, y):

	return x > y

def b_leq(x, y):

	return x <= y

def b_geq(x, y):

	return x >= y

def b_sbs(x, y):

	return x in y

def u_lnt(x):

	return not x

def b_lnd(x, y):

	return x and y

def b_lor(x, y):

	return x or y

def b_lxr(x, y):

	return x != y

def b_ins(x, y):

	if type(x) is type(y): # Only works on operands of the same type
		return [i for i in x if i in y] # Order of list dependent on order of operators

def b_uni(x, y):

	if type(x) is type(y):
		if isinstance(x, dict):
			return x | y
		else:
			return x + y

op_add = operator('+',							# Symbol
				  u_add,						# Unary operator
				  b_add,						# Binary operator
				  'number', 'number', 'number')	# Return type and input types

op_sub = operator('-',
				  u_sub,
				  b_sub,
				  'number', 'number', 'number')

op_mul = operator('*',
				  None,
				  b_mul,
				  'number', 'number', 'number')

op_div = operator('/',
				  None,
				  b_div,
				  'number', 'number', 'number')

op_exp = operator('^',
				  None,
				  b_exp,
				  'number', 'number', 'number')

op_mod = operator('%',
				  None,
				  b_mod,
				  'number', 'number', 'number')

op_eql = operator('=',
				  None,
				  b_eql,
				  'boolean', 'untyped', 'untyped')

op_neq = operator('!=',
				  None,
				  b_neq,
				  'boolean', 'untyped', 'untyped')

op_ltn = operator('<',
				  None,
				  b_ltn,
				  'boolean', 'number', 'number')

op_gtn = operator('>',
				  None,
				  b_gtn,
				  'boolean', 'number', 'number')

op_leq = operator('<=',
				  None,
				  b_leq,
				  'boolean', 'number', 'number')

op_geq = operator('>=',
				  None,
				  b_geq,
				  'boolean', 'number', 'number')

op_sbs = operator('in',
				  None,
				  b_sbs,
				  'boolean', 'untyped', 'sequence')

op_lnt = operator('not',
				  u_lnt,
				  None,
				  'boolean', 'boolean', 'boolean')

op_lnd = operator('and',
				  None,
				  b_lnd,
				  'boolean', 'boolean', 'boolean')

op_lor = operator('or',
				  None,
				  b_lor,
				  'boolean', 'boolean', 'boolean')

op_lxr = operator('xor',
				  None,
				  b_lxr,
				  'boolean', 'boolean', 'boolean')

op_ins = operator('&',
				  None,
				  b_ins,
				  'sequence', 'sequence', 'sequence')

op_uni = operator('|',
				  None,
				  b_uni,
				  'sequence', 'sequence', 'sequence')

op_bnt = operator('~', # Byte operators currently unimplemented
				  None,
				  None,
				  'untyped', 'untyped', 'untyped')

op_bnd = operator('&&',
				  None,
				  None,
				  'untyped', 'untyped', 'untyped')

op_bor = operator('||',
				  None,
				  None,
				  'untyped', 'untyped', 'untyped')

op_bxr = operator('^^',
				  None,
				  None,
				  'untyped', 'untyped', 'untyped')

def f_input(value):

	return input(value)

def f_print(*value):

	return print(*value)

def f_error(value):
		
	return current_process().error(value)