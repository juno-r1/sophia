import json
from dataclasses import dataclass
from sys import stderr
from typing import Any, Callable, Self

from .iris import reference, std_stdin
from .mathos import real, slice
from ..internal.instructions import instruction
from ..internal.presets import DATATYPES

with open('sophia/stdlib/kleio.json', 'r') as kleio:
	metadata = json.load(kleio)
del kleio

@dataclass(repr = False, frozen = True)
class type_method:
	"""
	Implements a user-defined type property.
	"""
	instructions: list[instruction]
	name: str
	initial: Any # typedef
	final: Any # typedef

	def __call__( # Type checks only take 1 argument
		self,
		task,
		value: Any
		) -> None:
		
		task.caller = task.state()
		task.final = self.final
		task.values[self.name], task.types[self.name] = value, self.initial
		task.instructions = self.instructions
		task.path = 1

	def __str__(self) -> str: return str(self.final)

class typedef:
	"""
	Type descriptor that holds the properties of a given type.
	Believe it or not, this implementation sucks less than it did before.
	"""
	def __init__(
		self,
		supertype: Self | None = None,
		*methods: tuple[type_method | type, ...],
		prototype: Any = None
		) -> None:
		
		if supertype: # Duplicate typedef
			self.types = supertype.types.copy()
			self.prototype = supertype.prototype
		else:
			self.types = []
			self.prototype = None
		if methods:
			self.types.extend(methods)
		if prototype:
			self.prototype = prototype

	def __call__(self, task, value):
		"""
		Types do not use the same dispatch as other routines.
		Instead, a custom dispatch is performed based on the known
		properties of the argument's type.
		"""
		address, definition = task.op.address, task.signature[0]
		if definition < self: # Value is subtype
			task.values[address] = value
			task.types[address] = typedef(self)
			return value
		for item in self.types:
			if item not in definition.types and not item(task, value):
				return task.error('CAST', item.name, value)
		task.values[address] = value
		task.types[address] = typedef(self)
		return value

	def __eq__( # Implements equality
		self,
		other: Self
		) -> bool:

		return self.__dict__ == other.__dict__

	def __lt__( # Implements subtype relation
		self,
		other: Self
		) -> bool:
		
		return not bool([i for i in other.types if i not in self.types])

	def __gt__( # Implements negative subtype relation
		self,
		other: Self
		) -> bool:

		return bool([i for i in other.types if i not in self.types])

	#def __and__(self, other): # Implements type intersection

	#	if self.type != other.type:
	#		return None
	#	return typedef(self.type, self.__dict__ | other.__dict__)

	def __or__( # Implements type union / mutual supertype
		self,
		other: Self
		) -> Self:

		return typedef(None, *[i for i in self.types if i in other.types])

	def __str__(self) -> str:

		return '.'.join(getattr(item, 'name', item.__name__) for item in self.types)

	__repr__ = __str__

	def criterion( # Gets the most specific property that two typedefs don't share (non-commutative)
		self,
		other: Self
		) -> type_method | None:

		shared = [i for i in self.types if i not in other.types]
		return shared[-1] if shared else None

	@classmethod
	def read( # Creates a typedef from a type descriptor
		cls,
		descriptor: str
		) -> Self:

		if descriptor == '?':
			return cls() # Infer return type
		attributes = descriptor.split('.')
		datatype = types[attributes[0]]
		methods = []
		for item in attributes[1:]:
			name, value = item.split(':')
			try:
				value = int(value)
			except ValueError:
				value = types[value]
			methods.append(properties[name](value))
		return cls(datatype, *methods) # Create new typedef from base datatype

class method:
	"""
	Implements a method. This functions as the leaf node of a multimethod's
	dispatch tree.
	"""
	def __init__(
		self,
		body: list[instruction] | Callable,
		names: list[str],
		types: list[typedef],
		user = False
		) -> None:
		
		if user:
			self.instructions = body
			self.routine = self
		else:
			self.instructions = None
			self.routine = body
		self.name = names[0]
		self.params = names[1:]
		self.final = types[0]
		self.signature = types[1:]

	def __bool__(self) -> bool: return False

	def __str__(self) -> str: return self.name

	def debug(
		self,
		level: int = 0
		) -> str:
		
		print(('  ' * level) + str(self), file = stderr)

