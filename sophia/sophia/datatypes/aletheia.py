import json
from functools import reduce
from sys import stderr
from typing import Any, Callable, Self

from .iris import reference, std_stdin
from .mathos import real, slice
from ..internal.instructions import instruction
from ..internal.presets import DATATYPES, PROPERTIES, STDLIB_NAMES

with open('sophia/stdlib/kleio.json', 'r') as kleio:
	metadata = json.load(kleio)
del kleio

class type_property:
	"""
	Implements a type property.
	"""
	def __init__(
		self,
		name: str,
		value: Any = None,
		) -> None:
		
		self.name = name
		self.check = self.__check__ if name in type_property.builtins else self.__user__
		self.property = value

	def __eq__(
		self,
		other
		) -> bool:

		return self.name == other.name and self.property == other.property

	def __str__(self) -> str: return self.name

	def __user__(
		self,
		task,
		value: Any
		) -> None:
		
		task.caller = task.state()
		task.final = self.final
		task.values[self.name], task.types[self.name] = value, self.initial
		task.instructions = self.instructions
		task.path = 1

	def __check__(
		self,
		task,
		value: Any
		) -> None:

		return getattr(self, '__{0}__'.format(self.name))(task, value)

	def __any__(
		self,
		task,
		value: Any
		) -> bool:

		return True

	def __none__(
		self,
		task,
		value: Any
		) -> bool:

		return value is None

	def __some__(
		self,
		task,
		value: Any
		) -> bool:

		return value is not None

	def __routine__(
		self,
		task,
		value: Any
		) -> bool:

		return hasattr(value, '__call__')

	def __type__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, typedef)

	def __event__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, eventdef)

	def __function__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, funcdef)

	def __boolean__(
		self,
		task,
		value: Any
		) -> bool:

		return value is True or value is False

	def __number__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, real)

	def __integer__( # Safe to assume that value is of type number
		self,
		task,
		value: real
		) -> bool:

		return value % 1 == 0

	def __sequence__(
		self,
		task,
		value: Any
		) -> bool:

		return hasattr(value, '__iter__')

	def __string__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, str)

	def __list__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, tuple)

	def __record__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, dict)

	def __slice__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, slice)

	def __future__(
		self,
		task,
		value: Any
		) -> bool:

		return isinstance(value, reference)

	def __element__(
		self,
		task,
		value: Any
		) -> bool:

		if isinstance(value, dict):
			return all(self.property(task, i) for i in value.values())
		else:
			return all(self.property(task, i) for i in value)

	def __length__(
		self,
		task,
		value: Any
		) -> bool:

		return len(value) == self.property

	builtins = [
		'any',
		'none',
		'some',
		'routine',
		'type',
		'event',
		'function',
		'boolean',
		'number',
		'integer',
		'sequence',
		'string',
		'list',
		'record',
		'slice',
		'future',
		'element',
		'length'
	]

