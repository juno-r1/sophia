'''
The Arche module defines the standard library of Sophia.
'''

from aletheia import descriptor, dispatch, infer, subtype
from iris import reference
from mathos import real, slice, element
from math import copysign
from functools import reduce
import aletheia, kadmos

import json
with open('kleio.json') as kleio:
	metadata = json.load(kleio)
del kleio # Python inexplicably does not free this automatically

class method:
	"""
	Implements a multimethod.
	Multimethods enable multiple dispatch on functions. Functions dispatch for
	the arity and types of their arguments. The precedence for dispatch is
	left-to-right, then most to least specific type.
	"""
	def __init__(self, name):

		self.name = name
		self.tree = dispatch(None)

	def retrieve(self, routine): # Retrieves metadata from Kleio

		data = metadata[self.name][routine.__name__]
		self.tree.extend(routine, descriptor(**data['final'], prepare = True), [descriptor(**i, prepare = True) for i in data['signature']])

	def register(self, definition, final, signature): # Registers user-defined definition
		
		self.tree.extend(definition, final, signature)

class type_method(method):

	def __init__(self, name, supertypes, prototype):

		super().__init__(name)
		self.supertypes = [name] + supertypes
		self.prototype = prototype

class event_method(method): pass
class function_method(method): pass

class definition:
	"""Definition for a user-defined method."""
	def __init__(self, instructions, names, signature):
		
		self.instructions = instructions
		self.name = names[0]
		self.params = names[1:]
		self.final = signature[0]
		self.signature = signature[1:]

class type_definition(definition):
	"""Definition for a user-defined type."""
	def __init__(self, instructions, name, supertype):
		
		super().__init__(instructions, (name, name), (descriptor(name), supertype))

	def __call__(self, task, value):
		
		task.caller = task.state()
		task.final = self.final
		task.values[self.name], task.types[self.name] = value, self.signature[0]
		task.reserved = tuple(task.values)
		task.instructions = self.instructions
		task.cache = [None for _ in self.instructions]
		task.path = 1

class event_definition(definition):
	"""Definition for a user-defined event."""
	def __init__(self, instructions, params, types):

		super().__init__(instructions, params[:-1], types[:-1])
		self.message = params[-1]
		self.check = types[-1]

	def __call__(self, task, *args):

		if '.bind' in task.op.label:
			task.message('future', self, args, task.values[self.name])
			task.properties.type = 'future'
			return task.calls.recv()
		else:
			task.caller = task.state()
			task.final = self.final
			task.values = task.values | dict(zip(self.params, args))
			task.types = task.types | dict(zip(self.params, self.signature))
			task.reserved = tuple(task.values)
			task.instructions = self.instructions
			task.cache = [None for _ in self.instructions]
			task.path = 1

class function_definition(definition):
	"""Definition for a user-defined function."""
	def __call__(self, task, *args):

		if '.bind' in task.op.label:
			task.message('future', self, args, task.values[self.name])
			task.properties.type = 'future'
			return task.calls.recv()
		else:
			task.caller = task.state()
			task.final = self.final
			task.values = task.values | dict(zip(self.params, args))
			task.types = task.types | dict(zip(self.params, self.signature))
			task.reserved = tuple(task.values)
			task.instructions = self.instructions
			task.cache = [None for _ in self.instructions]
			task.path = 1

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
		
		return value if isinstance(value, cls.types) else task.error('CAST', cls.name, str(value))

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

class sophia_routine(sophia_untyped): # Routine abstract type
	
	name = 'routine'
	types = type_method, event_method, function_method

cls_type = type_method('routine', ['untyped'], None)
cls_type.retrieve(sophia_routine)
cls_type.retrieve(subtype)

class sophia_type(sophia_untyped): # Type type
	
	name = 'type'
	types = type_method

cls_type = type_method('type', ['routine', 'untyped'], None)
cls_type.retrieve(sophia_type)
cls_type.retrieve(subtype)

class sophia_event(sophia_untyped): # Event type

	name = 'event'
	types = event_method

cls_event = type_method('event', ['routine', 'untyped'], None)
cls_event.retrieve(sophia_event)
cls_event.retrieve(subtype)

class sophia_function(sophia_untyped): # Function type

	name = 'function'
	types = function_method

