'''
The Arche module defines the standard library and internal data types.
'''

from aletheia import cast
from kadmos import instruction, module, translator
from rationals import Rational as real
from sys import stderr

class element(tuple):
	"""Key-value pair used in record construction."""
	pass

class slice:
	"""Implements an arithmetic slice with inclusive range."""
	__slots__ = ('start', 'end', 'step')

	def __init__(self, indices):
		
		self.start, self.end, self.step = indices

	def __getitem__(self, index): # Enables O(1) indexing of slices
		
		if index >= 0:
			return self.start + self.step * index
		else:
			return self.end + self.step * (index + 1)

	def __iter__(self): # Custom range generator for reals

		n = self.start
		if self.step >= 0:
			while n <= self.end:
				yield n
				n = n + self.step
		else:
			while n >= self.end:
				yield n
				n = n + self.step

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

	def register(self, method, final, signature): # Overwrites duplicate signatures
		
		self.methods[signature] = method # Function
		self.finals[signature] = final # Return type
		self.arity[signature] = len(signature) # Pre-evaluated length of signature

class type_method(method):

	def __init__(self, name, supertypes, prototype):

		super().__init__(name)
		self.supertypes = [name] + supertypes
		self.prototype = prototype
		self.specificity = len(supertypes) + 1
		self.register(self.subtype, name, (name,)) # Subtype check

	def subtype(self, task, value): return value # Type already known

class event_method(method): pass
class function_method(method): pass

class type_definition:
	"""Definition for a user-defined type."""
	def __init__(self, instructions, name, known):

		self.instructions = instructions
		self.name = name
		self.type = known

	def __call__(self, task, value):
		
		task.caller = task.state()
		task.values[self.name], task.types[self.name] = value, self.type
		task.reserved = tuple(i for i in task.values)
		task.instructions = self.instructions
		task.path = 1

class event_definition:
	"""Definition for a user-defined event."""
	def __init__(self, instructions, params, types):

		self.instructions = instructions
		self.name, self.params, self.message = params[0], params[1:-1], params[-1]
		self.type, self.types, self.check = types[0], types[1:-1], types[-1]

	def __call__(self, task, *args):

		if '.bind' in task.op.label:
			name = task.op.label[1]
			task.message('future', self, args, task.values[self.name], self.check)
			task.override = 'future'
			future = task.calls.recv()
			task.values[name], task.types[name] = future, 'future'
			return future
		else:
			task.caller = task.state()
			task.values = task.values | dict(zip(self.params, args))
			task.types = task.types | dict(zip(self.params, self.types))
			task.reserved = tuple(i for i in task.values)
			task.instructions = self.instructions
			task.path = 1

class function_definition:
	"""Definition for a user-defined function."""
	def __init__(self, instructions, params, types):

		self.instructions = instructions
		self.name, self.params = params[0], params[1:]
		self.type, self.types = types[0], types[1:]

	def __call__(self, task, *args):

		if '.bind' in task.op.label:
			name = task.op.label[1]
			task.message('future', self, args, task.values[self.name], None)
			task.override = 'future'
			future = task.calls.recv()
			task.values[name], task.types[name] = future, 'future'
			return future
		else:
			task.caller = task.state()
			task.values = task.values | dict(zip(self.params, args))
			task.types = task.types | dict(zip(self.params, self.types))
			task.reserved = tuple(i for i in task.values)
			task.instructions = self.instructions
			task.path = 1

# Internal functions

def assert_null(task, value): # Null assertion

	scope = 1
	while True:
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0:
				return

def assert_untyped(task, value): # Non-null assertion
	
	return value

f_assert = function_method('.assert')
f_assert.register(assert_null,
				  'null',
				  ('null',))
f_assert.register(assert_untyped,
				  'untyped',
				  ('untyped',))

def bind_untyped(task, value):
	
	name, offset = task.op.label[0], 0
	while task.instructions[task.path + offset].register != name:
		offset = offset + 1
	task.override = task.types[task.op.args[0]]
	task.instructions[task.path + offset].name = task.check(name, default = value) if name in task.values else task.override
	return task.error('BIND', name) if name in task.reserved else value

def bind_untyped_type(task, value, type_routine):
	
	name = task.op.label[0]
	task.override = task.types[task.op.args[0]]
	return task.error('BIND', name) if name in task.reserved else value