class typedef:
	"""
	Type descriptor that holds the properties of a given type.
	Believe it or not, this implementation sucks less than it did before.
	"""
	def __init__(
		self,
		supertype: Self | None = None,
		*methods: tuple[type_property | type, ...],
		prototype: Any = None
		) -> None:
		
		if supertype: # Duplicate typedef
			self.types = supertype.types.copy()
			self.prototype = supertype.prototype
		else:
			self.types = {}
			self.prototype = None
		if methods:
			self.types.update({i.name: i for i in methods})
		if prototype:
			self.prototype = prototype

	def __call__(self, task, value, *, write = True):
		"""
		Types do not use the same dispatch as other routines.
		Instead, a custom dispatch is performed based on the known
		properties of the argument's type.
		"""
		address, definition = task.op.address, task.signature[0]
		if definition < self: # Value is subtype
			check = True
		else:
			for item in self.types.values():
				if item not in definition.types.values() and not item.check(task, value):
					check = False
					break
			else:
				check = True
		if write:
			task.values[address] = check
			task.types[address] = typedef(std_boolean)
		return check

	def __eq__( # Implements equality
		self,
		other: Self
		) -> bool:

		return self.__dict__ == other.__dict__

	def __lt__( # Implements subtype relation
		self,
		other: Self
		) -> bool:
		
		return not bool([i for i in other.types.values() if i not in self.types.values()])

	def __gt__( # Implements negative subtype relation
		self,
		other: Self
		) -> bool:
		
		return bool([i for i in other.types.values() if i not in self.types.values()])

	#def __and__(self, other): # Implements type intersection

	#	if self.type != other.type:
	#		return None
	#	return typedef(self.type, self.__dict__ | other.__dict__)

	def __or__( # Implements type union / mutual supertype
		self,
		other: Self
		) -> Self:

		return typedef(None, *[i for i in self.types.values() if i in other.types.values()])

	def __str__(self) -> str:

		if not self.types:
			return '?'
		properties = []
		for item in self.types.values():
			if (name := item.name) in STDLIB_NAMES and name not in PROPERTIES:
				datatype = name # Get most specific data type
			else:
				properties.append('{0}:{1}'.format(name, item.property))
		return '.'.join([datatype] + properties)

	__repr__ = __str__

	def criterion( # Gets the most specific property that two typedefs don't share (non-commutative)
		self,
		other: Self
		) -> type_property | None:

		shared = [i for i in self.types.values() if i not in other.types.values()]
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
		*,
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
		self.arity = len(self.signature)

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

	def __bool__(self) -> bool: return False

	def __str__(self) -> str: return self.name

	def debug(
		self,
		level: int = 0
		) -> str:
		
		print(('. ' * level) + str(self), file = stderr)

class function_method(method): pass

class event_method(method):
	
	def __init__(
		self,
		body: list[instruction] | Callable,
		names: list[str],
		types: list[typedef],
		) -> None:

		super().__init__(body, names[:-1], types[:-1], user = True)
		self.message = names[-1]
		self.check = types[-1]

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
		address, signature, arity = task.op.address, task.signature, task.op.arity
		instance = self.true if signature else self.false
		while instance: # Traverse tree; terminates upon reaching leaf node
			instance = instance.true if instance.index < arity and instance.check(signature) else instance.false
		if instance is None or instance.arity != arity:
			task.handler.error('DISP', task.op.name, signature)
		for i, item in enumerate(signature): # Verify type signature
			if item > instance.signature[i]:
				task.handler.error('DISP', task.op.name, signature)
		final = instance.final
		value = instance.routine(task, *args)
		task.values[address] = value
		if value is None: # Null return override
			task.types[address] = std_none
		elif final.types:
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

		return self.property in signature[self.index].types.values()

	def collect(self) -> list[method]: # Collect all leaf nodes (order not important)

		x, y = self.true, self.false
		x = x.collect() if x else ([] if x is None else [x])
		y = y.collect() if y else ([] if y is None else [y])
		return x + y

	def debug(
		self,
		level: int = 0
		) -> None:
	
		print(('. ' * level) + str(self), file = stderr)
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

cls_any			= type_property('any')
cls_none		= type_property('none')
cls_some		= type_property('some')
cls_routine		= type_property('routine')
cls_type		= type_property('type')
cls_event		= type_property('event')
cls_function	= type_property('function')
cls_boolean		= type_property('boolean')
cls_number		= type_property('number')
cls_integer		= type_property('integer')
cls_sequence	= type_property('sequence')
cls_string		= type_property('string')
cls_list		= type_property('list')
cls_record		= type_property('record')
cls_slice		= type_property('slice')
cls_future		= type_property('future')

def cls_element(
	element: typedef
	) -> type_property:
	"""
	Closure for generating element properties.
	"""
	return type_property('element', element)

def cls_length(
	length: int
	) -> type_property:
	"""
	Closure for generating length properties.
	"""
	return type_property('length', length)