cls_function = type_method('function', ['routine', 'untyped'], None)
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
	def __string__(cls, value): return real.read(value)

	@classmethod
	def __future__(cls, value): return real(value.pid)

cls_number = type_method('number', ['untyped'], real())
cls_number.retrieve(sophia_number)
cls_number.retrieve(subtype)

class sophia_integer(sophia_number): # Integer type

	name = 'integer'
	types = real

	def __new__(cls, task, value):
		
		try: # Faster than isinstance(), I think
			return value if value % 1 == 0 else task.error('CAST', cls.name, str(value))
		except TypeError:
			return task.error('CAST', cls.name, str(value))

cls_integer = type_method('integer', ['number', 'untyped'], real())
cls_integer.retrieve(sophia_integer)
cls_integer.retrieve(subtype)

class sophia_sequence(sophia_untyped): # Sequence abstract type
	
	name = 'sequence'
	types = str, tuple, dict, slice

cls_type = type_method('sequence', ['untyped'], None)
cls_type.retrieve(sophia_sequence)
cls_type.retrieve(subtype)

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

cls_string = type_method('string', ['sequence', 'untyped'], '')
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

cls_record = type_method('record', ['sequence', 'untyped'], {})
cls_record.retrieve(sophia_record)
cls_record.retrieve(subtype)

class sophia_slice(sophia_untyped): # Slice type

	name = 'slice'
	types = slice

cls_slice = type_method('slice', ['sequence', 'untyped'], slice((real(), real(), real(1))))
cls_slice.retrieve(sophia_slice)
cls_slice.retrieve(subtype)

class sophia_future(sophia_untyped): # Process type
	
	name = 'future'
	types = reference

cls_future = type_method('future', ['sequence', 'untyped'], None)
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
	task.properties.merge(x.check)
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
		lower, upper = ranges[1], ranges[2]
		lower = lower - (lower % step) + step # Gets highest lower bound
		upper = upper - (upper % step) # Gets lowest upper bound
		return slice((lower, upper, m))

def b_ins_type(task, x, y):
	
	name, supername = '<{0}&{1}>'.format(x.name, y.name), [i for i in x.supertypes if i in y.supertypes][0] # Use closest mutual supertype
	supertype, index = task.values[supername], x.supertypes.index(supername)
	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
	type_tag.supertypes = [name] + super_tag.supertypes
	routine = type_method(name, x.supertypes[index:], x.prototype)
	routine.register(subtype, final_tag, (type_tag,))
	lhs, rhs = kadmos.generate_intersection(name, x.name), kadmos.generate_intersection(name, y.name)
	check = lhs + rhs
	start, end = kadmos.generate_labels(name)
	tree = supertype.tree.true
	while tree: # Rewrite methods with own type name
		key, value = tree.false.signature, tree.false.routine
		if isinstance(value, type_definition):
			definition = [kadmos.instruction.rewrite(i, supername, name) for i in value.instructions]
			definition[-2:-2] = check # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), final_tag, key)
		else: # Built-in definition
			routine.register(type_definition(start + check + end, name, key[0]), final_tag, key)
		tree = tree.true
	routine.register(type_definition(start + rhs + end, name, super_tag), final_tag, (type_tag,))
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
	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
	type_tag.supertypes = [name] + super_tag.supertypes
	routine = type_method(name, x.supertypes[index:], x.prototype)
	routine.register(subtype, final_tag, (type_tag,))
	check = kadmos.generate_union(name, x.name, y.name)
	start, end = kadmos.generate_labels(name)
	tree = supertype.tree.true
	while tree: # Rewrite methods with own type name
		key, value = tree.false.signature, tree.false.routine
		if isinstance(value, type_definition): # Built-in supertype
			definition = [kadmos.instruction.rewrite(i, supername, name) for i in value.instructions]
			definition[-2:-2] = check # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), final_tag, key)
		else:
			routine.register(type_definition(start + check + end, name, key[0]), final_tag, key)
		tree = tree.true
	routine.register(type_definition(start + end, name, super_tag), final_tag, (type_tag,))
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
	
	task.properties.merge(task.signature[0])
	return x

def b_sfe_null_untyped(task, x, y):
	
	task.properties.merge(task.signature[1])
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

