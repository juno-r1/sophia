'''
Internal functions. The names of these functions are prefixed with "." to make
them inaccessible to the user.
'''

from ..datatypes.aletheia import funcdef, eventdef, typedef
from ..datatypes.mathos import real, slice

def assert_none(task, value): # Null assertion
	
	return task.branch(1, True, True)

def assert_some(task, value): # Non-null assertion
	
	return value

std_assert = funcdef(
	assert_none,
	assert_some
)

def branch_none(task): # Unconditional branch
	
	return task.branch(1, False, True)

def branch_boolean(task, condition): # Conditional branch

	if not condition:
		return task.branch(1, True, True)

std_branch = funcdef(
	branch_none,
	branch_boolean
)

def constraint_boolean(task, constraint):
	
	name = task.instructions[0].label[0]
	if not constraint:
		value = task.values[name]
		task.restore(task.caller)
		task.error('CAST', name, str(value))
	elif task.op.label and task.op.label[0] != name: # Update type of checked value for subsequent constraints
		task.types[name].type = task.op.label[0]
		task.types[name].describe(task)

std_constraint = funcdef(
	constraint_boolean
)

#def event_none(task):

#	name = task.op.register
#	types, params = [descriptor.read(i).describe(task) for i in task.op.label[0::2]], task.op.label[1::2]
#	start = task.path
#	task.branch(0, True, True)
#	end = task.branch(0, True, True)
#	definition = event_method(task.instructions[start:end], params, types)
#	routine = task.values[name] if name in task.values and task.types[name].type == 'event' else eventdef(name)
#	routine.register(definition, types[0], tuple(types[1:-1]))
#	return routine

#std_event = funcdef('.event')
#std_event.retrieve(event_none)

#def function_none(task):
	
#	name = task.op.register
#	types, params = [descriptor.read(i).describe(task) for i in task.op.label[0::2]], task.op.label[1::2]
#	start, end = task.path, task.branch(0, True, True)
#	definition = function_method(task.instructions[start:end], params, types)
#	routine = task.values[name] if name in task.values and task.types[name].type == 'function' else funcdef(name)
#	routine.register(definition, types[0], tuple(types[1:]))
#	return routine

#std_function = funcdef('.function')
#std_function.retrieve(function_none)

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
		return sequence[int(index)]
	else:
		return task.error('INDX', index)

def index_list_slice(task, sequence, index):
	
	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return tuple(sequence[int(n)] for n in iter(index))
	else:
		return task.error('INDX', index)

def index_record_any(task, sequence, index):
	
	if index in sequence:
		return sequence[index]
	else:
		return task.error('INDX', index)

def index_record_slice(task, sequence, index):

	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		items = tuple(sequence.items())
		return dict(items[int(n)] for n in iter(index))
	else:
		return task.error('INDX', index)

def index_slice_integer(task, sequence, index):

	length = len(sequence)
	if -length <= index < length:
		return sequence[int(index)]
	else:
		return task.error('INDX', index)

def index_slice_slice(task, sequence, index):
	
	length = len(sequence)
	if (-length <= index.start < length) and (-length <= index.end < length):
		return tuple(sequence[int(n)] for n in iter(index))
	else:
		return task.error('INDX', index)

std_index = funcdef(
	index_string_integer,
	index_string_slice,
	index_list_integer,
	index_list_slice,
	index_record_any,
	index_record_slice,
	index_slice_integer,
	index_slice_slice
)

def iterator_sequence(task, sequence):
	
	return iter(sequence)

std_iterator = funcdef(
	iterator_sequence
)

def link_none(task):
	
	task.message('link', task.op.register + '.sph')
	return task.calls.recv()

std_link = funcdef(
	link_none
)

#def meta_string(task, string):

#	meta = module(string, meta = task.name)
#	offset = int(task.op.register) - 1
#	constants = len([item for item in task.values if item[0] == '&']) - 1
#	instructions, values, types = translator(meta, constants = constants).generate(offset = offset)
#	start = task.path
#	end = task.branch(0, True, False)
#	task.instructions[start + 1:end] = instructions
#	task.values.update(values)
#	task.types.update({k: v.describe(task) for k, v in types.items()})

#std_meta = funcdef('.meta')
#std_meta.retrieve(meta_string)

def next_any(task, iterator):
	
	try:
		return next(iterator)
	except StopIteration:
		task.values[task.op.args[0]] = None # Sanitise register
		return task.branch(1, False, True)

std_next = funcdef(
	next_any
)

def range_integer_integer_integer(task, x, y, z):

	return tuple(slice(x, y, z))

std_list = funcdef(
	range_integer_integer_integer
)

def return_none(task):
	
	if task.caller:
		task.restore(task.caller) # Restore namespace of calling routine
	else:
		task.path = 0 # End task
	return None # Returns null

def return_some(task, sentinel):
	
	task.properties = typedef(task.final)
	if task.caller:
		task.restore(task.caller) # Restore namespace of calling routine
	else:
		task.path = 0 # End task
	task.values[task.op.register] = sentinel # Different return address
	return sentinel

std_return = funcdef(
	return_none,
	return_some
)

#def type_type(task, supertype):
	
#	name, supername = task.op.register, supertype.name
#	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
#	type_tag.supertypes = [name] + super_tag.supertypes
#	start, end = task.path, task.branch(0, True, True)
#	instructions = task.instructions[start:end]
#	routine = typedef(name, supertype.supertypes, supertype.prototype)
#	if supername in aletheia.supertypes: # Built-in supertype
#		check = kadmos.generate_supertype(name, supername)
#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
#		instructions[1:1] = check
#		routine.register(type_method(instructions, name, super_tag), final_tag, (descriptor('untyped', prepare = True),))
#	else:
#		tree = supertype.tree.true
#		while tree: # Traverse down tree and copy all false leaves
#			key, value = tree.false.signature, tree.false.routine
#			definition = [instruction.rewrite(i, supername, name) for i in value.instructions] # Rewrite methods with own type name
#			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
#			routine.register(type_method(definition, name, key[0]), final_tag, key)
#			tree = tree.true
#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
#	return routine

#def type_type_any(task, supertype, prototype):
	
#	name, supername = task.op.register, supertype.name
#	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
#	type_tag.supertypes = [name] + super_tag.supertypes
#	start, end = task.path, task.branch(0, True, True)
#	instructions = task.instructions[start:end]
#	routine = typedef(name, supertype.supertypes, prototype)
#	if supername in aletheia.supertypes: # Built-in supertype
#		check = kadmos.generate_supertype(name, supername)
#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
#		instructions[1:1] = check
#		routine.register(type_method(instructions, name, super_tag), final_tag, (descriptor('untyped', prepare = True),))
#	else:
#		tree = supertype.tree.true
#		while tree: # Traverse down tree and copy all false leaves
#			key, value = tree.false.signature, tree.false.routine
#			definition = [instruction.rewrite(i, supername, name) for i in value.instructions] # Rewrite methods with own type name
#			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
#			routine.register(type_method(definition, name, key[0]), final_tag, key)
#			tree = tree.true
#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
#	return routine

#std_type = funcdef('.type')
#std_type.retrieve(type_type)
#std_type.retrieve(type_type_untyped)