std_any			= typedef(None, cls_any)
std_none		= typedef(std_any, cls_none)
std_some		= typedef(std_any, cls_some)
std_routine		= typedef(std_some, cls_routine)
std_type		= typedef(std_routine, cls_type, prototype = std_any)
std_event		= typedef(std_routine, cls_event)
std_function	= typedef(std_routine, cls_function)
std_boolean		= typedef(std_some, cls_boolean, prototype = False)
std_number		= typedef(std_some, cls_number, prototype = real())
std_integer		= typedef(std_number, cls_integer) # Inherits prototype from std_number
std_sequence	= typedef(std_some, cls_sequence)
std_string		= typedef(std_sequence, cls_string, prototype = '')
std_list		= typedef(std_sequence, cls_list, prototype = ())
std_record		= typedef(std_sequence, cls_record, prototype = {})
std_slice		= typedef(std_sequence, cls_slice, prototype = slice())
std_future		= typedef(std_some, cls_future, prototype = std_stdin)

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
	datatype = types[name]
	properties = []
	if cls_sequence in datatype.types.values():
		if name == 'string':
			element = std_string
		elif name == 'slice':
			element = std_integer
		else:
			element = infer_element(value)
		properties.append(cls_element(element))
		properties.append(cls_length(len(value)))
	definition = typedef(types[name], *properties)
	return definition

def infer_element( # Infers element type of value
	value: Any
	) -> typedef:

	if isinstance(value, dict):
		return reduce(typedef.__or__, [infer(i) for i in value.values()], typedef(std_any))
	else:
		return reduce(typedef.__or__, [infer(i) for i in value], typedef(std_any))

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

#class cls_any:

	#@classmethod
	#def __null__(cls, value): return

	#@classmethod
	#def __type__(cls, value): return

	#@classmethod
	#def __event__(cls, value): return

	#@classmethod
	#def __function__(cls, value): return

	#@classmethod
	#def __boolean__(cls, value): return

	#@classmethod
	#def __number__(cls, value): return

	#@classmethod
	#def __string__(cls, value): return

	#@classmethod
	#def __list__(cls, value): return

	#@classmethod
	#def __record__(cls, value): return

	#@classmethod
	#def __slice__(cls, value): return

	#@classmethod
	#def __future__(cls, value): return

#class cls_none(cls_any): # Null type

#class cls_some(cls_any): # Non-null type

#class cls_routine(cls_some):

#class cls_type(cls_routine):

#class cls_event(cls_routine):

#class cls_function(cls_routine):

#class cls_boolean(cls_some):

#	@classmethod
#	def __boolean__(cls, value): return value

#	@classmethod
#	def __number__(cls, value): return value != 0

#	@classmethod
#	def __string__(cls, value): return value != ''

#	@classmethod
#	def __list__(cls, value): return value != []

#	@classmethod
#	def __record__(cls, value): return value != {}

#	@classmethod
#	def __slice__(cls, value): return len(value) != 0

#class cls_number(cls_some):

#	@classmethod
#	def __boolean__(cls, value): return real(int(value))

#	@classmethod
#	def __number__(cls, value): return value

#	@classmethod
#	def __string__(cls, value): return real.read(value)

#	@classmethod
#	def __future__(cls, value): return real(value.pid)

#class cls_integer(cls_number):

#class cls_sequence(cls_some):

#class cls_string(cls_sequence):

#	@classmethod
#	def __null__(cls, value): return 'null'

#	@classmethod
#	def __type__(cls, value): return value.name

#	@classmethod
#	def __event__(cls, value): return value.name

#	@classmethod
#	def __function__(cls, value): return value.name

#	@classmethod
#	def __boolean__(cls, value): return 'true' if value else 'false'

#	@classmethod
#	def __number__(cls, value): return str(value)

#	@classmethod
#	def __string__(cls, value): return value

#	#@classmethod
#	#def __list__(cls, value): return '[' + ', '.join([cast_std_some(i, cls) for i in value]) + ']'

#	#@classmethod
#	#def __record__(cls, value): return '[' + ', '.join([cast_std_some(k, cls) + ': ' + cast_std_some(v, cls) for k, v in value.items()]) + ']'

#	@classmethod
#	def __slice__(cls, value): return '{0}:{1}:{2}'.format(value.start, value.stop, value.step)

#	@classmethod
#	def __future__(cls, value): return value.name

#class cls_list(cls_sequence):

#	@classmethod
#	def __string__(cls, value): return tuple(i for i in value)

#	@classmethod
#	def __list__(cls, value): return value

#	@classmethod
#	def __record__(cls, value): return tuple(value.items())

#	@classmethod
#	def __slice__(cls, value): return tuple(value)

#class cls_record(cls_sequence):

#class cls_slice(cls_sequence):

#class cls_future(cls_some):