f_bind = function_method('.bind')
f_bind.register(bind_untyped,
				'untyped',
				('untyped',))
f_bind.register(bind_untyped_type,
				'untyped',
				('untyped', 'type'))

def branch_null(task): # Unconditional branch
	
	scope = 1
	while True:
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0 and task.instructions[task.path].name != 'ELSE':
				return

def branch_boolean(task, condition): # Conditional branch

	if not condition:
		scope = 1
		while True:
			op, task.path = task.instructions[task.path], task.path + 1
			if not op.register:
				scope = scope - 1 if op.name == 'END' else scope + 1
				if scope == 0:
					return

f_branch = function_method('.branch')
f_branch.register(branch_null,
				  '.',
				  ())
f_branch.register(branch_boolean,
				  '.',
				  ('boolean',))

def break_untyped(task, value): # For loop break

	task.values[task.op.register], task.values[task.op.args[0]] = None, None # Sanitise registers
	while True:
		op, task.path = task.instructions[task.path], task.path + 1
		if op.name == '.loop':
			return

f_break = function_method('.break')
f_break.register(break_untyped,
				 '.',
				 ('untyped',))

def concatenate_untyped(task, value):
	
	return [value]

def concatenate_untyped_untyped(task, sequence, value):
	
	return sequence + [value]

f_concatenate = function_method('.concatenate')
f_concatenate.register(concatenate_untyped,
					   'untyped',
					   ('untyped',))
f_concatenate.register(concatenate_untyped_untyped,
					   'untyped',
					   ('untyped', 'untyped'))

def constraint_boolean(task, constraint):
	
	name = task.instructions[0].label[0]
	if not constraint:
		value = task.values[name]
		task.restore(task.caller)
		return task.error('CAST', name, str(value))
	elif task.op.label and task.op.label[0] != name:
		task.types[name] = task.op.label[0]

f_constraint = function_method('.constraint')
f_constraint.register(constraint_boolean,
					  'null',
					  ('boolean',))

def event_null(task):

	name = task.op.register
	types, params = task.op.label[0::2], task.op.label[1::2]
	start, scope = task.path, 0
	while True: # Collect instructions
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0:
				end = task.path
				break
	while True: # ...Twice
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0:
				end = task.path
				break
	definition = event_definition(task.instructions[start:end], params, types)
	if name in task.values and task.types[name] == 'event':
		routine = task.values[name]
	else:
		routine = event_method(name)
		task.types[name] = 'event'
	routine.register(definition,
					 types[0],
					 tuple(types[1:-1]))
	return routine

f_event = function_method('.event')
f_event.register(event_null,
				 'function',
				 ())

def function_null(task):

	name = task.op.register
	types, params = task.op.label[0::2], task.op.label[1::2]
	start, scope = task.path, 0
	while True: # Collect instructions
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0:
				end = task.path
				break
	definition = function_definition(task.instructions[start:end], params, types)
	if name in task.values and task.types[name] == 'function':
		routine = task.values[name]
	else:
		routine = function_method(name)
		task.types[name] = 'function'
	routine.register(definition,
					 types[0],
					 tuple(types[1:]))
	return routine

f_function = function_method('.function')
f_function.register(function_null,
					'function',
					())

def index_string_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)] # Sophia's integer type is abstract, Python's isn't
	else:
		return task.error('INDX', index)

def index_string_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return ''.join(sequence[int(n)] for n in iter(index)) # Constructs slice of string using range
	else:
		return task.error('INDX', index)

def index_list_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)] # Sophia's integer type is abstract, Python's isn't
	else:
		return task.error('INDX', index)

def index_list_slice(task, sequence, index):
	
	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return tuple(sequence[int(n)] for n in iter(index)) # Constructs list of list using range
	else:
		return task.error('INDX', index)

def index_record_untyped(task, sequence, index):
	
	if index in sequence:
		return sequence[index]
	else:
		return task.error('INDX', index)

def index_record_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		items = tuple(sequence.items())
		return dict(items[int(n)] for n in iter(index)) # Constructs slice of record using range
	else:
		return task.error('INDX', index)

def index_slice_integer(task, sequence, index):

	length = length_slice(task, sequence)
	if -length <= index < length:
		return sequence[int(index)]
	else:
		return task.error('INDX', index)

