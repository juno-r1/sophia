'''
The Arche module defines the standard library of Sophia.
'''
from aletheia import descriptor, infer, subtype
import aletheia
from iris import reference
from kadmos import instruction, module, translator
from mathos import real, slice, element
from math import copysign

import json
with open('kleio.json') as kleio:
	metadata = json.load(kleio)
del kleio # Python inexplicably does not do this automatically

class method:
	"""
	Implements a multimethod.
	Multimethods enable multiple dispatch on functions. Functions dispatch for
	the arity and types of their arguments. The precedence for dispatch is
	left-to-right, then most to least specific type.
	"""
	def __init__(self, name):

		self.name = name
		self.methods = {}
		self.finals = {}
		self.arity = {}

	def retrieve(self, routine): # Retrieves metadata from Kleio

		data = metadata[self.name][routine.__name__]
		signature = tuple(descriptor(**i, prepare = True) for i in data['signature']) # Tuples are hashable
		self.methods[signature] = routine
		self.finals[signature] = descriptor(**data['final'])
		self.arity[signature] = data['arity']

	def register(self, definition, final, signature): # Registers user-defined definition
		
		self.methods[signature] = definition # Function
		self.finals[signature] = final # Return type
		self.arity[signature] = len(signature) # Pre-evaluated length of signature

class type_method(method):

	def __init__(self, name, supertypes, prototype):

		super().__init__(name)
		self.supertypes = [name] + supertypes
		self.prototype = prototype
		self.specificity = len(supertypes) + 1

class event_method(method): pass
class function_method(method): pass

class type_definition:
	"""Definition for a user-defined type."""
	def __init__(self, instructions, name, known):

		self.instructions = instructions
		self.name = name # String name of type
		self.type = known # Descriptor of supertype

	def __call__(self, task, value):
		
		task.caller = task.state()
		task.final = descriptor(self.name)
		task.values[self.name], task.types[self.name] = value, self.type
		task.reserved = tuple(task.values)
		task.instructions = self.instructions
		task.path = 1
		task.properties.type = '!'

class event_definition:
	"""Definition for a user-defined event."""
	def __init__(self, instructions, params, types):

		self.instructions = instructions
		self.name, self.params, self.message = params[0], params[1:-1], params[-1]
		self.type, self.types, self.check = types[0], types[1:-1], types[-1]

	def __call__(self, task, *args):

		if '.bind' in task.op.label:
			task.message('future', self, args, task.values[self.name])
			task.properties.type = 'future'
			return task.calls.recv()
		else:
			task.caller = task.state()
			task.final = self.type
			task.values = task.values | dict(zip(self.params, args))
			task.types = task.types | dict(zip(self.params, self.types))
			task.reserved = tuple(task.values)
			task.instructions = self.instructions
			task.path = 1
			task.properties.type = '!'

class function_definition:
	"""Definition for a user-defined function."""
	def __init__(self, instructions, params, types):

		self.instructions = instructions
		self.name, self.params = params[0], params[1:]
		self.type, self.types = types[0], types[1:]

	def __call__(self, task, *args):

		if '.bind' in task.op.label:
			task.message('future', self, args, task.values[self.name])
			task.properties.type = 'future'
			return task.calls.recv()
		else:
			task.caller = task.state()
			task.final = self.type
			task.values = task.values | dict(zip(self.params, args))
			task.types = task.types | dict(zip(self.params, self.types))
			task.reserved = tuple(task.values)
			task.instructions = self.instructions
			task.path = 1
			task.properties.type = '!'

"""
Built-in types.
"""

class sophia_null: # Null type

	name = 'null'
	types = type(None)

	def __new__(cls, task, value): return

cls_null = type_method('null', [], None)
cls_null.retrieve(sophia_null)
cls_null.retrieve(subtype)

class sophia_untyped: # Non-abstract base class

	name = 'untyped'
	types = object
	
	def __new__(cls, task, value): # Type check disguised as an object constructor
		
		if isinstance(value, cls.types):
			return value
		else:
			task.properties.type = 'null'
			return task.error('CAST', cls.name, str(value))

	@classmethod
	def __null__(cls, value): return

	@classmethod
	def __type__(cls, value): return

	@classmethod
	def __event__(cls, value): return

	@classmethod
	def __function__(cls, value): return

	@classmethod
	def __boolean__(cls, value): return

	@classmethod
	def __number__(cls, value): return

	@classmethod
	def __string__(cls, value): return

	@classmethod
	def __list__(cls, value): return

	@classmethod
	def __record__(cls, value): return

	@classmethod
	def __slice__(cls, value): return

	@classmethod
	def __future__(cls, value): return

