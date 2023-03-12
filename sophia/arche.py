'''
The Arche module defines the standard library and internal data types.
'''

from fractions import Fraction as real
from sys import stderr

class element(tuple): pass # Stupid hack to make record construction work

class slice: # Slice object

	def __init__(self, indices):
		
		self.indices = indices

	def __getitem__(self, index): # Enables O(1) indexing of slices
		
		if index >= 0:
			return self.indices[0] + self.indices[2] * index
		else:
			return self.indices[1] + self.indices[2] * (index + 1)

	def __iter__(self): # Custom range generator for reals

		n = self.indices[0]
		if self.indices[2] >= 0:
			while n <= self.indices[1]:
				yield n
				n = n + self.indices[2]
		else:
			while n >= self.indices[1]:
				yield n
				n = n + self.indices[2]

class method: # Multimethod object

	def __init__(self, name):

		self.name = name
		self.finals = {}
		self.methods = {}

	def register(self, method, final, signature): # Overwrites duplicate signatures
		
		self.finals[signature] = final # Return type
		self.methods[signature] = method # Function

class event: # Multimethod object

	def __init__(self, name):

		self.name = name
		self.finals = {}
		self.sends = {}
		self.methods = {}

	def register(self, method, final, send, signature): # Overwrites duplicate signatures
		
		self.finals[signature] = final # Return type
		self.sends[signature] = send # Send type
		self.methods[signature] = method # Function

# Internal functions

def bind_untyped(task, value):
	
	type_name = task.instructions[task.path].split(' ')[2]
	instruction = task.instructions[task.path - 1].split(' ')
	name, known = instruction[1], task.types[instruction[2]]
	if task.cast(value, type_name, known) is not None:
		return task.bind(name, value, infer(value) if type_name == 'null' else type_name)

f_bind = method('.bind')
f_bind.register(bind_untyped,
				'untyped',
				('untyped',))

def branch_null(task): # Unconditional branch
	
	scope = int(task.instructions[task.path].split(' ')[1])
	while True:
		label = task.instructions[task.path].split(' ')
		peek = task.instructions[task.path + 1]
		if label[0] == ';' and int(label[1]) <= scope and label[2] == '.end' and '.else' not in peek:
			return
		task.path = task.path + 1

def branch_boolean(task, condition): # Conditional branch

	if not condition:
		scope = int(task.instructions[task.path].split(' ')[1])
		while True:
			label = task.instructions[task.path].split(' ')
			if label[0] == ';' and int(label[1]) <= scope and label[2] == '.end':
				return
			task.path = task.path + 1

f_branch = method('.branch')
f_branch.register(branch_null,
				  'null',
				  ())
f_branch.register(branch_boolean,
				  'null',
				  ('boolean',))

def break_null(task):

	scope = int(task.instructions[task.path].split(' ')[1])
	while True:
		label = task.instructions[task.path].split(' ')
		if label[0] == ';' and int(label[1]) <= scope and label[2] == '.end':
			return
		task.path = task.path + 1

f_break = method('.break')
f_break.register(break_null,
				 'null',
				 ())

def concatenate_untyped(task, value):
	
	return [value]

def concatenate_untyped_untyped(task, sequence, value):
	
	return sequence + [value]

f_concatenate = method('.concatenate')
f_concatenate.register(concatenate_untyped,
					   'untyped',
					   ('untyped',))
f_concatenate.register(concatenate_untyped_untyped,
					   'untyped',
					   ('untyped', 'untyped'))

def for_untyped(task, iterator):
	
	type_name = task.instructions[task.path].split(' ')[2]
	instruction = task.instructions[task.path - 1].split(' ')
	name, known = instruction[1], task.types[instruction[2]]
	try:
		value = next(iterator)
		if task.cast(value, type_name, known) is not None:
			return task.bind(name, value, infer(value) if type_name == 'null' else type_name)
	except StopIteration:
		scope = int(task.instructions[task.path].split(' ')[1])
		while True:
			label = task.instructions[task.path].split(' ')
			peek = task.instructions[task.path + 1]
			if label[0] == ';' and int(label[1]) <= scope and label[2] == '.end' and '.else' not in peek:
				return
			task.path = task.path + 1

f_for = method('.for')
f_for.register(for_untyped,
			   'untyped',
			   ('untyped',))

def index_string_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)] # Sophia's integer type is abstract, Python's isn't

def index_string_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		return ''.join(sequence[int(n)] for n in iter(index)) # Constructs slice of string using range

def index_list_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)] # Sophia's integer type is abstract, Python's isn't