def b_cmp(task, x, y):
	
	new = function_method('{0}.{1}'.format(x.name, y.name))
	methods = [i for i in y.tree.collect()] # Methods of 1st function
	for method in methods:
		tree = x.tree.true # Dispatch tree of 2nd function
		while tree:
			if tree.index == 0:
				tree = tree.true if tree.op(method.final) else tree.false
			else:
				tree = tree.false
		if tree is None:
			continue
		instance, final, x_signature = tree.routine, tree.final, tree.signature
		if not method.final < x_signature[0]:
			continue
		routine = method.routine
		y_signature = method.signature
		try:
			x_params = instance.params
			x_instructions = instance.instructions
		except AttributeError: # x is built-in
			x_params = ['x' + str(i) for i, _ in enumerate(x_signature)]
			x_instructions = kadmos.generate_x_function(x.name, x_params)
		try:
			y_params = routine.params
			y_instructions = routine.instructions
		except AttributeError: # y is built-in
			y_params = ['x' + str(i) for i, _ in enumerate(y_signature)]
			y_instructions = kadmos.generate_y_function(y.name, y_params, x_params[0])
		for op in y_instructions: # Rewrite 1st function so that returns set up the 2nd function instead
			if op.name == '.return':
				op.name, op.register = '.skip', x_params[0]
		instructions = y_instructions + [kadmos.instruction('RETURN', '')] + x_instructions
		print(*instructions, sep = '\n')
		definition = function_definition(instructions, [new.name] + y_params, [final] + list(y_signature))
		new.register(definition, final, method.signature)
	if new.tree.true is None and new.tree.false is None: # Empty tree
		del new
		return task.error('COMP', x.name, y.name)
	else:
		return new

arche_cmp = function_method('.')
arche_cmp.retrieve(b_cmp)

"""
Internal functions. The names of these functions are prefixed with "." to make
them inaccessible to the user.
"""

def alias_type(task, routine): # Type alias

	replace, name, supername = routine.name, task.op.register, routine.supertypes[1]
	new_tag, final_tag = descriptor(supername).describe(task), descriptor(name)
	new_tag.type = name
	new_tag.supertypes = [name] + new_tag.supertypes
	new = type_method(name, routine.supertypes[1:], routine.prototype)
	tree = routine.tree.true
	while tree: # Rewrite methods with own type name
		if tree.value == replace:
			tree.value = name
		key, value = tree.false.signature, tree.false.routine
		new.register(type_definition([kadmos.instruction.rewrite(i, replace, name) for i in value.instructions]
									 if isinstance(value, type_definition)
									 else value, name, key[0]), final_tag, key)
		tree = tree.true
	new.register(subtype, final_tag, (new_tag,))
	return new

def alias_function(task, routine): # Function alias

	name = task.op.register
	new = function_method(name)
	methods = routine.tree.collect()
	for method in methods:
		instance = method.routine
		try:
			definition = function_definition(instance.instructions, [name] + instance.params, [method.final] + list(method.signature))
			new.register(definition, method.final, method.signature)
		except AttributeError: # Built-ins
			new.register(instance, method.final, method.signature)
	return new

arche_alias = function_method('.alias')
arche_alias.retrieve(alias_type)
arche_alias.retrieve(alias_function)

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
	task.instructions[task.path + offset].name = task.types[name].type if name in task.types else signature.type
	if name in task.reserved:
		return task.error('BIND', name)
	else:
		task.properties.__dict__.update(signature.__dict__)
		return value

def bind_untyped_type(task, value, type_routine):
	
	name, signature = task.op.label[0], task.signature[0]
	if name in task.reserved:
		return task.error('BIND', name)
	else:
		task.properties.__dict__.update(signature.__dict__)
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

def concatenate_sequence_untyped(task, sequence, value):
	
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
arche_concatenate.retrieve(concatenate_sequence_untyped)

def constraint_boolean(task, constraint):
	
	name = task.instructions[0].label[0]
	if not constraint:
		value = task.values[name]
		task.restore(task.caller)
		task.error('CAST', name, str(value))
	elif task.op.label and task.op.label[0] != name: # Update type of checked value for subsequent constraints
		task.types[name].type = task.op.label[0]
		task.types[name].describe(task)

