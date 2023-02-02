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

def u_add(_, x):

	return x

def b_add(_, x, y):

	return x + y

def u_sub(_, x):

	return -x

def b_sub(_, x, y):

	return x - y

def b_mul(_, x, y):

	return x * y

def b_div(_, x, y):

	if y != 0: # Null return on division-by-zero
		return real(x) / real(y) # Normalise type

def b_exp(_, x, y):

	return real(real(x) ** real(y)) # Normalise type more forcefully (exponentiation can produce irrational numbers)

def b_mod(_, x, y):

	if y != 0: # Null return on modulo-by-zero
		return real(x) % real(y) # Normalise type

def b_eql(_, x, y):

	return x == y

def b_neq(_, x, y):

	return x != y

def b_ltn(_, x, y):
	
	return x < y

def b_gtn(_, x, y):

	return x > y

def b_leq(_, x, y):

	return x <= y

def b_geq(_, x, y):

	return x >= y

def b_sbs(_, x, y):

	return x in y

def u_lnt(_, x):

	return not x

def b_lnd(_, x, y):

	return x and y

def b_lor(_, x, y):

	return x or y

def b_lxr(_, x, y):

	return x != y

def b_ins(_, x, y):

	if type(x) is type(y): # Only works on operands of the same type
		return [i for i in x if i in y] # Order of list dependent on order of operators

def b_uni(_, x, y):

	if type(x) is type(y):
		if isinstance(x, dict):
			return x | y
		else:
			return x + y

def u_bnt(_, x):

	pass

def b_bnd(_, x, y):

	pass

def b_bor(_, x, y):

	pass

def b_bxr(_, x, y):

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

def f_input(value): # Functions should be wrapped because checking Python functions for type fucking sucks

	return input(value)

def f_print(*value):

	return print(*value)

def f_time():

	return count()

def f_error(value):
	
	return current_process().error(value)

operators = {v[0]: operator(*v) for k, v in globals().items() if k.split('_')[0] == 'op'}
functions = {k.split('_')[1]: v for k, v in globals().items() if k.split('_')[0] == 'f'}

supertypes = {'untyped': ['untyped'], # Suboptimal way to optimise subtype checking
			  'process': ['process', 'untyped'],
			  'routine': ['routine', 'untyped'],
			  'type': ['type', 'routine', 'untyped'],
			  'operator': ['operator', 'routine', 'untyped'],
			  'function': ['function', 'routine', 'untyped'],
			  'value': ['value', 'untyped'],
			  'boolean': ['boolean', 'value', 'untyped'],
			  'number': ['number', 'value', 'untyped'],
			  'integer': ['integer', 'number', 'value', 'untyped'],
			  'real': ['real', 'number', 'value', 'untyped'],
			  'iterable': ['iterable', 'untyped'],
			  'slice' : ['slice', 'iterable', 'untyped'],
			  'sequence': ['sequence', 'iterable', 'untyped'],
			  'string': ['string', 'sequence', 'iterable', 'untyped'],
			  'list': ['list', 'sequence', 'iterable', 'untyped'],
			  'record': ['record', 'sequence', 'iterable', 'untyped']}