cls_untyped = type_method('untyped', [], None)
cls_untyped.retrieve(sophia_untyped)
cls_untyped.retrieve(subtype)

class sophia_type(sophia_untyped): # Type type
	
	name = 'type'
	types = type_method

cls_type = type_method('type', ['untyped'], None)
cls_type.retrieve(sophia_type)
cls_type.retrieve(subtype)

class sophia_event(sophia_untyped): # Event type

	name = 'event'
	types = event_method

cls_event = type_method('event', ['untyped'], None)
cls_event.retrieve(sophia_event)
cls_event.retrieve(subtype)

class sophia_function(sophia_untyped): # Function type

	name = 'function'
	types = function_method

cls_function = type_method('function', ['untyped'], None)
cls_function.retrieve(sophia_function)
cls_function.retrieve(subtype)

class sophia_boolean(sophia_untyped): # Boolean type

	name = 'boolean'
	types = bool

	@classmethod
	def __boolean__(cls, value): return value

	@classmethod
	def __number__(cls, value): return value != 0

	@classmethod
	def __string__(cls, value): return value != ''

	@classmethod
	def __list__(cls, value): return value != []

	@classmethod
	def __record__(cls, value): return value != {}

	@classmethod
	def __slice__(cls, value): return len(value) != 0

cls_boolean = type_method('boolean', ['untyped'], False)
cls_boolean.retrieve(sophia_boolean)
cls_boolean.retrieve(subtype)

class sophia_number(sophia_untyped): # Abstract number type

	name = 'number'
	types = real

	@classmethod
	def __boolean__(cls, value): return real(int(value))

	@classmethod
	def __number__(cls, value): return value

	@classmethod
	def __string__(cls, value): return real(value)

	@classmethod
	def __future__(cls, value): return real(value.pid)

cls_number = type_method('number', ['untyped'], real(0))
cls_number.retrieve(sophia_number)
cls_number.retrieve(subtype)

class sophia_integer(sophia_number): # Integer type

	name = 'integer'
	types = real

	def __new__(cls, task, value):
		
		try: # Faster than isinstance(), I think
			return value if value % 1 == 0 else task.error('CAST', cls.name, str(value))
		except TypeError:
			task.properties.type = 'null'
			return task.error('CAST', cls.name, str(value))

cls_integer = type_method('integer', ['number', 'untyped'], real(0))
cls_integer.retrieve(sophia_integer)
cls_integer.retrieve(subtype)

class sophia_string(sophia_untyped): # String type

	name = 'string'
	types = str

	@classmethod
	def __null__(cls, value): return 'null'

	@classmethod
	def __type__(cls, value): return value.name

	@classmethod
	def __event__(cls, value): return value.name

	@classmethod
	def __function__(cls, value): return value.name

	@classmethod
	def __boolean__(cls, value): return 'true' if value else 'false'

	@classmethod
	def __number__(cls, value): return str(value)

	@classmethod
	def __string__(cls, value): return value

	@classmethod
	def __list__(cls, value): return '[' + ', '.join([cast_type_untyped(cls, i) for i in value]) + ']'

	@classmethod
	def __record__(cls, value): return '[' + ', '.join([cast_type_untyped(cls, k) + ': ' + cast_type_untyped(cls, v) for k, v in value.items()]) + ']'

	@classmethod
	def __slice__(cls, value): return '{0}:{1}:{2}'.format(value.start, value.stop, value.step)

	@classmethod
	def __future__(cls, value): return value.name

cls_string = type_method('string', ['untyped'], '')
cls_string.retrieve(sophia_string)
cls_string.retrieve(subtype)

class sophia_list(sophia_untyped): # List type

	name = 'list'
	types = tuple

	@classmethod
	def __string__(cls, value): return tuple(i for i in value)

	@classmethod
	def __list__(cls, value): return value

	@classmethod
	def __record__(cls, value): return tuple(value.items())

	@classmethod
	def __slice__(cls, value): return tuple(value)

cls_list = type_method('list', ['untyped'], [])
cls_list.retrieve(sophia_list)
cls_list.retrieve(subtype)

class sophia_record(sophia_untyped): # Record type

	name = 'record'
	types = dict

