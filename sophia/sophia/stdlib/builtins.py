'''
Built-in functions.
'''
from functools import reduce
from math import copysign

from ..datatypes.aletheia import funcdef, typedef
from ..datatypes.mathos import real

def abs_number(task, value):

	return value if value >= 0 else -value

std_abs = funcdef(
	abs_number
)

#def cast_any_type(task, value, target):
	
#	try:
#		result = getattr(types.types['__{0}__'.format(types.names[type(value).__name__])])(value)
#	except KeyError:
#		return task.error('CAST', target.name, value)
#	if result is None:
#		return task.error('CAST', target.name, value)
#	else:
#		return result

#std_cast = funcdef(
#	cast_any_type
#)

def ceiling_number(task, value):

	return value.__ceil__() # Handled by real

std_ceiling = funcdef(
	ceiling_number
)

#def dispatch_function_list(task, routine, signature):
	
#	tree = routine.tree.true if signature else routine.tree.false
#	while tree:
#		try:
#			tree = tree.true if tree.op(signature[tree.index]) else tree.false
#		except IndexError:
#			tree = tree.false
#	try:
#		if tree is None:
#			raise KeyError
#		instance, final, result = tree.routine, tree.final, tree.signature
#		for i, item in enumerate(signature): # Verify type signature
#			if not item < result[i]:
#				raise KeyError
#	except (IndexError, KeyError):
#		return task.error('DISP', routine.name, signature)
#	new = funcdef(routine.name)
#	try:
#		definition = function_method(instance.instructions, [routine.name] + instance.params, [final] + list(signature))
#		new.register(definition, final, signature)
#	except AttributeError: # Built-ins
#		new.register(instance, final, signature)
#	return new

#std_dispatch = funcdef('dispatch')
#std_dispatch.retrieve(dispatch_function_list)

def error_string(task, status):
	
	task.handler.error('USER', status)

std_error = funcdef(
	error_string
)

def floor_number(task, value):

	return value.__floor__() # Handled by real

std_floor = funcdef(
	floor_number
)

#def filter_function_list(task, routine, target):

#	result, member, length = [], task.signature[1].member, 0
#	for value in target: # Dispatch and execute for each element of the list
#		signature = descriptor(member).complete(types.infer(value), value).describe(task)
#		tree = routine.tree.true if target else routine.tree.false
#		while tree: # Traverse tree; terminates upon reaching leaf node
#			tree = tree.true if tree.index == 0 and tree.op(signature) else tree.false
#		if (tree is None) or len(tree.signature) > 1 or not (signature < tree.signature[0]):
#			return task.error('DISP', routine.name, signature)
#		instance, signature = tree.routine, tree.signature
#		if 'boolean' not in tree.final.supertypes:
#			return task.error('FLTR', routine.name, value)
#		if isinstance(instance, function_method):
#			caller = task.caller
#			instance(task, value)
#			check = task.run() # WARNING: Recursive runtime
#			task.caller = caller
#		else: # Built-ins
#			check = instance(task, value)
#		if check:
#			result.append(value)
#			length = length + 1
#	task.properties.member = member # Member type remains constant
#	task.properties.length = length
#	return result

#std_filter = funcdef('filter')
#std_filter.retrieve(filter_function_list)

def format_string_list(task, string, args):

	return string.format(*args)

std_format = funcdef(
	format_string_list
)

def hash_any(task, value):
	"""
	THIS HASH IS NOT CRYPTOGRAPHICALLY SECURE.
	"""
	return real(hash(value))

std_hash = funcdef(
	hash_any
)

def if_none(task):
	"""
	Unconditional branch.
	"""
	return task.branch(1, False, True)

def if_boolean(task, condition):
	"""
	Conditional branch.
	"""
	if not condition:
		return task.branch(1, True, True)

std_if = funcdef(
	if_none,
	if_boolean
)

def input_string(task, value):
	
	task.message('read', value)
	return task.calls.recv()

std_input = funcdef(
	input_string
)

def join_list_string(task, sequence, joiner):

	return joiner.join(sequence)

std_join = funcdef(
	join_list_string
)

def length_string(task, sequence):
	
	return len(sequence)

def length_list(task, sequence):
	
	return len(sequence)

def length_record(task, sequence):
	
	return len(sequence)

def length_slice(task, sequence):
	
	return len(sequence)

std_length = funcdef(
	length_string,
	length_list,
	length_record,
	length_slice
)

#def map_function_list(task, routine, target):

