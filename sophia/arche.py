'''
The Arche module defines the standard library and internal data types.
'''

from fractions import Fraction as real
from sys import stderr

class element(tuple): pass # Stupid hack to make record construction work

class slice: # Slice object

	def __init__(self, indices):
		
		self.indices = indices.copy() # Stores indices for reversal
		indices[1] = indices[1] + 1 if indices[2] >= 0 else indices[1] - 1 # Correction for inclusive range
		self.value = range(*indices) # Stores slice iterator

	def __getitem__(self, index): # Enables O(1) indexing of slices
		
		if index >= 0:
			return self.indices[0] + self.indices[2] * index
		else:
			return self.indices[1] + self.indices[2] * (index + 1)

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
	
	type_name = task.instructions[task.path - 2].split(' ')[2]
	instruction = task.instructions[task.path - 1].split(' ')
	name, known = instruction[1], task.types[instruction[2]]
	if task.cast(value, type_name, known) is not None:
		return task.bind(name, value, infer(value) if type_name == 'null' else type_name)

f_bind = method('.bind')
f_bind.register(bind_untyped,
				'untyped',
				('untyped',))

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

def index_string_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)] # Sophia's integer type is abstract, Python's isn't

def index_string_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		return ''.join(sequence[n] for n in index) # Constructs slice of string using range

def index_list_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)] # Sophia's integer type is abstract, Python's isn't

def index_list_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		return tuple(sequence[n] for n in index) # Constructs list of list using range

def index_record_untyped(task, sequence, index):
	
	if index in sequence:
		return sequence[index]

def index_record_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		items = tuple(sequence.items())
		return dict(items[n] for n in index) # Constructs slice of record using range

def index_slice_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)]

def index_slice_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.indices[0] < length) and (-length <= index.indices[1] < length):
		return tuple(sequence[n] for n in index)

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

	return iter(iterable.value)

def iterator_stream(task, iterable):

	return None # Not yet implemented

f_iterator = method('.iterator')
f_iterator.register(iterator_string,
					'.iterator', # Invalid type so that iterator can be found on the stack
					('string',))
f_iterator.register(iterator_list,
					'.iterator',
					('list',))
f_iterator.register(iterator_record,
					'.iterator',
					('record',))
f_iterator.register(iterator_slice,
					'.iterator',
					('slice',))
f_iterator.register(iterator_stream,
					'.iterator',
					('stream',))

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

def input_string(value):

	return input(value)

f_input = method('input')
f_input.register(input_string,
				 'string',
				 ('string',))

def print_string(value):

	print(value)
	return value

f_print = method('print')
f_print.register(print_string,
				 'string',
				 ('string',))

def error_string(status):
	
	print(status, file = stderr)
	return None

f_error = method('error')
f_error.register(error_string,
				 'untyped', # Fails own type check on purpose
				 ('string',))

# Built-in methods

def cast_type_untyped(target, value):

	while target.supertype:
		target = target.supertype
	return getattr(target, '__' + names[type(value).__name__] + '__')(value)

f_cast = method('cast')
f_cast.register(cast_type_untyped,
				'*', # Signals to infer type
				('type', 'untyped'))

def length_string(sequence):

	return len(sequence)

def length_list(sequence):

	return len(sequence)

def length_record(sequence):

	return len(sequence)

def length_slice(sequence):

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

def reverse_slice(value):
		
	return slice([value.indices[1], value.indices[0], -value.indices[2]])

f_reverse = method('reverse')
f_reverse.register(reverse_slice,
				   'slice',
				   ('slice',))

# Namespace composition

names = {
	'NoneType': 'null', # Internal types
	'int': 'integer',
	'list': 'untyped',
	'element': 'untyped',
	'type': 'type', # User-accessible types
	'event': 'event',
	'method': 'function',
	'bool': 'boolean',
	'Fraction': 'number',
	'str': 'string',
	'tuple': 'list',
	'dict': 'record',
	'slice': 'slice',
	'future': 'future',
	'stream': 'stream'
}

functions = {v.name: v for k, v in globals().items() if k.split('_')[0] == 'f'}

def infer(value): # Infers type of value

	name = type(value).__name__
	if name in names:
		return names[name]
	else:
		return 'untyped'

#class module(coroutine): # Module object is always the top level of a syntax tree

#	def execute(self, routine):
		
#		routine.node = self.source
#		if routine.node:
#			routine.path.pop() # Handles meta-statement

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

#class interface_statement(coroutine):