cls_record = type_method('record', ['untyped'], {})
cls_record.retrieve(sophia_record)
cls_record.retrieve(subtype)

class sophia_slice(sophia_untyped): # Slice type

	name = 'slice'
	types = slice

cls_slice = type_method('slice', ['untyped'], slice((real(0), real(0), real(1))))
cls_slice.retrieve(sophia_slice)
cls_slice.retrieve(subtype)

class sophia_future(sophia_untyped): # Process type
	
	name = 'future'
	types = reference

cls_future = type_method('future', ['untyped'], None)
cls_future.retrieve(sophia_future)
cls_future.retrieve(subtype)

"""
Built-in operators.
"""

def u_add(_, x): return +x

def b_add(_, x, y): return x + y

arche_add = function_method('+')
arche_add.retrieve(u_add)
arche_add.retrieve(b_add)

def u_sub(_, x): return -x

def b_sub(_, x, y): return x - y

arche_sub = function_method('-')
arche_sub.retrieve(u_sub)
arche_sub.retrieve(b_sub)

def u_rsv(task, x):
	
	task.message('resolve', x)
	task.properties = x.check
	return task.calls.recv()

def b_mul(_, x, y):	return x * y

arche_mul = function_method('*')
arche_mul.retrieve(u_rsv)
arche_mul.retrieve(b_mul)

def b_div(_, x, y): return x / y if y != 0 else None

arche_div = function_method('/')
arche_div.retrieve(b_div)

def b_exp(_, x, y):	return x ** y

arche_exp = function_method('^')
arche_exp.retrieve(b_exp)

def b_mod(_, x, y): return x % y if y != 0 else None

arche_mod = function_method('%')
arche_mod.retrieve(b_mod)

def b_eql(_, x, y): return x == y

arche_eql = function_method('=')
arche_eql.retrieve(b_eql)

def b_neq(_, x, y): return x != y

arche_neq = function_method('!=')
arche_neq.retrieve(b_neq)

def b_ltn(_, x, y):	return x < y

arche_ltn = function_method('<')
arche_ltn.retrieve(b_ltn)

def n_rcv(task):
	
	return task.messages.recv()

def b_gtn(_, x, y):	return x > y

arche_gtn = function_method('>')
arche_gtn.retrieve(n_rcv)
arche_gtn.retrieve(b_gtn)

def b_leq(_, x, y):	return x <= y

arche_leq = function_method('<=')
arche_leq.retrieve(b_leq)

def b_geq(_, x, y):	return x >= y

arche_geq = function_method('>=')
arche_geq.retrieve(b_geq)

def b_sbs_string(_, x, y): return x in y

def b_sbs_list(_, x, y): return x in y

def b_sbs_record(_, x, y): return x in y

def b_sbs_slice(_, x, y): return x in y

arche_sbs = function_method('in')
arche_sbs.retrieve(b_sbs_string)
arche_sbs.retrieve(b_sbs_list)
arche_sbs.retrieve(b_sbs_record)
arche_sbs.retrieve(b_sbs_slice)

def u_lnt(_, x): return not x

arche_lnt = function_method('not')
arche_lnt.retrieve(u_lnt)

def b_lnd(_, x, y): return x and y

arche_lnd = function_method('and')
arche_lnd.retrieve(b_lnd)

def b_lor(_, x, y): return x or y

arche_lor = function_method('or')
arche_lor.retrieve(b_lor)

def b_lxr(_, x, y): return x != y

arche_lxr = function_method('xor')
arche_lxr.retrieve(b_lxr)

def b_ins_string(_, x, y): return ''.join(i for i in x if i in y) # Order of list dependent on order of operators

def b_ins_list(_, x, y): return tuple(i for i in x if i in y)

def b_ins_record(_, x, y): return tuple(k for k in x if k in y)

def b_ins_slice(_, x, y):
	
	n, m = x.step, y.step
	while m != 0: # Euclidean algorithm for greatest common divisor
		n, m = m, n % m
	if n % (y.start - x.start) == 0: # Solution for intersection of slices
		step = (x.step * y.step) / n # Step of intersection
		ranges = [x.start, x.end, y.start, y.end].sort()
		lower = ranges[1] - (ranges[1] % step) + step # Gets highest lower bound
		upper = ranges[2] - (ranges[2] % step) # Gets lowest upper bound
		return slice((lower, upper, m))

