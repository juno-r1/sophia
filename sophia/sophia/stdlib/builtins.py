'''
Built-in functions.
'''
import re
from math import copysign

from . import casts
from ..datatypes import aletheia
from ..datatypes.aletheia import funcdef, typedef
from ..datatypes.mathos import real
from ..internal.presets import DATATYPES

def abs_number(task, value):

	return value if value >= 0 else -value

std_abs = funcdef(
	abs_number
)

def cast_any_type(task, value, routine):
	
	for item in routine.types[::-1]:
		if item.name in DATATYPES.values():
			return casts.cast(value, item.name)
	else:
		return None
#	try:
#		result = getattr(types.types['__{0}__'.format(types.names[type(value).__name__])])(value)
#	except KeyError:
#		return task.error('CAST', target.name, value)
#	if result is None:
#		return task.error('CAST', target.name, value)
#	else:
#		return result

std_cast = funcdef(
	cast_any_type
)

def ceiling_number(task, value):

	return value.__ceil__() # Handled by real

std_ceiling = funcdef(
	ceiling_number
)

def dispatch_function_list(task, routine, signature):
	
	arity = len(signature)
	instance = routine.true if signature else routine.false
	while instance: # Traverse tree; terminates upon reaching leaf node
		instance = instance.true if instance.index < arity and instance.check(signature) else instance.false
	if instance is None or instance.arity != arity:
		return None
	for i, item in enumerate(signature): # Verify type signature
		if item > instance.signature[i]:
			return None
	new = funcdef()
	new.extend(instance)
	return new

std_dispatch = funcdef(
	dispatch_function_list
)

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

def filter_function_list(task, routine, sequence):

	result, element = [], (task.signature[1]['element'] or aletheia.infer(sequence)['element']).property
	instance = routine.true
	while instance: # Traverse tree; terminates upon reaching leaf node
		instance = instance.true if instance.index == 0 and instance.check([element]) else instance.false
	if (instance is None or \
		instance.arity != 1 or \
		element > instance.signature[0] or \
		instance.final > aletheia.std_boolean):
		return None # Verify type signature
	for item in sequence:
		if instance.instructions:
			caller = task.call()
			instance(task, item)
			check = task.run() # WARNING: Recursive runtime
			task.restore(caller)
		else: # Built-ins
			check = instance(task, item)
		if check:
			result.append(item)
	return tuple(result)

def filter_type_list(task, routine, sequence):
	
	return tuple(i for i in sequence if routine(task, i))

std_filter = funcdef(
	filter_function_list,
	filter_type_list
)

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

def map_function_list(task, routine, sequence):

	result, element = [], (task.signature[1]['element'] or aletheia.infer(sequence)['element']).property
	instance = routine.true
	while instance: # Traverse tree; terminates upon reaching leaf node
		instance = instance.true if instance.index == 0 and instance.check([element]) else instance.false
	if (instance is None or \
		instance.arity != 1 or \
		element > instance.signature[0]):
		return None # Verify type signature
	for item in sequence:
		if instance.instructions:
			caller = task.call()
			instance(task, item)
			result.append(task.run()) # WARNING: Recursive runtime
			task.restore(caller)
		else: # Built-ins
			result.append(instance(task, item))
	return tuple(result)

def map_type_list(task, routine, sequence):
	
	return tuple(routine(task, i) for i in sequence)

std_map = funcdef(
	map_function_list,
	map_type_list
)

def namespace_none(task):
	"""
	Retrieves the current namespace as a record, excluding internal registers.
	"""
	return {k: v for k, v in task.values.items() if not re.fullmatch(r'[-0123456789]+', k)}

std_namespace = funcdef(
	namespace_none
)

def print_string(task, value):

	print(value)
	return value

std_print = funcdef(
	print_string
)

def reduce_function_list(task, routine, sequence):
	
	if not sequence:
		return None
	if len(sequence) == 1:
		return sequence[0]
	left, element = sequence[0], (task.signature[1]['element'] or aletheia.infer(sequence)['element']).property
	instance = routine.true
	while instance: # Traverse tree; terminates upon reaching leaf node
		instance = instance.true if (0 <= instance.index < 2) and instance.check([element, element]) else instance.false
	if (instance is None or \
		instance.arity != 2 or \
		element > instance.signature[0] or \
		element > instance.signature[1]):
		return None # Verify type signature
	for right in sequence[1:]:
		if instance.instructions:
			caller = task.call()
			instance(task, left, right)
			left = task.run() # WARNING: Recursive runtime
			task.restore(caller)
		else: # Built-ins
			left = instance(task, left, right)
	return left

std_reduce = funcdef(
	reduce_function_list
)

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