def index_list_slice(task, sequence, index):
	
	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		return tuple(sequence[int(n)] for n in iter(index)) # Constructs list of list using range

def index_record_untyped(task, sequence, index):
	
	if index in sequence:
		return sequence[index]

def index_record_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		items = tuple(sequence.items())
		return dict(items[int(n)] for n in iter(index)) # Constructs slice of record using range

def index_slice_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)]

def index_slice_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		return tuple(sequence[int(n)] for n in iter(index))

f_index = method('.index')
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

def iterator_stream(task, iterable):

	return None # Not yet implemented

f_iterator = method('.iterator')
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
f_iterator.register(iterator_stream,
					'untyped',
					('stream',))

def loop_null(task):

	scope = int(task.instructions[task.path].split(' ')[1])
	while True:
		label = task.instructions[task.path].split(' ')
		if label[0] == ';' and int(label[1]) <= scope and label[2] == '.start':
			return
		task.path = task.path - 1

f_loop = method('.loop')
f_loop.register(loop_null,
				'null',
				())

def return_untyped(task, sentinel):
	
	task.path = 0
	return sentinel

f_return = method('.return')
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

f_sequence = method('.sequence')
f_sequence.register(sequence_null,
					'untyped',
					())
f_sequence.register(sequence_untyped,
					'*',
					('untyped',))
f_sequence.register(sequence_slice,
					'list',
					('slice',))

# Built-in I/O functions

def input_string(task, value):

	return input(value)

f_input = method('input')
f_input.register(input_string,
				 'string',
				 ('string',))

def print_string(task, value):

	print(value)
	return value

f_print = method('print')
f_print.register(print_string,
				 'string',
				 ('string',))

def error_string(task, status):
	
	print(status, file = stderr)
	return None

f_error = method('error')
f_error.register(error_string,
				 'untyped', # Fails own type check on purpose
				 ('string',))

# Built-in methods

def cast_type_untyped(task, target, value):

	while target.supertype:
		target = target.supertype
	return getattr(target, '__' + names[type(value).__name__] + '__')(value)

f_cast = method('cast')
f_cast.register(cast_type_untyped,
				'*', # Signals to infer type
				('type', 'untyped'))

def length_string(task, sequence):

	return len(sequence)

def length_list(task, sequence):

	return len(sequence)

def length_record(task, sequence):

	return len(sequence)

def length_slice(task, sequence):

	return real(int((sequence.indices[1] - sequence.indices[0]) / sequence.indices[2]))

f_length = method('length')
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
		
	return slice([value.indices[1], value.indices[0], -value.indices[2]])

f_reverse = method('reverse')
f_reverse.register(reverse_slice,
				   'slice',
				   ('slice',))

# Namespace composition and internals

functions = {v.name: v for k, v in globals().items() if k.split('_')[0] == 'f'}

names = {
	'NoneType': 'null',
	'type': 'type',
	'event': 'event',
	'method': 'function',
	'bool': 'boolean',
	'Fraction': 'number',
	'int': 'integer',
	'str': 'string',
	'tuple': 'list',
	'dict': 'record',
	'slice': 'slice',
	'future': 'future',
	'stream': 'stream'
}

def infer(value): # Infers type of value

	name = type(value).__name__
	if name in names:
		if names[name] == 'number' and value % 1 == 0:
			return 'integer'
		else:
			return names[name]
	else:
		return 'untyped' # Applies to all internal types

#class type_statement(coroutine):

#	def __call__(self, routine, value): # Initialises type routine
		
#		routine.message('call', self, [value])
#		return routine.calls.recv()

#	def start(self, routine): # Initialises type
		
#		for name in self.interfaces:
#			interface = routine.find(name)
#			if not interface:
#				return
#			if not aletheia.sophia_interface(interface):
#				return routine.error('CAST', 'interface', str(interface))
#			if interface.supertype != self.supertype: # Check for compability of interface
#				return routine.error('INTR', interface.name, self.name)
#			self.namespace = self.namespace | {item.name: item for item in interface.nodes} # Interface operations override type operations
#		routine.bind(self.name, self, 'type')
#		routine.branch() # Skips body of routine

#	def execute(self, routine):
		
#		routine.sentinel = routine.find(self.name) # Returns cast value upon success
#		routine.node = None

#class event_statement(coroutine):

#	def __call__(self, args, routine):