def b_ins_type(task, x, y):
	
	name, supername = '<{0}&{1}>'.format(x.name, y.name), [i for i in x.supertypes if i in y.supertypes][0] # Use closest mutual supertype
	supertype, index = task.values[supername], x.supertypes.index(supername)
	routine = type_method(name, x.supertypes[index:], x.prototype)
	lhs = [instruction(x.name, '0', (name,)), 
		   instruction('?', '0', ('0',)),
		   instruction('.constraint', '0', ('0',))]
	rhs = [instruction(y.name, '0', (name,)),
		   instruction('?', '0', ('0',)),
		   instruction('.constraint', '0', ('0',))]
	check = lhs + rhs
	start, end = [instruction('START', '', label = [name])], [instruction('.return', '0', (name,)), instruction('END', '')]
	routine.register(type_definition(start + rhs + end, name, descriptor(supername)), name, (descriptor(x.name),))
	routine.register(type_definition(start + lhs + end, name, descriptor(supername)), name, (descriptor(y.name),))
	for key, value in supertype.methods.items(): # Rewrite methods with own type name
		if isinstance(value, type_definition):
			definition = [instruction.rewrite(i, supername, name) for i in value.instructions]
			definition[-2:-2] = check # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), descriptor(name), key)
		else: # Built-in definition
			routine.register(type_definition(start + check + end, name, key[0]), descriptor(name), key)
	return routine

arche_ins = function_method('&')
arche_ins.retrieve(b_ins_string)
arche_ins.retrieve(b_ins_list)
arche_ins.retrieve(b_ins_record)
arche_ins.retrieve(b_ins_slice)
arche_ins.retrieve(b_ins_type)

def b_uni_string(_, x, y): return x + y

def b_uni_list(_, x, y): return tuple(list(x) + list(y))

def b_uni_record(_, x, y): return x | y

def b_uni_slice(_, x, y): return tuple((list(x) + list(y)).sort())

def b_uni_type(task, x, y):

	name, supername = '<{0}|{1}>'.format(x.name, y.name), [i for i in x.supertypes if i in y.supertypes][0] # Use closest mutual supertype
	supertype, index = task.values[supername], x.supertypes.index(supername)
	routine = type_method(name, x.supertypes[index:], x.prototype)
	check = [instruction(x.name, '0', (name,)), 
			 instruction('?', '1', ('0',)),
			 instruction(y.name, '0', (name,)),
			 instruction('?', '0', ('0',)),
			 instruction('or', '0', ('0', '1')),
			 instruction('.constraint', '0', ('0',))]
	start, end = [instruction('START', '', label = [name])], [instruction('.return', '0', (name,)), instruction('END', '')]
	routine.register(type_definition(start + end, name, descriptor(supername)), descriptor(name), (descriptor(x.name),))
	routine.register(type_definition(start + end, name, descriptor(supername)), descriptor(name), (descriptor(y.name),))
	for key, value in supertype.methods.items(): # Rewrite methods with own type name
		if isinstance(value, type_definition): # Built-in supertype
			definition = [instruction.rewrite(i, supername, name) for i in value.instructions]
			definition[-2:-2] = check # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), descriptor(name), key)
		else:
			routine.register(type_definition(start + check + end, name, key[0]), descriptor(name), key)
	return routine

arche_uni = function_method('|')
arche_uni.retrieve(b_uni_string)
arche_uni.retrieve(b_uni_list)
arche_uni.retrieve(b_uni_record)
arche_uni.retrieve(b_uni_slice)
arche_uni.retrieve(b_uni_type)

def b_slc(_, x, y): return element((x, y))

def t_slc(_, x, y, z): return slice((x, y, z))

arche_slc = function_method(':')
arche_slc.retrieve(b_slc)
arche_slc.retrieve(t_slc)

def u_sfe_null(_, x): return False

def u_sfe_untyped(_, x): return True

def b_sfe_untyped_untyped(task, x, y):
	
	task.properties = task.signature[0]
	return x

def b_sfe_null_untyped(task, x, y):
	
	task.properties = task.signature[1]
	return y

arche_sfe = function_method('?')
arche_sfe.retrieve(u_sfe_null)
arche_sfe.retrieve(u_sfe_untyped)
arche_sfe.retrieve(b_sfe_untyped_untyped)
arche_sfe.retrieve(b_sfe_null_untyped)

def u_usf(task, x): return x or None

arche_usf = function_method('!')
arche_usf.retrieve(u_usf)