arche_constraint = function_method('.constraint')
arche_constraint.retrieve(constraint_boolean)

def event_null(task):

	name = task.op.register
	types, params = [descriptor.read(i).describe(task) for i in task.op.label[0::2]], task.op.label[1::2]
	start = task.path
	task.branch(0, True, True)
	end = task.branch(0, True, True)
	definition = event_definition(task.instructions[start:end], params, types)
	routine = task.values[name] if name in task.values and task.types[name].type == 'event' else event_method(name)
	routine.register(definition, types[0], tuple(types[1:-1]))
	task.cache = [None for i in task.cache]
	return routine

arche_event = function_method('.event')
arche_event.retrieve(event_null)

def function_null(task):
	
	name = task.op.register
	types, params = [descriptor.read(i).describe(task) for i in task.op.label[0::2]], task.op.label[1::2]
	start, end = task.path, task.branch(0, True, True)
	definition = function_definition(task.instructions[start:end], params, types)
	routine = task.values[name] if name in task.values and task.types[name].type == 'function' else function_method(name)
	routine.register(definition, types[0], tuple(types[1:]))
	task.cache = [None for i in task.cache] # Clean up cache to ensure correct dispatch
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

def iterator_sequence(task, sequence):

	task.properties.member = task.signature[0].member
	return iter(sequence)

arche_iterator = function_method('.iterator')
arche_iterator.retrieve(iterator_sequence)

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

	meta = kadmos.module(string, meta = task.name)
	offset = int(task.op.register) - 1
	constants = len([item for item in task.values if item[0] == '&']) - 1
	instructions, values, types = kadmos.translator(meta, constants = constants).generate(offset = offset)
	start = task.path
	end = task.branch(0, True, False)
	task.instructions[start + 1:end] = instructions
	task.cache[start + 1:end] = [None for _ in instructions]
	task.values.update(values)
	task.types.update({k: v.describe(task) for k, v in types.items()})

arche_meta = function_method('.meta')
arche_meta.retrieve(meta_string)

def next_untyped(task, iterator):
	
	try:
		task.properties.type = task.signature[0].member
		return next(iterator)
	except StopIteration:
		task.properties.type = 'null'
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
	
	task.properties.merge(task.final)
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

def skip_untyped(task, value):

	signature, final = task.signature[0], task.properties
	final.type, final.member, final.length = signature.type, signature.member, signature.length
	path = task.path
	while True:
		op, path = task.instructions[path], path + 1
		if not op.register and op.name == 'RETURN':
			task.path = path
			return value

arche_skip = function_method('.skip')
arche_skip.retrieve(skip_untyped)

def type_type(task, supertype):
	
	name, supername = task.op.register, supertype.name
	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
	type_tag.supertypes = [name] + super_tag.supertypes
	start, end = task.path, task.branch(0, True, True)
	instructions = task.instructions[start:end]
	routine = type_method(name, supertype.supertypes, supertype.prototype)
	task.cache = [None for i in task.cache]
	if supername in aletheia.supertypes: # Built-in supertype
		check = kadmos.generate_supertype(name, supername)
		routine.register(type_definition(instructions, name, super_tag), final_tag, (super_tag,))
		instructions[1:1] = check
		routine.register(type_definition(instructions, name, super_tag), final_tag, (descriptor('untyped', prepare = True),))
	else:
		tree = supertype.tree.true
		while tree: # Traverse down tree and copy all false leaves
			key, value = tree.false.signature, tree.false.routine
			definition = [kadmos.instruction.rewrite(i, supername, name) for i in value.instructions] # Rewrite methods with own type name
			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), final_tag, key)
			tree = tree.true
		routine.register(type_definition(instructions, name, super_tag), final_tag, (super_tag,))
	routine.register(subtype, final_tag, (type_tag,))
	return routine