#	def start(self, routine): # Initialises type
		
#		routine.bind(self.name, self, 'interface')
#		routine.branch() # Skips body of routine

#	def execute(self, routine): return

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

#class while_statement(statement):

#	def start(self, routine):

#		condition = routine.get('boolean')
#		if not condition:
#			routine.node = routine.node.head # Walk upward
#			if routine.node:
#				routine.path.pop()
#				routine.path[-1] = routine.path[-1] + 1
#				while routine.path[-1] < routine.node.length and routine.node.nodes[routine.path[-1]].branch:
#					routine.path[-1] = routine.path[-1] + 1

#	def execute(self, routine):

#		routine.branch(0)

#class for_statement(statement):

#	def start(self, routine):
		
#		sequence = iter(routine.get('iterable')) # Enables fast slice
#		try:
#			value = next(sequence)
#			type_name = self.value.type if self.value.type else routine.check(self.value.value, default = 'untyped')
#			routine.cast(value, type_name)
#			routine.bind(self.value.value, value, type_name)
#			routine.send(sequence, '.index') # Stack trickery with invalid type name
#		except StopIteration:
#			routine.branch(self.node.length)

#	def execute(self, routine):
		
#		sequence, type_name = routine.data.pop(), routine.type_data.pop() # Don't check for type
#		while type_name != '.index':
#			sequence, type_name = routine.data.pop(), routine.type_data.pop()
#		try:
#			value = next(sequence)
#			routine.cast(value, routine.types[self.value.value])
#			routine.bind(self.value.value, value)
#			routine.send(sequence, '.index') # .index isn't even a type
#			routine.branch(1) # Skip start
#		except StopIteration:
#			routine.unbind(self.value.value)

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

#class return_statement(statement):

#	def execute(self, routine):
		
#		if self.nodes:
#			routine.sentinel = routine.get()
#		routine.node = None

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

#class else_statement(statement):

#	def execute(self, routine): return # Final else statement

#class keyword(identifier): # Adds keyword behaviours to a node

#	def start(self, routine):

#		loop = routine.node
#		while not isinstance(loop, (while_statement, for_statement)): # Traverses up to closest enclosing loop
#			loop = loop.head
#			routine.path.pop()
#		routine.node = loop
#		if self.value == 'continue':
#			if loop.value: # For loop
#				loop.execute(routine) if '.index' in routine.type_data else routine.branch(loop.length) # Tests if loop is unbound
#			else:
#				routine.branch(0)
#		elif self.value == 'break':
#			routine.branch()
#			if loop.value: # End for loop correctly
#				routine.data.pop() # Don't check for type
#				type_name = routine.type_data.pop()
#				while type_name != '.index':
#					routine.data.pop()
#					type_name = routine.type_data.pop()
#				routine.unbind(loop.value.value)

#	def execute(self, routine): return # Shouldn't ever be called anyway

#class prefix(operator): # Adds prefix behaviours to a node

#	def execute(self, routine): # Unary operators

#		op = routine.find(self.value) # Gets the operator definition
#		x = routine.get(op.types[1])
#		routine.send(op.unary(routine, x), op.types[0]) # Equivalent for all operators

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

#class infix(operator): # Adds infix behaviours to a node

#	def execute(self, routine):
		
#		op = routine.find(self.value)
#		x, y = routine.get(op.types[2]), routine.get(op.types[1]) # Operands are received in reverse order
#		routine.send(op.binary(routine, y, x), op.types[0])

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

#class infix_r(operator): # Adds right-binding infix behaviours to a node

#	def execute(self, routine):

#		if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a slice object or a dictionary
#			x, y = routine.get(), routine.get()
#			value = [y] + x if self.nodes and self.nodes[1].value == ':' else [y, x]
#			if self.head.value == ':':
#				routine.send(value)
#			elif len(value) == 2:
#				if aletheia.sophia_integer(value[0]): # Equalise integer type
#					value[0] = int(value[0])
#				routine.send(arche.element(value))
#			else:
#				routine.send(arche.slice(value))
#		elif self.value == ',': # Sorts out comma-separated parameters by returning them as a list
#			x, y = routine.get(), routine.get()
#			routine.send([y] + x if self.nodes and self.nodes[1].value == ',' else [y, x])
#		else: # Binary operators
#			op = routine.find(self.value) # Gets the operator definition
#			x, y = routine.get(op.types[2]), routine.get(op.types[1])
#			routine.send(op.binary(routine, y, x), op.types[0])

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