def b_snd(task, x, y):
	
	task.message('send', y, x)
	return y

arche_snd = function_method('->')
arche_snd.retrieve(b_snd)

def u_new(task, x):
	
	if x.prototype is None:
		return task.error('PROT', x.name)
	else:
		signature = infer(x.prototype)
		task.properties.type = x.name
		task.properties.member = signature.member
		task.properties.length = signature.length
		return x.prototype

arche_new = function_method('new')
arche_new.retrieve(u_new)

"""
Internal functions. The names of these functions are prefixed with "." to make
them inaccessible to the user.
"""

def alias_type(task, routine): # Type alias

	new = type_method(task.op.register, routine.supertypes[1:], routine.prototype)
	for key, value in list(routine.methods.items())[1:]: # Rewrite methods with own type name
		new.register(type_definition([instruction.rewrite(i, routine.name, new.name) for i in value.instructions]
									 if isinstance(value, type_definition)
									 else value, new.name, key[0]), descriptor(new.name), key)
	return new

arche_alias = function_method('.alias')
arche_alias.retrieve(alias_type)

def assert_null(task, value): # Null assertion
	
	return task.branch(1, True, True)

def assert_untyped(task, value): # Non-null assertion
	
	return value

arche_assert = function_method('.assert')
arche_assert.retrieve(assert_null)
arche_assert.retrieve(assert_untyped)

def bind_untyped(task, value):
	
	name, signature, offset = task.op.label[0], task.signature[0], 0
	while task.instructions[task.path + offset].register != name:
		offset = offset + 1
	task.instructions[task.path + offset].name = task.check(name, default = value).type if name in task.values else signature.type
	if name in task.reserved:
		return task.error('BIND', name)
	else:
		task.properties = signature
		return value

def bind_untyped_type(task, value, type_routine):
	
	name, signature = task.op.label[0], task.signature[0]
	if name in task.reserved:
		return task.error('BIND', name)
	else:
		task.properties = signature
		return value

arche_bind = function_method('.bind')
arche_bind.retrieve(bind_untyped)
arche_bind.retrieve(bind_untyped_type)

def branch_null(task): # Unconditional branch
	
	return task.branch(1, False, True)

def branch_boolean(task, condition): # Conditional branch

	if not condition:
		return task.branch(1, True, True)

arche_branch = function_method('.branch')
arche_branch.retrieve(branch_null)
arche_branch.retrieve(branch_boolean)

def break_untyped(task, value): # Loop break

	task.values[task.op.register], task.values[task.op.args[0]] = None, None # Sanitise registers
	while True:
		op, task.path = task.instructions[task.path], task.path + 1
		if op.name == '.loop':
			return

arche_break = function_method('.break')
arche_break.retrieve(break_untyped)

def concatenate_untyped(task, value):
	
	task.properties.member = task.signature[0].type
	return [value]

def concatenate_untyped_untyped(task, sequence, value):

	sequence_type, member_type = task.signature[0], task.signature[1]
	task.properties.length = sequence_type.length + 1
	if sequence_type.member == member_type.type:
		task.properties.member = sequence_type.member
	else:
		sequence_type, member_type = task.values[sequence_type.member], task.values[member_type.type]
		task.properties.member = [i for i in sequence_type.supertypes if i in member_type.supertypes][0]
	return sequence + [value]

arche_concatenate = function_method('.concatenate')
arche_concatenate.retrieve(concatenate_untyped)
arche_concatenate.retrieve(concatenate_untyped_untyped)

def constraint_boolean(task, constraint):
	
	name = task.instructions[0].label[0]
	if not constraint:
		value = task.values[name]
		task.restore(task.caller)
		task.error('CAST', name, str(value))
	elif task.op.label and task.op.label[0] != name: # Update type of checked value for subsequent constraints
		task.types[name].type = task.op.label[0]

arche_constraint = function_method('.constraint')
arche_constraint.retrieve(constraint_boolean)

def event_null(task):

	name = task.op.register
	types, params = [task.describe(descriptor.read(i)) for i in task.op.label[0::2]], task.op.label[1::2]
	start = task.path
	task.branch(0, True, True)
	end = task.branch(0, True, True)
	definition = event_definition(task.instructions[start:end], params, types)
	routine = task.values[name] if name in task.values and task.types[name].type == 'event' else event_method(name)
	routine.register(definition, types[0], tuple(types[1:-1]))
	return routine