def type_type_untyped(task, supertype, prototype):
	
	name, supername = task.op.register, supertype.name
	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
	type_tag.supertypes = [name] + super_tag.supertypes
	start, end = task.path, task.branch(0, True, True)
	instructions = task.instructions[start:end]
	routine = type_method(name, supertype.supertypes, prototype)
	task.cache = [None for i in task.cache]
	if supername in aletheia.supertypes: # Built-in supertype
		check = kadmos.generate_supertype(name, supername)
		routine.register(type_definition(instructions, name, super_tag), final_tag, (super_tag,))
		instructions[1:1] = check
		routine.register(type_definition(instructions, name, super_tag), final_tag, (descriptor('untyped', prepare = True),))
	else:
		tree = supertype.tree.true
		while tree: # Traverse down tree and copy all false leaves
			key, value = tree.false.signature, tree.false.routine
			definition = [kadmos.instruction.rewrite(i, supername, name) for i in value.instructions] # Rewrite methods with own type name
			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), final_tag, key)
			tree = tree.true
		routine.register(type_definition(instructions, name, super_tag), final_tag, (super_tag,))
	routine.register(subtype, final_tag, (type_tag,))
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
	
	name, signature = task.op.label[0], task.signature[0]
	if name in task.reserved:
		return task.error('BIND', name)
	else:
		task.properties.__dict__.update(signature.__dict__)
		return value

def unloop_null_type(task, value, routine):
	
	iterator, name = str(int(task.op.args[0]) - 1), task.op.label[0]
	task.values[iterator] = None # Sanitise registers
	del task.values[name], task.types[name]
	return task.branch(1, False, True)

def unloop_untyped_type(task, value, routine):
	
	return value

arche_unloop = function_method('.unloop')
arche_unloop.retrieve(unloop_null)
arche_unloop.retrieve(unloop_untyped)
arche_unloop.retrieve(unloop_null_type)
arche_unloop.retrieve(unloop_untyped_type)

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

def dispatch_function_list(task, routine, signature):
	
	tree = routine.tree.true if signature else routine.tree.false
	while tree:
		try:
			tree = tree.true if tree.op(signature[tree.index]) else tree.false
		except IndexError:
			tree = tree.false
	try:
		if tree is None:
			raise KeyError
		instance, final, result = tree.routine, tree.final, tree.signature
		for i, item in enumerate(signature): # Verify type signature
			if not item < result[i]:
				raise KeyError
	except (IndexError, KeyError):
		return task.error('DISP', routine.name, signature)
	new = function_method(routine.name)
	try:
		definition = function_definition(instance.instructions, [routine.name] + instance.params, [final] + list(signature))
		new.register(definition, final, signature)
	except AttributeError: # Built-ins
		new.register(instance, final, signature)
	return new

arche_dispatch = function_method('dispatch')
arche_dispatch.retrieve(dispatch_function_list)

def floor_number(task, value):

	return value.__floor__() # Handled by real

arche_floor = function_method('floor')
arche_floor.retrieve(floor_number)

def filter_function_list(task, routine, target):

	result, member, length = [], task.signature[1].member, 0
	for value in target: # Dispatch and execute for each element of the list
		signature = descriptor(member).complete(infer(value), value).describe(task)
		tree = routine.tree.true if target else routine.tree.false
		while tree: # Traverse tree; terminates upon reaching leaf node
			tree = tree.true if tree.index == 0 and tree.op(signature) else tree.false
		if (tree is None) or len(tree.signature) > 1 or not (signature < tree.signature[0]):
			return task.error('DISP', routine.name, signature)
		instance, signature = tree.routine, tree.signature
		if 'boolean' not in tree.final.supertypes:
			return task.error('FLTR', routine.name, value)
		if isinstance(instance, function_definition):
			caller = task.caller
			instance(task, value)
			check = task.run() # WARNING: Recursive runtime
			task.caller = caller
		else: # Built-ins
			check = instance(task, value)
		if check:
			result.append(value)
			length = length + 1
	task.properties.member = member # Member type remains constant
	task.properties.length = length
	return result

arche_filter = function_method('filter')
arche_filter.retrieve(filter_function_list)

def format_string_list(task, string, args):

	return string.format(*args)

arche_format = function_method('format')
arche_format.retrieve(format_string_list)

def hash_untyped(task, value):

	return real(hash(value)) # NOT CRYPTOGRAPHICALLY SECURE

arche_hash = function_method('hash')
arche_hash.retrieve(hash_untyped)

def join_list_string(task, sequence, joiner):

	return joiner.join(sequence)

