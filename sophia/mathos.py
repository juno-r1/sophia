'''
The Mathos module defines built-in operators.
'''

from aletheia import infer
from arche import element, slice, function_method

def u_add(_, x): # Pain

	return +x

def b_add(_, x, y):

	return x + y

op_add = function_method('+')
op_add.register(u_add,
				'number',
				('number',))
op_add.register(b_add,
				'number',
				('number', 'number'))

def u_sub(_, x):

	return -x

def b_sub(_, x, y):

	return x - y

op_sub = function_method('-')
op_sub.register(u_sub,
				'number',
				('number',))
op_sub.register(b_sub,
				'number',
				('number', 'number'))

def u_rsv(task, x):
	
	task.message('resolve', x)
	return task.calls.recv()

def b_mul(_, x, y):

	return x * y

op_mul = function_method('*')
op_mul.register(u_rsv,
				'*',
				('future',))
op_mul.register(b_mul,
				'number',
				('number', 'number'))

def b_div(_, x, y):

	if y != 0: # Null return on division-by-zero
		return x / y

op_div = function_method('/')
op_div.register(b_div,
				'number',
				('number', 'number'))

def b_exp(_, x, y):

	return x ** y

op_exp = function_method('^')
op_exp.register(b_exp,
				'number',
				('number', 'number'))

def b_mod(_, x, y):

	if y != 0: # Null return on modulo-by-zero
		return x % y

op_mod = function_method('%')
op_mod.register(b_mod,
				'number',
				('number', 'number'))

def b_eql(_, x, y): # Stricter equality because of that dumb fucker bool

	return type(x) is type(y) and x == y

op_eql = function_method('=')
op_eql.register(b_eql,
				'boolean',
				('untyped', 'untyped'))

def b_neq(_, x, y):

	return type(x) is not type(y) or x != y

op_neq = function_method('!=')
op_neq.register(b_neq,
				'boolean',
				('untyped', 'untyped'))

def b_ltn(_, x, y):
	
	return x < y

op_ltn = function_method('<')
op_ltn.register(b_ltn,
				'boolean',
				('number', 'number'))

def n_rcv(task):
	
	value = task.messages.recv()
	return task.bind(task.address, value, infer(value))

def b_gtn(_, x, y):

	return x > y

op_gtn = function_method('>')
op_gtn.register(n_rcv,
				'.',
				())
op_gtn.register(b_gtn,
				'boolean',
				('number', 'number'))

def b_leq(_, x, y):

	return x <= y

op_leq = function_method('<=')
op_leq.register(b_leq,
				'boolean',
				('number', 'number'))

def b_geq(_, x, y):

	return x >= y

op_geq = function_method('>=')
op_geq.register(b_geq,
				'boolean',
				('number', 'number'))

def b_sbs(_, x, y):
	
	return x in y

op_sbs = function_method('in')
op_sbs.register(b_sbs,
				'boolean',
				('untyped', 'string'))
op_sbs.register(b_sbs,
				'boolean',
				('untyped', 'list'))
op_sbs.register(b_sbs,
				'boolean',
				('untyped', 'record'))
op_sbs.register(b_sbs,
				'boolean',
				('untyped', 'slice'))

def u_lnt(_, x):

	return not x

op_lnt = function_method('not')
op_lnt.register(u_lnt,
				'boolean',
				('boolean',))

def b_lnd(_, x, y):

	return x and y

op_lnd = function_method('and')
op_lnd.register(b_lnd,
				'boolean',
				('boolean', 'boolean'))

def b_lor(_, x, y):

	return x or y

op_lor = function_method('or')
op_lor.register(b_lor,
				'boolean',
				('boolean', 'boolean'))

def b_lxr(_, x, y):

	return x != y

op_lxr = function_method('xor')
op_lxr.register(b_lxr,
				'boolean',
				('boolean', 'boolean'))

def b_ins_string(_, x, y):

	return ''.join(i for i in x if i in y) # Order of list dependent on order of operators

def b_ins_list(_, x, y):

	return tuple(i for i in x if i in y)

def b_ins_record(_, x, y):

	return tuple(k for k in x if k in y)

def b_ins_slice(_, x, y):
	
	n, m = x.indices[2], y.indices[2]
	while m != 0: # Euclidean algorithm for greatest common divisor
		n, m = m, n % m
	if n % (y.indices[0] - x.indices[0]) == 0: # Solution for intersection of slices
		step = (x.indices[2] * y.indices[2]) / n # Step of intersection
		ranges = [x.indices[0], x.indices[1], y.indices[0], y.indices[1]].sort()
		lower = ranges[1] - (ranges[1] % step) + step # Gets highest lower bound
		upper = ranges[2] - (ranges[2] % step) # Gets lowest upper bound
		return slice((lower, upper, m))
	else:
		return None

op_ins = function_method('&')
op_ins.register(b_ins_string,
				'string',
				('string', 'string'))
op_ins.register(b_ins_list,
				'list',
				('list', 'list'))
op_ins.register(b_ins_record,
				'list',
				('record', 'record'))
op_ins.register(b_ins_slice,
				'slice',
				('slice', 'slice'))

def b_uni_string(_, x, y):

	return x + y

def b_uni_list(_, x, y):

	return tuple(list(x) + list(y))

def b_uni_record(_, x, y):

	return x | y

def b_uni_slice(_, x, y):

	return tuple((list(x) + list(y)).sort())

op_uni = function_method('|')
op_uni.register(b_uni_string,
				'string',
				('string', 'string'))
op_uni.register(b_uni_list,
				'list',
				('list', 'list'))
op_uni.register(b_uni_record,
				'record',
				('record', 'record'))
op_uni.register(b_uni_slice,
				'list',
				('slice', 'slice'))

def b_slc(_, x, y):

	return element((x, y))

def t_slc(_, x, y, z):
	
	return slice([x, y, z])

op_slc = function_method(':')
op_slc.register(b_slc,
				'untyped',
				('untyped', 'untyped'))
op_slc.register(t_slc,
				'slice',
				('integer', 'integer', 'integer'))

def u_sfe_null(_, x):

	return False

def u_sfe_untyped(_, x):
	
	return True

op_sfe = function_method('?')
op_sfe.register(u_sfe_null,
				'boolean',
				('null',))
op_sfe.register(u_sfe_untyped,
				'boolean',
				('untyped',))

def u_usf(_, x):

	return x if x else None

op_usf = function_method('!')
op_usf.register(u_usf,
				'*',
				('untyped',))

def b_snd(task, x, y):
	
	if y.check:
		task.message('update', y, x)
		return y
	else:
		task.message('send', y, x)
		return y

op_snd = function_method('->')
op_snd.register(b_snd,
				'future',
				('untyped', 'future'))

# Namespace composition

operators = {v.name: v for k, v in globals().items() if k.split('_')[0] == 'op'}