arche_event = function_method('.event')
arche_event.retrieve(event_null)

def function_null(task):

	name = task.op.register
	types, params = [task.describe(descriptor.read(i)) for i in task.op.label[0::2]], task.op.label[1::2]
	start, end = task.path, task.branch(0, True, True)
	definition = function_definition(task.instructions[start:end], params, types)
	routine = task.values[name] if name in task.values and task.types[name].type == 'function' else function_method(name)
	routine.register(definition, types[0], tuple(types[1:]))
	return routine

arche_function = function_method('.function')
arche_function.retrieve(function_null)

def index_string_integer(task, sequence, index):
	
	length = task.signature[0].length
	if -length <= index < length:
		return sequence[int(index)] # Sophia's integer type is abstract, Python's isn't
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

def index_string_slice(task, sequence, index):

	length = task.signature[0].length
	if (-length <= index.start < length) and (-length <= index.end < length):
		task.properties.length = task.signature[1].length
		return ''.join(sequence[int(n)] for n in iter(index)) # Constructs slice of string using range
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

def index_list_integer(task, sequence, index):
	
	length = task.signature[0].length
	if -length <= index < length:
		task.properties.type = task.signature[0].member
		return sequence[int(index)]
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

def index_list_slice(task, sequence, index):
	
	length = task.signature[0].length
	if (-length <= index.start < length) and (-length <= index.end < length):
		task.properties.member = task.signature[0].member
		task.properties.length = task.signature[1].length
		return tuple(sequence[int(n)] for n in iter(index))
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

def index_record_untyped(task, sequence, index):
	
	if index in sequence:
		task.properties.type = task.signature[0].member
		return sequence[index]
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

def index_record_slice(task, sequence, index):

	length = task.signature[0].length
	if (-length <= index.start < length) and (-length <= index.end < length):
		task.properties.member = task.signature[0].member
		task.properties.length = task.signature[1].length
		items = tuple(sequence.items())
		return dict(items[int(n)] for n in iter(index))
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

def index_slice_integer(task, sequence, index):

	length = task.signature[0].length
	if -length <= index < length:
		return sequence[int(index)]
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

def index_slice_slice(task, sequence, index):
	
	length = task.signature[0].length
	if (-length <= index.start < length) and (-length <= index.end < length):
		task.properties.length = task.signature[1].length
		return tuple(sequence[int(n)] for n in iter(index))
	else:
		task.properties.type = 'null'
		return task.error('INDX', index)

arche_index = function_method('.index')
arche_index.retrieve(index_string_integer)
arche_index.retrieve(index_string_slice)
arche_index.retrieve(index_list_integer)
arche_index.retrieve(index_list_slice)
arche_index.retrieve(index_record_untyped)
arche_index.retrieve(index_record_slice)
arche_index.retrieve(index_slice_integer)
arche_index.retrieve(index_slice_slice)

def iterator_string(task, iterable):

	return iter(iterable)

def iterator_list(task, iterable):

	return iter(iterable)

def iterator_record(task, iterable):

	return iter(iterable)

def iterator_slice(task, iterable):

	return iter(iterable)

arche_iterator = function_method('.iterator')
arche_iterator.retrieve(iterator_string)
arche_iterator.retrieve(iterator_list)
arche_iterator.retrieve(iterator_record)
arche_iterator.retrieve(iterator_slice)

def link_null(task):
	
	task.message('link', task.op.register + '.sph')
	return task.calls.recv()

arche_link = function_method('.link')
arche_link.retrieve(link_null)

def loop_null(task): # Reverse branch
	
	scope = 1
	while True:
		task.path = task.path - 1
		op = task.instructions[task.path]
		if not op.register:
			scope = scope + 1 if op.name == 'END' else scope - 1
			if scope == 0:
				return

arche_loop = function_method('.loop')
arche_loop.retrieve(loop_null)

def meta_string(task, string):

	meta = module(string, meta = task.name)
	offset = int(task.op.register) - 1
	constants = len([item for item in task.values if item[0] == '&']) - 1
	instructions, values, types = translator(meta, constants = constants).generate(offset = offset)
	start = task.path
	end = task.branch(0, True, False)
	task.instructions[start + 1:end] = instructions
	task.values.update(values)
	task.types.update({k: task.describe(v) for k, v in types.items()})

arche_meta = function_method('.meta')
arche_meta.retrieve(meta_string)