arche_join = function_method('join')
arche_join.retrieve(join_list_string)

def length_string(task, sequence):
	
	return real(task.signature[0].length)

def length_list(task, sequence):
	
	return real(task.signature[0].length)

def length_record(task, sequence):
	
	return real(task.signature[0].length)

def length_slice(task, sequence):
	
	return real(task.signature[0].length)

arche_length = function_method('length')
arche_length.retrieve(length_string)
arche_length.retrieve(length_list)
arche_length.retrieve(length_record)
arche_length.retrieve(length_slice)

def map_function_list(task, routine, target):

	result, final, member = [], [], task.signature[1].member
	for value in target: # Dispatch and execute for each element of the list
		signature = descriptor(member).complete(infer(value), value).describe(task)
		tree = routine.tree.true if target else routine.tree.false
		while tree: # Traverse tree; terminates upon reaching leaf node
			tree = tree.true if tree.index == 0 and tree.op(signature) else tree.false
		if (tree is None) or len(tree.signature) > 1 or not (signature < tree.signature[0]):
			return task.error('DISP', routine.name, signature)
		instance, signature = tree.routine, tree.signature
		final.append(tree.final)
		if isinstance(instance, function_definition):
			caller = task.caller
			instance(task, value)
			result.append(task.run()) # WARNING: Recursive runtime
			task.caller = caller
		else: # Built-ins
			result.append(instance(task, value))
	final = reduce(descriptor.mutual, final) # Use the return type of the map, not the inferred type of the elements
	task.properties.member = final.type
	return result

arche_map = function_method('map')
arche_map.retrieve(map_function_list)

def namespace_null(task): # Do not let the user read working registers

	return {k: v for k, v in task.values.items() if k not in task.reserved}

arche_namespace = function_method('namespace')
arche_namespace.retrieve(namespace_null)

def reduce_function_list(task, routine, target):
	
	try:
		x, member = target[0], task.signature[1].member
		x_type = descriptor(member).complete(infer(x), x).describe(task)
	except IndexError:
		return task.error('RDCE')
	for y in target[1:]: # Dispatch and execute for each element of the list
		y_type = descriptor(member).complete(infer(y), y).describe(task)
		xy = [x_type, y_type]
		tree = routine.tree.true if target else routine.tree.false
		while tree: # Traverse tree; terminates upon reaching leaf node
			try:
				tree = tree.true if tree.op(xy[tree.index]) else tree.false
			except IndexError:
				tree = tree.false
		try:
			if tree is None:
				raise KeyError
			instance, final, signature = tree.routine, tree.final, tree.signature
			for i, item in enumerate(xy): # Verify type signature
				if not item < signature[i]:
					raise KeyError
		except (IndexError, KeyError):
			return task.error('DISP', routine.name, xy)
		if isinstance(instance, function_definition):
			caller = task.caller
			instance(task, x, y)
			x = task.run() # WARNING: Recursive runtime
			task.caller = caller
		else: # Built-ins
			x = instance(task, x, y)
		x_type, y_type = final, member
	task.properties.merge(final)
	return x

arche_reduce = function_method('reduce')
arche_reduce.retrieve(reduce_function_list)

def reverse_slice(task, value):
		
	return slice((value.end, value.start, -value.step))

arche_reverse = function_method('reverse')
arche_reverse.retrieve(reverse_slice)

def round_number(task, value):

	return round(value)

arche_round = function_method('round')
arche_round.retrieve(round_number)

def sign_number(task, value):

	return real() if value == 0 else real(int(copysign(1, value)))

arche_sign = function_method('sign')
arche_sign.retrieve(sign_number)

def signature_function_list(task, routine, signature):

	tree = routine.tree.true if signature else routine.tree.false
	while tree:
		try:
			tree = tree.true if tree.op(signature[tree.index]) else tree.false
		except IndexError:
			tree = tree.false
	try:
		if tree is None:
			raise KeyError
		for i, item in enumerate(signature): # Verify type signature
			if not item < tree.signature[i]:
				raise KeyError
		return True
	except (IndexError, KeyError):
		return False

arche_signature = function_method('signature')
arche_signature.retrieve(signature_function_list)

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
types = {k: infer(v) for k, v in builtins.items()}