class function_method(method):

	def __call__(
		self,
		task,
		*args: tuple
		) -> None:

		task.caller = task.state()
		task.final = self.final
		task.values = task.values | dict(zip(self.params, args))
		task.types = task.types | dict(zip(self.params, self.signature))
		task.instructions = self.instructions
		task.path = 1

class event_method(method):
	
	def __init__(
		self,
		body: list[instruction] | Callable,
		names: list[str],
		types: list[typedef],
		) -> None:

		super().__init__(body, names[:-1], types[:-1], user = True)
		self.event_name = names[-1]
		self.event_type = types[-1]

	def __call__(
		self,
		task,
		*args: tuple
		) -> reference:
		
		task.message('future', self, args, task.values[self.name])
		task.properties = typedef(std_future)
		return task.calls.recv()

class multimethod:
	"""
	Implements a multimethod.
	Multimethods enable multiple dispatch on functions. Functions dispatch for
	the arity and types of their arguments. The precedence for dispatch is
	left-to-right, then most to least specific type.

	Dispatch is implemented using a singly linked binary search
	tree. It is only ever necessary to traverse downward.
	"""

	def __init__(self):

		self.true = None # Path or method if true
		self.false = None # Path or method if false
		self.property = cls_any # Distinguishing type property
		self.index = 0 # Signature index

	def __call__(self, task, *args):
		"""
		Multiple dispatch algorithm, with help from Julia:
		https://github.com/JeffBezanson/phdthesis
		Binary search tree yields closest key for method, then key is verified.
		"""
		address, signature = task.op.address, task.signature
		instance = self.true if signature else self.false
		while instance: # Traverse tree; terminates upon reaching leaf node
			instance = instance.true if instance.index < task.op.arity and instance.check(signature) else instance.false
		if instance is None:
			return task.error('DISP', task.op.name, signature)
		try:
			for i, item in enumerate(signature): # Verify type signature
				if item > instance.signature[i]:
					raise IndexError
		except IndexError:
			return task.error('DISP', task.op.name, signature)
		final = instance.final
		value = instance.routine(task, *args)
		if final == std_none: # Null return; write to address 0
			task.values['0'] = None
			task.types['0'] = std_none
		else:
			task.values[address] = value
			if final.types:
				task.types[address], task.properties = task.properties or final, None
			else:
				task.types[address] = infer(value)
		return value

	def __bool__(self): return True

	def __str__(self): return '{0} {1}'.format(self.property.name, self.index)

	def set( # Set check attributes
		self,
		true: method,
		false: method,
		check: typedef,
		index: int,
		) -> Self:

		self.true = true
		self.false = false
		self.property = check
		self.index = index
		return self

	def extend( # Add node to tree
		self,
		new: method
		) -> None:
		
		if not new.signature: # Zero-argument method
			self.false = new
			return
		if self.true is None: # Empty tree
			self.true = new
			return
		branch, arity = self, len(new.signature)
		while branch: # Traverse tree to closest leaf node
			check = branch.index < arity and branch.check(new.signature)
			head, branch = branch, branch.true if check else branch.false
		if check:
			head.true = head.build(new, branch)
		else:
			head.false = head.build(new, branch)

	def build( # Reorder branch node with new method
		self,
		new: method,
		other: method
		) -> Self | method:
		
		if new.signature == other.signature: # If signatures match, end early
			return new
		new_length, other_length = len(new.signature), len(other.signature)
		node = type(self)() # Get new instance of subclass
		if new_length > other_length:
			return node.set(new, other, cls_any, other_length)
		elif new_length < other_length:
			return node.set(other, new, cls_any, new_length)
		else: # Prioritise unmatched arity over unmatched signatures
			for i in range(new_length): # Signatures guaranteed not to match
				new_item, other_item = new.signature[i], other.signature[i]
				new_criterion = new_item.criterion(other_item)
				other_criterion = other_item.criterion(new_item)
				if new_criterion is not None: # If new has a property that other doesn't
					return node.set(new, other, new_criterion, i)
				elif other_criterion is not None: # If other has a property that new doesn't, just in case
					return node.set(other, new, other_criterion, i)
		return node

	def check( # Universal dispatch check exploiting properties of structural typing
		self,
		signature: list[typedef]
		) -> bool: 

		return self.property in signature[self.index].types

	def collect(self) -> list[method]: # Collect all leaf nodes (order not important)

		x, y = self.true, self.false
		x = x.collect() if x else ([] if x is None else [x])
		y = y.collect() if y else ([] if y is None else [y])
		return x + y

	def debug(
		self,
		level: int = 0
		) -> None:
	
		print(('  ' * level) + str(self), file = stderr)
		if self:
			if self.true is not None:
				self.true.debug(level + 1)
			if self.false is not None:
				self.false.debug(level + 1)
		