def next_untyped(task, iterator):

	try:
		return next(iterator)
	except StopIteration:
		return None

arche_next = function_method('.next')
arche_next.retrieve(next_untyped)

def return_null(task, sentinel):
	
	if task.caller:
		task.restore(task.caller) # Restore namespace of calling routine
	else:
		task.path = 0 # End task
	return sentinel # Returns null

def return_untyped(task, sentinel):
	
	task.properties = task.final
	if task.caller:
		task.restore(task.caller) # Restore namespace of calling routine
	else:
		task.path = 0 # End task
	return sentinel

arche_return = function_method('.return')
arche_return.retrieve(return_null)
arche_return.retrieve(return_untyped)

def sequence_untyped(task, sequence):
	
	signature = task.signature[0]
	task.properties.member, task.properties.length = signature.member, signature.length
	if not isinstance(sequence, list):
		sequence = [sequence]
	if sequence and isinstance(sequence[0], element): # If items is a key-item pair in a record
		return dict(iter(sequence))
	else: # If list:
		return tuple(sequence)

arche_sequence = function_method('.sequence')
arche_sequence.retrieve(sequence_untyped)

def type_type(task, supertype):
	
	name, supername = task.op.register, supertype.name
	type_tag, final_tag, supertype_tag = descriptor(name), descriptor(name), task.describe(descriptor(supername))
	type_tag.supertypes = [name] + supertype_tag.supertypes
	type_tag.specificity = (supertype_tag.specificity[0] + 1, 0, 0)
	start, end = task.path, task.branch(0, True, True)
	instructions = task.instructions[start:end]
	routine = type_method(name, supertype.supertypes, supertype.prototype)
	routine.register(subtype, final_tag, (type_tag,))
	if supername in aletheia.supertypes: # Built-in supertype
		check = [instruction(supername, '0', (name,)), 
				 instruction('?', '0', ('0',)), # Convert to boolean
				 instruction('.constraint', '0', ('0',), label = [supername])]
		routine.register(type_definition(instructions, name, supertype_tag), final_tag, (supertype_tag,))
		instructions[1:1] = check
		routine.register(type_definition(instructions, name, supertype_tag), final_tag, (descriptor('untyped', prepare = True),))
	else:
		for key, value in list(supertype.methods.items())[1:]: # Rewrite methods with own type name
			definition = [instruction.rewrite(i, supername, name) for i in value.instructions]
			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), final_tag, key)
		routine.register(type_definition(instructions, name, supertype_tag), final_tag, (supertype_tag,))
	return routine

def type_type_untyped(task, supertype, prototype):
	
	name, supername = task.op.register, supertype.name
	type_tag, final_tag, supertype_tag = descriptor(name), descriptor(name), task.describe(descriptor(supername))
	type_tag.supertypes = [name] + supertype_tag.supertypes
	type_tag.specificity = (supertype_tag.specificity[0] + 1, 0, 0)
	start, end = task.path, task.branch(0, True, True)
	instructions = task.instructions[start:end]
	routine = type_method(name, supertype.supertypes, prototype)
	routine.register(subtype, final_tag, (type_tag,))
	if supername in aletheia.supertypes: # Built-in supertype
		check = [instruction(supername, '0', (name,)), 
				 instruction('?', '0', ('0',)), # Convert to boolean
				 instruction('.constraint', '0', ('0',), label = [supername])]
		routine.register(type_definition(instructions, name, supertype_tag), final_tag, (supertype_tag,))
		instructions[1:1] = check
		routine.register(type_definition(instructions, name, supertype_tag), final_tag, (descriptor('untyped', prepare = True),))
	else:
		for key, value in list(supertype.methods.items())[1:]: # Rewrite methods with own type name
			definition = [instruction.rewrite(i, supername, name) for i in value.instructions]
			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), final_tag, key)
		routine.register(type_definition(instructions, name, supertype_tag), final_tag, (supertype_tag,))
	return routine

arche_type = function_method('.type')
arche_type.retrieve(type_type)
arche_type.retrieve(type_type_untyped)

def unloop_null(task, value):
	
	iterator, name = str(int(task.op.args[0]) - 1), task.op.label[0]
	task.values[iterator] = None # Sanitise registers
	del task.values[name], task.types[name]
	return task.branch(1, False, True)

def unloop_untyped(task, value):
	
	return value

