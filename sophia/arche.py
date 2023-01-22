from multiprocessing import current_process
from fractions import Fraction as real
from time import perf_counter_ns as count

class element(tuple): pass # Stupid hack to make record construction work

class iterable: # Loop index

	def __init__(self, value):

		self.value = iter(value)

	def __next__(self):

		return next(self.value)

class slice: # Slice object

	def __init__(self, sequence):
		
		if sequence[1] >= 0: # Correction for inclusive range
			sequence[1] = sequence[1] + 1
		else:
			sequence[1] = sequence[1] - 1
		self.value, self.nodes = range(*sequence), sequence # Stores slice and iterator

	def __iter__(self): # Enables loop syntax

		return iter(self.value) # Enables iteration over range without expanding slice

class operator: # Base operator object

	def __init__(self, symbol, unary, binary, *types):

		self.symbol = symbol # Operator symbol
		self.unary = unary # Unary function
		self.binary = binary # Binary function
		self.types = types # Tuple of return type and input types

	def __call__(self, routine, *args):
		
		x = routine.cast(args[0], routine.find(self.types[1]))
		if x is None:
			return None
		if len(args) > 1:
			y = routine.cast(args[1], routine.find(self.types[2]))
			if y is None:
				return None
			value = self.binary(x, y)
		else:
			value = self.unary(x)
		return routine.cast(value, routine.find(self.types[0]))

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
		return real(x) / real(y) # Normalise type

def b_exp(x, y):

	return real(real(x) ** real(y)) # Normalise type more forcefully (exponentiation can produce irrational numbers)

def b_mod(x, y):

	if y != 0: # Null return on modulo-by-zero
		return real(x) % real(y) # Normalise type

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

f_input = input # First-class functions exist and can be used

f_print = print

f_time = count

def f_error(value):
	
	return current_process().error(value)

operators = {v[0]: operator(*v) for k, v in globals().items() if k.split('_')[0] == 'op'}
functions = {k.split('_')[1]: v for k, v in globals().items() if k.split('_')[0] == 'f'}