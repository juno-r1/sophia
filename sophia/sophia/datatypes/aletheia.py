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

@dataclass(repr = False)
class type_method:
	"""
	Implements a user-defined type method.
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

	def __str__(self) -> str: return self.name

class typedef:
	"""
	Type descriptor that holds the properties of a given type.
	Believe it or not, this implementation sucks less than it did before.
	"""
	def __init__(
		self,
		supertype: Self | None = None,
		method: type_method | type | None = None,
		*,
		prototype: Any = None
		) -> None:
		
		if supertype: # Duplicate typedef
			self.types = supertype.types.copy()
			self.properties = supertype.properties.copy()
			self.prototype = supertype.prototype
		else:
			self.types = []
			self.properties = {}
			self.prototype = None
		if method:
			self.types.append(method)
		if prototype:
			self.prototype = prototype

	def __call__(self, task, signature):
		"""
		Types do not use the same dispatch as other routines.
		Instead, a custom dispatch is performed based on the known
		properties of the argument's type.
		"""
		pass

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

	##def __or__(self, other): # Implements type union / mutual supertype
		
	##	return descriptor(None, **{k: v for k, v in self.__dict__.items() if k in other.__dict__ and other.__dict__[k] == v})

	def __str__(self) -> str:

		return '.'.join(item.name for item in self.types)

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
		properties = descriptor.split('.')
		datatype = properties[0]
		definition = cls(types[datatype]) # Create new typedef from base datatype
		for item in properties[1:]:
			name, value = item.split(':')
			definition.properties[name] = value
		return definition

class method:
	"""
	Implements a user-defined method. This functions as the leaf node
	of a multimethod's dispatch tree.
	User-defined methods have a custom __call___ method;
	Built-in methods override __call__.
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
		else:
			self.instructions = None
			self.__call__ = body
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
		instructions: list[instruction],
		signature: dict[str, typedef],
		check: dict[str, typedef]
		) -> None:

		super().__init__(instructions, signature)

	def __call__(
		self,
		task,
		*args: tuple
		) -> reference:
		
		task.message('future', self, args, task.values[self.name])
		task.properties.type = 'future'
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
		self.property = sophia_any # Distinguishing type property
		self.index = 0 # Signature index
		self.value = None # Optional property value

	def __call__(self, task, *types):
		"""
		Multiple dispatch algorithm, with help from Julia:
		https://github.com/JeffBezanson/phdthesis
		Binary search tree yields closest key for method, then key is verified.
		"""
		tree = self.true if types else self.false # Here's tree
		while tree: # Traverse tree; terminates upon reaching leaf node
			tree = tree.true if (tree.index < task.op.arity) and tree.op(types[tree.index]) else tree.false
		if tree is None:
			return task.error('DISP', task.op.name, types)
		instance, final, signature = tree.routine, tree.final, tree.signature
		try:
			for i, item in enumerate(types): # Verify type signature
				if item > signature[i]:
					raise IndexError
		except IndexError:
			return task.error('DISP', task.op.name, types)
		return instance, final, signature

	def __bool__(self): return True

	def __str__(self): return '{0} {1} {2}'.format(self.property.name, self.index, self.value)

	def set( # Set check attributes
		self,
		true: method,
		false: method,
		check: typedef,
		index: int,
		value: Any = None
		) -> None:

		self.true = true
		self.false = false
		self.property = check
		self.index = index
		self.value = value

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
			node.set(new, other, sophia_any, other_length)
		elif new_length < other_length:
			node.set(other, new, sophia_any, new_length)
		else: # Prioritise unmatched arity over unmatched signatures
			for i in range(new_length): # Signatures guaranteed not to match
				new_item, other_item = new.signature[i], other.signature[i]
				new_criterion = new_item.criterion(other_item)
				other_criterion = other_item.criterion(new_item)
				if new_criterion is not None: # If new has a property that other doesn't
					value = new_item.properties[new_criterion.name] if new_criterion.name in new_item.properties else None
					node.set(new, other, new_criterion, i, value)
					break
				elif other_criterion is not None: # If other has a property that new doesn't, just in case
					value = other_item.properties[other_criterion.name] if other_criterion.name in other_item.signature[i].properties else None
					node.set(other, new, other_criterion, i, value)
					break
		return node

	def check( # Universal dispatch check exploiting properties of structural typing
		self,
		signature: list[typedef]
		) -> bool: 

		return self.property in signature[self.index].types and \
			   (self.value is None or \
			   (self.property.name in signature.properties and signature.properties[self.property.name] == self.value))

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

class sophia_any:
	"""
	Base template for built-in types, equivalent to none | some.
	"""
	name = 'any'
	data = object, type(None)

	def __new__(
		cls,
		task,
		value: Any
		) -> Any: # Type check disguised as an object constructor

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

std_any = typedef(None, sophia_any)

class sophia_none(sophia_any): # Null type
	
	name = 'none'
	data = type(None)

	def __new__(
		cls,
		task,
		value: Any
		) -> Any: # Type check disguised as an object constructor

		return value is None

std_none = typedef(std_any, sophia_none)

class sophia_some(sophia_any): # Non-null type
	
	name = 'some'
	data = object

	def __new__(
		cls,
		task,
		value: Any
		) -> Any:

		return isinstance(value, cls.data)

std_some = typedef(std_any, sophia_some)

class sophia_routine(sophia_some):
	
	name = 'routine'
	data = funcdef, eventdef, typedef

std_routine = typedef(std_some, sophia_routine)

class sophia_type(sophia_routine):
	
	name = 'type'
	data = typedef

std_type = typedef(std_routine, sophia_type, prototype = std_any)

class sophia_event(sophia_routine):
	
	name = 'event'
	data = eventdef

std_event = typedef(std_routine, sophia_event)

class sophia_function(sophia_routine):
	
	name = 'function'
	data = funcdef

std_function = typedef(std_routine, sophia_function)

class sophia_boolean(sophia_some):
	
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

std_boolean = typedef(std_some, sophia_boolean, prototype = False)

class sophia_number(sophia_some):
	
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

std_number = typedef(std_some, sophia_number, prototype = real())

class sophia_integer(sophia_number):

	name = 'integer'

	def __new__( # Sophia now does these sequentially, so no need to check the data type
		cls,
		task,
		value: real
		) -> bool:
		
		return value % 1 == 0

std_integer = typedef(std_number, sophia_integer) # Inherits prototype from std_number

class sophia_sequence(sophia_some):
	
	name = 'sequence'
	data = str, list, dict, slice

std_sequence = typedef(std_some, sophia_sequence)

class sophia_string(sophia_sequence):
	
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

std_string = typedef(std_sequence, sophia_string, prototype = '')

class sophia_list(sophia_sequence):
	
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

std_list = typedef(std_sequence, sophia_list, prototype = ())

class sophia_record(sophia_sequence):
	
	name = 'record'
	data = dict

std_record = typedef(std_sequence, sophia_record, prototype = {})

class sophia_slice(sophia_sequence):
	
	name = 'slice'
	data = slice
	
std_slice = typedef(std_sequence, sophia_slice, prototype = slice())

class sophia_future(sophia_some):
	
	name = 'future'
	data = reference

std_future = typedef(std_some, sophia_future, prototype = std_stdin)

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
del std_stdin # stdlib.arche shouldn't find this yet