arche_unloop = function_method('.unloop')
arche_unloop.retrieve(unloop_null)
arche_unloop.retrieve(unloop_untyped)

"""
Standard streams and I/O operations. These futures are abstract interfaces
with stdin, stdout, and stderr.
"""

stdin = reference(None)
stdin.name, stdin.pid = 'stdin', 0
stdout = reference(None)
stdout.name, stdout.pid = 'stdout', 1
stderr = reference(None)
stderr.name, stderr.pid = 'stderr', 2

def input_string(task, value):
	
	return input(value)

arche_input = function_method('input')
arche_input.retrieve(input_string)

def print_string(task, value):

	print(value)
	return value

arche_print = function_method('print')
arche_print.retrieve(print_string)

def error_string(task, status):
	
	task.error('USER', status)
	return None

arche_error = function_method('error')
arche_error.retrieve(error_string)

"""
Built-in functions.
"""

def abs_number(task, value):

	return value if value >= 0 else -value

arche_abs = function_method('abs')
arche_abs.retrieve(abs_number)

def cast_type_untyped(task, target, value):
	
	try:
		result = getattr(globals()['sophia_' + target.name], '__{0}__'.format(aletheia.names[type(value).__name__]), None)(value)
	except KeyError:
		return task.error('CAST', target.name, value)
	if result is None:
		return task.error('CAST', target.name, value)
	else:
		return result

arche_cast = function_method('cast')
arche_cast.retrieve(cast_type_untyped)

def ceiling_number(task, value):

	return value.__ceil__() # Handled by real

arche_ceiling = function_method('ceiling')
arche_ceiling.retrieve(ceiling_number)

def floor_number(task, value):

	return value.__floor__() # Handled by real

arche_floor = function_method('floor')
arche_floor.retrieve(floor_number)

def format_string_list(task, string, args):

	return string.format(*args)

arche_format = function_method('format')
arche_format.retrieve(format_string_list)

def hash_untyped(task, value):

	return real(hash(value), 1, _normalise = False) # NOT CRYPTOGRAPHICALLY SECURE

arche_hash = function_method('hash')
arche_hash.retrieve(hash_untyped)

def join_list_string(task, sequence, joiner):

	return joiner.join(sequence)

arche_join = function_method('join')
arche_join.retrieve(join_list_string)

def length_string(task, sequence):
	
	return real(task.signature[0].length, 1, _normalise = False)

def length_list(task, sequence):
	
	return real(task.signature[0].length, 1, _normalise = False)

def length_record(task, sequence):
	
	return real(task.signature[0].length, 1, _normalise = False)

def length_slice(task, sequence):
	
	return real(task.signature[0].length, 1, _normalise = False)

arche_length = function_method('length')
arche_length.retrieve(length_string)
arche_length.retrieve(length_list)
arche_length.retrieve(length_record)
arche_length.retrieve(length_slice)

def namespace_null(task): # Do not let the user read working registers

	return {k: v for k, v in task.values.items() if k not in task.reserved}

arche_namespace = function_method('namespace')
arche_namespace.retrieve(namespace_null)

def reverse_slice(task, value):
		
	return slice((value.end, value.start, -value.step))

arche_reverse = function_method('reverse')
arche_reverse.retrieve(reverse_slice)

def round_number(task, value):

	return round(value)

arche_round = function_method('round')
arche_round.retrieve(round_number)

def sign_number(task, value):

	return real(0) if value == 0 else real(int(copysign(1, value)))

arche_sign = function_method('sign')
arche_sign.retrieve(sign_number)

def split_string_string(task, string, separator):

	return tuple(string.split(separator))

arche_split = function_method('split')
arche_split.retrieve(split_string_string)

def sum_list(task, sequence):

	return real(sum(sequence))

def sum_slice(task, sequence):

	return real(sum(i for i in sequence))

arche_sum = function_method('sum')
arche_sum.retrieve(sum_list)
arche_sum.retrieve(sum_slice)

def typeof_untyped(task, value):
	
	return task.values[task.types[task.op.args[0]].type]

arche_typeof = function_method('typeof')
arche_typeof.retrieve(typeof_untyped)

"""
Namespace composition and internals.
"""

builtins = {v.name: v for k, v in globals().items() if k.split('_')[0] in ('cls', 'arche')} | \
		   {'stdin': stdin, 'stdout': stdout, 'stderr': stderr}
types = {i: descriptor(**metadata[i]['type'], prepare = True) for i in builtins}