class funcdef(multimethod):
	"""
	Accepts zero or more callables as initial methods.
	These are assumed to be built-ins. To create a user-defined function,
	do not specify any initial methods.
	"""
	def __init__(
		self,
		*methods: tuple[Callable, ...]
		) -> None:

		super().__init__()
		for item in methods:
			data = metadata[item.__name__] # Retrieve method signature from Kleio
			names = [item.__name__] + [str(i) for i in range(len(data['signature']))]
			types = [typedef.read(data['final'])] + [typedef.read(i) for i in data['signature']]
			self.extend(function_method(item, names, types))

class eventdef(multimethod): pass

"""
Built-in types and properties.
Types are expressed by a Boolean predicate which is true for that type's
set of values. This predicate also functions as a type check.
"""

class cls_any:
	"""
	Base template for built-in types, equivalent to none | some.
	"""
	name = 'any'
	data = object, type(None)

	def __new__( # Type check constructor disguised as an object constructor
		cls,
		task,
		value: Any
		) -> bool:

		return True

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

std_any = typedef(None, cls_any)

class cls_none(cls_any): # Null type
	
	name = 'none'
	data = type(None)

	def __new__(
		cls,
		task,
		value: Any
		) -> bool:

		return value is None

std_none = typedef(std_any, cls_none)

class cls_some(cls_any): # Non-null type
	
	name = 'some'
	data = object

	def __new__(
		cls,
		task,
		value: Any
		) -> bool:
		
		return isinstance(value, cls.data)

std_some = typedef(std_any, cls_some)

class cls_routine(cls_some):
	
	name = 'routine'
	data = funcdef, eventdef, typedef

std_routine = typedef(std_some, cls_routine)

class cls_type(cls_routine):
	
	name = 'type'
	data = typedef

std_type = typedef(std_routine, cls_type, prototype = std_any)

class cls_event(cls_routine):
	
	name = 'event'
	data = eventdef

std_event = typedef(std_routine, cls_event)

class cls_function(cls_routine):
	
	name = 'function'
	data = funcdef

std_function = typedef(std_routine, cls_function)

class cls_boolean(cls_some):
	
	name = 'boolean'
	data = bool

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

std_boolean = typedef(std_some, cls_boolean, prototype = False)

class cls_number(cls_some):
	
	name = 'number'
	data = real

	@classmethod
	def __boolean__(cls, value): return real(int(value))

	@classmethod
	def __number__(cls, value): return value

	@classmethod
	def __string__(cls, value): return real.read(value)

	@classmethod
	def __future__(cls, value): return real(value.pid)

std_number = typedef(std_some, cls_number, prototype = real())

class cls_integer(cls_number):

	name = 'integer'

	def __new__( # Sophia now does these sequentially, so no need to check the data type
		cls,
		task,
		value: real
		) -> bool:

		return value % 1 == 0