#		if len(self.types) - 1 != len(args):
#			return routine.error('ARGS', len(self.types) - 1, len(args)) # Requires data to be sent to the stack
#		for i, arg in enumerate(args):
#			if routine.cast(arg, self.types[i + 1]) is None: # Cast error
#				return None
#		if isinstance(routine.node.head, bind):
#			routine.message('stream', self, args)
#			return routine.calls.recv()
#		else:
#			routine.message('call', self, args)
#			return routine.cast(routine.calls.recv(), self.types[0])

#	def start(self, routine):

#		routine.bind(self.name, self, 'event')
#		routine.branch()

#class function_statement(coroutine):

#	def __call__(self, args, routine):

#		if len(self.types) - 1 != len(args):
#			return routine.error('ARGS', len(self.types) - 1, len(args)) # Requires data to be sent to the stack
#		for i, arg in enumerate(args):
#			if routine.cast(arg, self.types[i + 1]) is None: # Cast error
#				return None
#		if isinstance(routine.node.head, bind):
#			routine.message('future', self, args)
#			return routine.calls.recv()
#		else:
#			routine.message('call', self, args)
#			return routine.cast(routine.calls.recv(), self.types[0])

#	def start(self, routine):
		
#		routine.bind(self.name, self, 'function')
#		routine.branch() # Skips body of routine

#	def execute(self, routine):
		
#		routine.node = None

#class assert_statement(statement):

#	def start(self, routine):
		
#		for i in range(self.active):
#			if routine.get(self.nodes[i].type if self.nodes[i].type else 'untyped') is None:
#				return routine.branch()

#	def execute(self, routine): return
	
#class constraint_statement(statement):

#	def execute(self, routine):
		
#		for constraint in self.nodes:
#			constraint = routine.get('boolean')
#			if not constraint:
#				routine.node = None
#				return

#class link_statement(statement):

#	def execute(self, routine):

#		for item in self.value:
#			name = item.value if '.' in item.value else (item.value + '.sophia')
#			routine.message('link', name, [])
#			routine.bind(name.split('.')[0], routine.calls.recv(), 'process')

#class start_statement(statement):

#	def start(self, routine):

#		routine.branch()

#	def execute(self, routine):

#		routine.node = None

#class bind(prefix): # Defines the bind operator

#	def execute(self, routine):
		
#		address = routine.get('channel')
#		routine.bind(self.value, address, self.type) # Binds routine
#		routine.send(address, 'channel')

#class receive(prefix): # Defines the receive operator

#	def execute(self, routine):
		
#		value = routine.messages.recv()
#		routine.bind(self.value.value, value, self.value.type if self.value.type else None)
#		routine.send(value, self.value.type if self.value.type else None)

#class resolve(prefix): # Defines the resolution operator

#	def execute(self, routine):
		
#		reference = routine.get('channel')
#		routine.message('resolve', reference)
#		routine.send(routine.cast(routine.calls.recv(), reference.type), reference.type)

#class safe(prefix): # Defines the safety operator

#	def execute(self, routine):

#		value = routine.data.pop() # Bypass type checking
#		routine.type_data.pop()
#		routine.send(True if value is not None else False, 'boolean')

#class unsafe(prefix): # Defines the unsafety operator

#	def execute(self, routine):

#		value = routine.get()
#		routine.send(value if value else None) # I'm sure someone has a use for this

#class left_conditional(infix): # Defines the conditional operator

#	def start(self, routine):

#		condition = routine.get('boolean')
#		routine.node = self.nodes[1]
#		routine.path.append(0 if condition else 1)

#	def execute(self, routine): return

#class right_conditional(infix): # Defines the conditional operator

#	def start(self, routine):
		
#		routine.node = self.head
#		routine.path.pop()
#		routine.path[-1] = routine.node.length

#	def execute(self, routine): return

#class send(infix_r): # Defines the send operator

#	def execute(self, routine):
		
#		address = routine.get('channel')
#		routine.message('send', address, routine.get(address.check))
#		routine.send(address, 'channel')

#class function_call(left_bracket):

#	def execute(self, routine):

#		args = routine.get() if self.length > 1 else []
#		if not isinstance(args, list): # Type correction
#			args = [args] # Very tiresome type correction, at that
#		if self.nodes[0].operation: # Type operation
#			args = [routine.get()] + args # Shuffle arguments
#		function = routine.get('callable') # Get actual function
#		routine.send(function(args, routine), None if isinstance(self.head, bind) else function.types[0])

#class meta_statement(left_bracket):

#	def start(self, routine):
		
#		tree = module(routine.get('string'), source = self, name = routine.name) # Here's tree
#		routine.node = tree # Redirect control flow to new tree
#		routine.path.append(0)

#	def execute(self, routine): return