def index_slice_slice(task, sequence, index):
	
	length = length_slice(task, sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return tuple(sequence[int(n)] for n in iter(index))
	else:
		return task.error('INDX', index)

f_index = function_method('.index')
f_index.register(index_string_integer,
				 'string',
				 ('string', 'integer'))
f_index.register(index_string_slice,
				 'string',
				 ('string', 'slice'))
f_index.register(index_list_integer,
				 '*',
				 ('list', 'integer'))
f_index.register(index_list_slice,
				 'list',
				 ('list', 'slice'))
f_index.register(index_record_untyped,
				 '*',
				 ('record', 'untyped'))
f_index.register(index_record_slice,
				 'record',
				 ('record', 'slice'))
f_index.register(index_slice_integer,
				 'integer',
				 ('slice', 'integer'))
f_index.register(index_slice_slice,
				 'list',
				 ('slice', 'slice'))

def iterator_string(task, iterable):

	return iter(iterable)

def iterator_list(task, iterable):

	return iter(iterable)

def iterator_record(task, iterable):

	return iter(iterable)

def iterator_slice(task, iterable):

	return iter(iterable)

f_iterator = function_method('.iterator')
f_iterator.register(iterator_string,
					'untyped',
					('string',))
f_iterator.register(iterator_list,
					'untyped',
					('list',))
f_iterator.register(iterator_record,
					'untyped',
					('record',))
f_iterator.register(iterator_slice,
					'untyped',
					('slice',))

def link_null(task):
	
	name = task.op.register
	task.message('link', name if '.' in name else (name + '.sph'))
	return task.calls.recv()

f_link = function_method('.link')
f_link.register(link_null,
				'future',
				())

def loop_null(task): # Reverse branch

	scope = 1
	while True:
		task.path = task.path - 1
		op = task.instructions[task.path]
		if not op.register:
			scope = scope + 1 if op.name == 'END' else scope - 1
			if scope == 0:
				return

f_loop = function_method('.loop')
f_loop.register(loop_null,
				'.',
				())

def meta_string(task, string):

	meta = module(string, meta = task.name)
	offset = int(task.op.register) - 1
	constants = len([item for item in task.values if item[0] == '&']) - 1
	instructions, values, types = translator(meta, constants = constants).generate(offset = offset)
	start, path, scope = task.path, task.path, 0
	while True: # Collect instructions
		op, path = task.instructions[path], path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0:
				end = path
				break
	task.instructions = task.instructions[:start + 1] + instructions + task.instructions[end:]
	task.values.update(values)
	task.types.update(types)

f_meta = function_method('.meta')
f_meta.register(meta_string,
				'*',
				('string',))

def next_untyped(task, iterator):

	try:
		return next(iterator)
	except StopIteration:
		return None

f_next = function_method('.next')
f_next.register(next_untyped,
				'*',
				('untyped',))

def return_untyped(task, sentinel):
	
	if task.caller:
		task.restore(task.caller) # Restore namespace of calling routine
		if task.types[task.op.name] == 'type':
			task.override = task.op.name # Allow type checks to return their own type
	else:
		task.path = 0 # End task
	return sentinel

f_return = function_method('.return')
f_return.register(return_untyped,
				  'null',
				  ('null',))
f_return.register(return_untyped,
				  'untyped',
				  ('untyped',))

def sequence_null(task):

	return []

def sequence_untyped(task, sequence):
	
	if not isinstance(sequence, list):
		sequence = [sequence]
	if sequence and isinstance(sequence[0], element): # If items is a key-item pair in a record
		return dict(iter(sequence)) # Better way to merge a list of key-value pairs into a record
	else: # If list or slice:
		return tuple(sequence)

def sequence_slice(task, sequence):

	return tuple(sequence) # Tuple expands slice

f_sequence = function_method('.sequence')
f_sequence.register(sequence_null,
					'untyped',
					())
f_sequence.register(sequence_untyped,
					'*',
					('untyped',))
f_sequence.register(sequence_slice,
					'list',
					('slice',))


def type_type(task, supertype):
	
	name, supername = task.op.register, supertype.name
	start, scope = task.path, 0
	while True: # Collect instructions
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0:
				break
	end = task.path
	instructions = task.instructions[start:end]
	routine = type_method(name, supertype.supertypes, supertype.prototype)
	if isinstance(supertype.methods[('untyped',)], type): # Built-in supertype
		check = [instruction(supername, '0', (name,)), 
				 instruction('?', '0', ('0',)), # Convert to boolean
				 instruction('.constraint', '0', ('0',), label = [supername])]
		routine.register(type_definition([instructions[0]] + check + instructions[1:], name, supername), name, ('untyped',))
		routine.register(type_definition(instructions, name, supername), name, (supername,))
	else:
		for key, value in list(supertype.methods.items())[1:]: # Rewrite methods with own type name
			definition = [instruction.rewrite(i, supername, name) for i in value.instructions]
			definition = definition[:-2] + instructions[1:-2] + definition[-2:] # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), name, key)
		routine.register(type_definition(instructions, name, supername), name, (supername,))
	return routine

def type_type_untyped(task, supertype, prototype):
	
	name, supername = task.op.register, supertype.name
	start, scope = task.path, 0
	while True: # Collect instructions
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0:
				break
	end = task.path
	instructions = task.instructions[start:end]
	routine = type_method(name, supertype.supertypes, prototype)
	if isinstance(supertype.methods[('untyped',)], type): # Built-in supertype
		check = [instruction(supername, '0', (name,)), 
				 instruction('?', '0', ('0',)), # Convert to boolean
				 instruction('.constraint', '0', ('0',), label = [supername])]
		routine.register(type_definition([instructions[0]] + check + instructions[1:], name, supername), name, ('untyped',))
		routine.register(type_definition(instructions, name, supername), name, (supername,))
	else:
		for key, value in list(supertype.methods.items())[1:]: # Rewrite methods with own type name
			definition = [instruction.rewrite(i, supername, name) for i in value.instructions]
			definition = definition[:-2] + instructions[1:-2] + definition[-2:] # Add user constraints to instructions
			routine.register(type_definition(definition, name, key[0]), name, key)
		routine.register(type_definition(instructions, name, supername), name, (supername,))
	return routine

f_type = function_method('.type')
f_type.register(type_type,
				'type',
				('type',))
f_type.register(type_type_untyped,
				'type',
				('type', 'untyped'))

def unloop_null(task, value):

	iterator, name = str(int(task.op.args[0]) - 1), task.op.label[0]
	task.values[iterator] = None # Sanitise registers
	del task.values[name], task.types[name]
	scope = 1
	while True:
		op, task.path = task.instructions[task.path], task.path + 1
		if not op.register:
			scope = scope - 1 if op.name == 'END' else scope + 1
			if scope == 0 and task.instructions[task.path].name != 'ELSE':
				return

def unloop_untyped(task, value):

	return value

f_unloop = function_method('.unloop')
f_unloop.register(unloop_null,
				  'null',
				  ('null',))
f_unloop.register(unloop_untyped,
				  '*',
				  ('untyped',))

# Built-in I/O functions

def input_string(task, value):

	return input(value)

f_input = function_method('input')
f_input.register(input_string,
				 'string',
				 ('string',))

def print_string(task, value):

	print(value)
	return value

f_print = function_method('print')
f_print.register(print_string,
				 'string',
				 ('string',))

def error_string(task, status):
	
	print(status, file = stderr)
	return None

f_error = function_method('error')
f_error.register(error_string,
				 'untyped', # Fails own type check on purpose
				 ('string',))

# Built-in methods

f_cast = function_method('cast')
f_cast.register(cast,
				'*', # Signals to infer type
				('type', 'untyped'))

def length_string(task, sequence):

	return real(len(sequence), 1, _normalise = False)

def length_list(task, sequence):

	return real(len(sequence), 1, _normalise = False)

def length_record(task, sequence):

	return real(len(sequence), 1, _normalise = False)

def length_slice(task, sequence):

	return real(int((sequence.end - sequence.start) / sequence.step), 1, _normalise = False)

f_length = function_method('length')
f_length.register(length_string,
				  'integer',
				  ('string',))
f_length.register(length_list,
				  'integer',
				  ('list',))
f_length.register(length_record,
				  'integer',
				  ('record',))
f_length.register(length_slice,
				  'integer',
				  ('slice',))

def reverse_slice(task, value):
		
	return slice([value.end, value.start, -value.step])

f_reverse = function_method('reverse')
f_reverse.register(reverse_slice,
				   'slice',
				   ('slice',))

def round_number(task, value):

	return round(value)

f_round = function_method('round')
f_round.register(round_number,
				 'integer',
				 ('number',))

# Namespace composition and internals

functions = {v.name: v for k, v in globals().items() if k.split('_')[0] == 'f'}