std_integer = typedef(std_number, cls_integer) # Inherits prototype from std_number

class cls_sequence(cls_some):
	
	name = 'sequence'
	data = str, list, dict, slice

std_sequence = typedef(std_some, cls_sequence)

class cls_string(cls_sequence):
	
	name = 'string'
	data = str

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

	#@classmethod
	#def __list__(cls, value): return '[' + ', '.join([cast_std_some(i, cls) for i in value]) + ']'

	#@classmethod
	#def __record__(cls, value): return '[' + ', '.join([cast_std_some(k, cls) + ': ' + cast_std_some(v, cls) for k, v in value.items()]) + ']'

	@classmethod
	def __slice__(cls, value): return '{0}:{1}:{2}'.format(value.start, value.stop, value.step)

	@classmethod
	def __future__(cls, value): return value.name

std_string = typedef(std_sequence, cls_string, prototype = '')

class cls_list(cls_sequence):
	
	name = 'list'
	data = tuple

	@classmethod
	def __string__(cls, value): return tuple(i for i in value)

	@classmethod
	def __list__(cls, value): return value

	@classmethod
	def __record__(cls, value): return tuple(value.items())

	@classmethod
	def __slice__(cls, value): return tuple(value)

std_list = typedef(std_sequence, cls_list, prototype = ())

class cls_record(cls_sequence):
	
	name = 'record'
	data = dict

std_record = typedef(std_sequence, cls_record, prototype = {})

class cls_slice(cls_sequence):
	
	name = 'slice'
	data = slice
	
std_slice = typedef(std_sequence, cls_slice, prototype = slice())

class cls_future(cls_some):
	
	name = 'future'
	data = reference

std_future = typedef(std_some, cls_future, prototype = std_stdin)

class generator(type):
	"""
	Metaclass that generates type properties.
	"""
	def __new__(
		meta,
		name,
		value
		) -> type:

		return type(name, (), {'__new__': properties[name], '__eq__': meta.eq, 'property': value})

	@classmethod
	def eq(
		cls,
		other
		) -> bool:

		return cls.__new__ is other.__new__ and cls.property == other.property

	@classmethod
	def element(
		cls,
		task,
		value: Any,
		) -> bool:

		return all(cls.property(i) for i in value)
		
	@classmethod
	def length(
		cls,
		task,
		value: Any,
		) -> bool:

		return len(value) == cls.property

	properties = {
		'element': element,
		'length': length
	}

def cls_element(
	element: typedef
	) -> type:

	return generator('element', element)

def cls_length(
	length: int
	) -> type:

	return generator('length', length)

"""
Type inference and internals.
"""

def infer( # Infers typedef of value
	value: Any
	) -> typedef:
	
	name = type(value).__name__
	name = DATATYPES[name] if name in DATATYPES else 'any'
	if name == 'number' and value % 1 == 0:
		return typedef(std_integer)
	definition = typedef(types[name])
	# Add property inferences later
	return definition

#def infer_type(value): # Infers type of value

#	name = type(value).__name__
#	if name in names:
#		name = names[name]
#		return 'integer' if name == 'number' and value % 1 == 0 else name
#	else:
#		return 'untyped'

#def infer_element(value): # Infers element type of value
	
#	try:
#		return reduce(descriptor.__or__, [infer_type(item) for item in value.values()]) if value else 'untyped'
#	except AttributeError:
#		return reduce(descriptor.__or__, [infer_type(item) for item in value]) if value else 'untyped'

types = {
	'any': std_any,
	'none': std_none,
	'some': std_some,
	'routine': std_routine,
	'type': std_type,
	'event': std_event,
	'function': std_function,
	'boolean': std_boolean,
	'number': std_number,
	'integer': std_integer,
	'sequence': std_sequence,
	'string': std_string,
	'list': std_list,
	'record': std_record,
	'slice': std_slice,
	'future': std_future
}
properties = {
	'element': cls_element,
	'length': cls_length
}
del std_stdin # stdlib.arche shouldn't find this yet