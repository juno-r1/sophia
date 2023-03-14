'''
The Mathos module defines built-in operators.
'''

from arche import element, slice, method

def u_add(_, x): # Pain

	return x

def b_add(_, x, y):

	return x + y

op_add = method('+')
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

op_sub = method('-')
op_sub.register(u_sub,
				'number',
				('number',))
op_sub.register(b_sub,
				'number',
				('number', 'number'))

def b_mul(_, x, y):

	return x * y

op_mul = method('*')
op_mul.register(b_mul,
				'number',
				('number', 'number'))

def b_div(_, x, y):

	if y != 0: # Null return on division-by-zero
		return x / y

op_div = method('/')
op_div.register(b_div,
				'number',
				('number', 'number'))

def b_exp(_, x, y):

	return x ** y

op_exp = method('^')
op_exp.register(b_exp,
				'number',
				('number', 'number'))

def b_mod(_, x, y):

	if y != 0: # Null return on modulo-by-zero
		return x % y

op_mod = method('%')
op_mod.register(b_mod,
				'number',
				('number', 'number'))

def b_eql(_, x, y): # Stricter equality because of that dumb fucker bool

	return type(x) is type(y) and x == y

op_eql = method('=')
op_eql.register(b_eql,
				'boolean',
				('untyped', 'untyped'))

def b_neq(_, x, y):

	return type(x) is not type(y) or x != y

op_neq = method('!=')
op_neq.register(b_neq,
				'boolean',
				('untyped', 'untyped'))

def b_ltn(_, x, y):
	
	return x < y

op_ltn = method('<')
op_ltn.register(b_ltn,
				'boolean',
				('number', 'number'))

def b_gtn(_, x, y):

	return x > y

op_gtn = method('>')
op_gtn.register(b_gtn,
				'boolean',
				('number', 'number'))

def b_leq(_, x, y):

	return x <= y

op_leq = method('<=')
op_leq.register(b_leq,
				'boolean',
				('number', 'number'))

def b_geq(_, x, y):

	return x >= y

op_geq = method('>=')
op_geq.register(b_geq,
				'boolean',
				('number', 'number'))

def b_sbs(_, x, y):
	
	return x in y

op_sbs = method('in')
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

op_lnt = method('not')
op_lnt.register(u_lnt,
				'boolean',
				('boolean',))

def b_lnd(_, x, y):

	return x and y

op_lnd = method('and')
op_lnd.register(b_lnd,
				'boolean',
				('boolean', 'boolean'))

def b_lor(_, x, y):

	return x or y

op_lor = method('or')
op_lor.register(b_lor,
				'boolean',
				('boolean', 'boolean'))

def b_lxr(_, x, y):

	return x != y

op_lxr = method('xor')
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

op_ins = method('&')
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

op_uni = method('|')
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

op_slc = method(':')
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

op_sfe = method('?')
op_sfe.register(u_sfe_null,
				'boolean',
				('null',))
op_sfe.register(u_sfe_untyped,
				'boolean',
				('untyped',))

def u_usf(_, x):

	return x if x else None

op_usf = method('!')
op_usf.register(u_usf,
				'*',
				('untyped',))

# Namespace composition

operators = {v.name: v for k, v in globals().items() if k.split('_')[0] == 'op'}