#	result, final, member = [], [], task.signature[1].member
#	for value in target: # Dispatch and execute for each element of the list
#		signature = descriptor(member).complete(types.infer(value), value).describe(task)
#		tree = routine.tree.true if target else routine.tree.false
#		while tree: # Traverse tree; terminates upon reaching leaf node
#			tree = tree.true if tree.index == 0 and tree.op(signature) else tree.false
#		if (tree is None) or len(tree.signature) > 1 or not (signature < tree.signature[0]):
#			return task.error('DISP', routine.name, signature)
#		instance, signature = tree.routine, tree.signature
#		final.append(tree.final)
#		if isinstance(instance, function_method):
#			caller = task.caller
#			instance(task, value)
#			result.append(task.run()) # WARNING: Recursive runtime
#			task.caller = caller
#		else: # Built-ins
#			result.append(instance(task, value))
#	final = reduce(descriptor.mutual, final) # Use the return type of the map, not the inferred type of the elements
#	task.properties.member = final.type
#	return result

#std_map = funcdef('map')
#std_map.retrieve(map_function_list)

#def namespace_none(task): # Do not let the user read working registers

#	return {k: v for k, v in task.values.items() if k not in builtins} # ABOVE COMMENT IS LYING

#std_namespace = funcdef('namespace')
#std_namespace.retrieve(namespace_none)

def print_string(task, value):

	print(value)
	return value

std_print = funcdef(
	print_string
)

#def reduce_function_list(task, routine, target):
	
#	try:
#		x, member = target[0], task.signature[1].member
#		x_type = descriptor(member).complete(types.infer(x), x).describe(task)
#	except IndexError:
#		return task.error('RDCE')
#	for y in target[1:]: # Dispatch and execute for each element of the list
#		y_type = descriptor(member).complete(types.infer(y), y).describe(task)
#		xy = [x_type, y_type]
#		tree = routine.tree.true if target else routine.tree.false
#		while tree: # Traverse tree; terminates upon reaching leaf node
#			try:
#				tree = tree.true if tree.op(xy[tree.index]) else tree.false
#			except IndexError:
#				tree = tree.false
#		try:
#			if tree is None:
#				raise KeyError
#			instance, final, signature = tree.routine, tree.final, tree.signature
#			for i, item in enumerate(xy): # Verify type signature
#				if not item < signature[i]:
#					raise KeyError
#		except (IndexError, KeyError):
#			return task.error('DISP', routine.name, xy)
#		if isinstance(instance, function_method):
#			caller = task.caller
#			instance(task, x, y)
#			x = task.run() # WARNING: Recursive runtime
#			task.caller = caller
#		else: # Built-ins
#			x = instance(task, x, y)
#		x_type, y_type = final, member
#	task.properties.merge(final)
#	return x

#std_reduce = funcdef('reduce')
#std_reduce.retrieve(reduce_function_list)

def return_none(task):
	
	if task.caller:
		task.restore() # Restore namespace of calling routine
	else:
		task.path = 0 # End task
	return None # Returns null

def return_any(task, sentinel):
	
	task.properties = typedef(task.final)
	if task.caller:
		task.restore() # Restore namespace of calling routine
	else:
		task.path = 0 # End task
	task.values[task.op.address] = sentinel # Different return address
	return sentinel

std_return = funcdef(
	return_none,
	return_any
)

def reverse_slice(task, value):
		
	return slice(value.end, value.start, -value.step)

std_reverse = funcdef(
	reverse_slice
)

def round_number(task, value):

	return round(value)

std_round = funcdef(
	round_number
)

def sign_number(task, value):

	return real() if value == 0 else real(int(copysign(1, value)))

std_sign = funcdef(
	sign_number
)

def signature_function_list(task, routine, signature):

	while routine: # Just do dispatch
		routine = routine.true if routine.index < task.op.arity and routine.check(signature) else routine.false
	if routine is None or routine.arity != len(signature):
		return False
	for i, item in enumerate(signature):
		if item > routine.signature[i]:
			return False
	return True

std_signature = funcdef(
	signature_function_list
)

def split_string_string(task, string, separator):

	return tuple(string.split(separator))

std_split = funcdef(
	split_string_string
)

def sum_list(task, sequence):

	return real(sum(sequence))

def sum_slice(task, sequence):

	return real(sum(sequence))

std_sum = funcdef(
	sum_list,
	sum_slice
)

def typeof_any(task, value):
	
	return typedef(task.signature[0])

std_typeof = funcdef(
	typeof_any
)