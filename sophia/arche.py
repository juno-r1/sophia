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

class element(tuple): pass # Stupid hack to make record construction work

class proxy: # Base proxy object

	def __init__(self, process):
		
		self.name = process.name
		self.type = process.type
		self.supertype = process.supertype # Types only
		self.pid = process.pid # Unset on initialisation
		self.link = process.link # For linked modules
		self.messages = None # Pipe to send messages
		self.end = None # Pipe for return value
		self.bound = False # Determines whether process is bound

	def send(self, value): # Proxy method to send to process

		return self.messages.send(value)

	def get(self): # Proxy method to get return value from process

		return self.end.recv()

class operator: # Base operator object

	def __init__(self, symbol, unary, binary, *types):

		self.symbol = symbol # Operator symbol
		self.unary = unary # Unary function
		self.binary = binary # Binary function
		self.types = types # Tuple of return type and input types

	def __call__(self, routine, *args):

		x = routine.cast(args[0], self.types[1])
		if x is None:
			return None
		if len(args) > 1:
			y = routine.cast(args[1], self.types[2])
			if y is None:
				return None
			value = self.binary(x, y)
		else:
			value = self.unary(x)
		return routine.cast(value, self.types[0])

class routine: # Base function object

	def __init__(self, value):

		self.value = value

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

def u_bnt(x):

	pass

def b_bnd(x, y):

	pass

def b_bor(x, y):

	pass

def b_bxr(x, y):

	pass

op_add = ('+',							# Symbol
		  u_add,						# Unary operator
		  b_add,						# Binary operator
		  'number', 'number', 'number')	# Return type and input types

op_sub = ('-',
		  u_sub,
		  b_sub,
		  'number', 'number', 'number')

op_mul = ('*',
		  None,
		  b_mul,
		  'number', 'number', 'number')

op_div = ('/',
		  None,
		  b_div,
		  'number', 'number', 'number')

op_exp = ('^',
		 None,
		 b_exp,
		 'number', 'number', 'number')

op_mod = ('%',
		  None,
		  b_mod,
		  'number', 'number', 'number')

op_eql = ('=',
		  None,
		  b_eql,
		  'boolean', 'untyped', 'untyped')

op_neq = ('!=',
		  None,
		  b_neq,
		  'boolean', 'untyped', 'untyped')

op_ltn = ('<',
		  None,
		  b_ltn,
		  'boolean', 'number', 'number')

op_gtn = ('>',
		  None,
		  b_gtn,
		  'boolean', 'number', 'number')

op_leq = ('<=',
		  None,
		  b_leq,
		  'boolean', 'number', 'number')

op_geq = ('>=',
		  None,
		  b_geq,
		  'boolean', 'number', 'number')

op_sbs = ('in',
		  None,
		  b_sbs,
		  'boolean', 'untyped', 'sequence')

op_lnt = ('not',
		  u_lnt,
		  None,
		  'boolean', 'boolean', 'boolean')

op_lnd = ('and',
		  None,
		  b_lnd,
		  'boolean', 'boolean', 'boolean')

op_lor = ('or',
		  None,
		  b_lor,
		  'boolean', 'boolean', 'boolean')

op_lxr = ('xor',
		  None,
		  b_lxr,
		  'boolean', 'boolean', 'boolean')

op_ins = ('&',
		  None,
		  b_ins,
		  'sequence', 'sequence', 'sequence')

op_uni = ('|',
		  None,
		  b_uni,
		  'sequence', 'sequence', 'sequence')

op_bnt = ('~',
		  u_bnt,
		  None,
		  'untyped', 'untyped', 'untyped')

op_bnd = ('&&',
		  None,
		  b_bnd,
		  'untyped', 'untyped', 'untyped')

op_bor = ('||',
		  None,
		  b_bor,
		  'untyped', 'untyped', 'untyped')

op_bxr = ('^^',
		  None,
		  b_bxr,
		  'untyped', 'untyped', 'untyped')

def f_input(value):

	return input(value)

def f_print(*value):

	return print(*value)

def f_error(value):
		
	return current_process().error(value)