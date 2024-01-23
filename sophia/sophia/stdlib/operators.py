'''
Built-in operators.
'''

from ..datatypes import aletheia
from ..datatypes.aletheia import funcdef, typedef

def u_add(_, x): return +x

def b_add(_, x, y): return x + y

std_add = funcdef(
	u_add,
	b_add
)

def u_sub(_, x): return -x

def b_sub(_, x, y): return x - y

std_sub = funcdef(
	u_sub,
	b_sub
)

def u_rsv(task, x):
	
	task.message('resolve', x)
	task.properties = typedef(x.check)
	return task.calls.recv()

def b_mul(_, x, y):	return x * y

std_mul = funcdef(
	u_rsv,
	b_mul
)

def b_div(_, x, y): return x / y if y != 0 else None

std_div = funcdef(
	b_div
)

def b_exp(_, x, y):	return x ** y

std_exp = funcdef(
	b_exp
)

def b_mod(_, x, y): return x % y if y != 0 else None

std_mod = funcdef(
	b_mod
)

def b_eql(_, x, y): return x == y

std_eql = funcdef(
	b_eql
)

def b_neq(_, x, y): return x != y

std_neq = funcdef(
	b_neq
)

def b_ltn(_, x, y):	return x < y

std_ltn = funcdef(
	b_ltn
)

def n_rcv(task):
	
	return task.messages.recv()

def b_gtn(_, x, y):	return x > y

std_gtn = funcdef(
	n_rcv,
	b_gtn
)

def b_leq(_, x, y):	return x <= y

std_leq = funcdef(
	b_leq
)

def b_geq(_, x, y):	return x >= y

std_geq = funcdef(
	b_geq
)

def b_sbs_string(_, x, y): return x in y

def b_sbs_list(_, x, y): return x in y

def b_sbs_record(_, x, y): return x in y

def b_sbs_slice(_, x, y): return x in y

std_sbs = funcdef(
	b_sbs_string,
	b_sbs_list,
	b_sbs_record,
	b_sbs_slice
)

def u_lnt(_, x): return not x

std_lnt = funcdef(
	u_lnt
)

def b_lnd(_, x, y): return x and y

std_lnd = funcdef(
	b_lnd
)

def b_lor(_, x, y): return x or y

std_lor = funcdef(
	b_lor
)

def b_lxr(_, x, y): return x != y

std_lxr = funcdef(
	b_lxr
)

def b_ins_string(_, x, y): return ''.join(i for i in x if i in y) # Order of list dependent on order of operators

def b_ins_list(_, x, y): return tuple(i for i in x if i in y)

def b_ins_record(_, x, y): return tuple(k for k in x if k in y)

def b_ins_slice(_, x, y): return x & y

def b_ins_type(_, x, y): return x & y

std_ins = funcdef(
	b_ins_string,
	b_ins_list,
	b_ins_record,
	b_ins_slice,
	b_ins_type
)

def b_uni_string(_, x, y): return x + y

def b_uni_list(_, x, y): return tuple(list(x) + list(y))

def b_uni_record(_, x, y): return x | y

def b_uni_slice(_, x, y): return x | y

def b_uni_type(_, x, y): return x | y

std_uni = funcdef(
	b_uni_string,
	b_uni_list,
	b_uni_record,
	b_uni_slice,
	b_uni_type
)

def b_idx_string_integer(task, sequence, index):
	
	length = len(sequence) # Sophia's integer type is abstract, Python's isn't
	return sequence[int(index)] if -length <= index < length else task.handler.error('INDX', index)

def b_idx_string_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return ''.join(sequence[int(n)] for n in iter(index)) # Constructs slice of string using range
	else:
		return task.handler.error('INDX', index)

def b_idx_list_integer(task, sequence, index):
	
	length = len(sequence)
	return sequence[int(index)] if -length <= index < length else task.handler.error('INDX', index)

def b_idx_list_slice(task, sequence, index):
	
	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return tuple(sequence[int(n)] for n in iter(index))
	else:
		return task.handler.error('INDX', index)

def b_idx_record_any(task, sequence, index):
	
	return sequence[index] if index in sequence else task.handler.error('INDX', index)

def b_idx_record_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		items = tuple(sequence.items())
		return dict(items[int(n)] for n in iter(index))
	else:
		return task.handler.error('INDX', index)

def b_idx_slice_integer(task, sequence, index):

	length = len(sequence)
	return sequence[int(index)] if -length <= index < length else task.handler.error('INDX', index)

def b_idx_slice_slice(task, sequence, index):
	
	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return tuple(sequence[int(n)] for n in iter(index))
	else:
		return task.handler.error('INDX', index)

def b_idx_type_type(task, definition, element):

	return typedef(definition, aletheia.cls_element(element))

def b_idx_type_integer(task, definition, length):

	return typedef(definition, aletheia.cls_length(length))

std_idx = funcdef(
	b_idx_string_integer,
	b_idx_string_slice,
	b_idx_list_integer,
	b_idx_list_slice,
	b_idx_record_any,
	b_idx_record_slice,
	b_idx_slice_integer,
	b_idx_slice_slice,
	b_idx_type_type,
	b_idx_type_integer
)

def u_sfe_none(_, x): return False

def u_sfe_some(_, x): return True

def b_sfe_some_some(task, x, y):
	
	task.properties = typedef(task.signature[0])
	return x

def b_sfe_none_some(task, x, y):
	
	task.properties = typedef(task.signature[1])
	return y

std_sfe = funcdef(
	u_sfe_none,
	u_sfe_some,
	b_sfe_some_some,
	b_sfe_none_some
)

def u_usf(task, x): return x or None

std_usf = funcdef(
	u_usf
)

def b_snd(task, x, y):
	
	task.message('send', y, x)
	return y

std_snd = funcdef(
	b_snd
)

def u_new(task, x):
	
	if x.prototype is None:
		return None
	else:
		task.properties = typedef(x)
		return x.prototype

std_new = funcdef(
	u_new
)

def b_cmp(task, x, y):

	return y + x

std_cmp = funcdef(
	b_cmp
)