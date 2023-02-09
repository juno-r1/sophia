'''
The Aletheia module defines built-in types and type operations.
'''

import arche, kleio, mathos
from fractions import Fraction as real

class sophia_untyped: # Non-abstract base class

	name = 'untyped'
	types = object
	supertype = None
	
	def __new__(cls, value): # Type check disguised as an object constructor
		
		if cls.types:
			if isinstance(value, cls.types):
				return value
		else:
			for subclass in cls.__subclasses__():
				if subclass(value) is not None:
					return value

class sophia_process(sophia_untyped): # Process type
	
	name = 'process'
	types = kleio.reference

class sophia_routine(sophia_untyped): # Abstract routine type

	name = 'routine'
	types = None # Null types makes __new__ check the types of a type's subclasses

class sophia_type(sophia_routine): # Type type
	
	name = 'type'
	types = type

	def __new__(cls, value):
		
		if isinstance(value, cls.types) or type(value).__name__ == 'type_statement': # I hate that this is necessary so so much
			return value

	def cast(self, value): # Type conversion
		
		while self.supertype:
			self = self.supertype
		try: # Please find a better way to do this
			try:
				return self.types[0](value)
			except TypeError:
				return self.types(value)
		except TypeError:
			return None

	cast = (cast, 'untyped', 'type', 'untyped')

class sophia_interface(sophia_routine): # Interface type

	name = 'interface'

	def __new__(cls, value):
		
		if type(value).__name__ == 'interface_statement':
			return value

class sophia_operator(sophia_routine): # Operator type

	name = 'operator'
	types = mathos.operator

	def __new__(cls, value):
		
		if isinstance(value, cls.types) or type(value).__name__ == 'operator_statement':
			return value

class sophia_callable(sophia_routine): # Callable type

	name = 'callable'
	types = None

class sophia_event(sophia_callable): # Event type

	name = 'event'

	def __new__(cls, value):
		
		if type(value).__name__ == 'event_statement':
			return value

class sophia_function(sophia_callable): # Function type

	name = 'function'
	types = arche.procedure

	def __new__(cls, value):
		
		if isinstance(value, cls.types) or type(value).__name__ == 'function_statement':
			return value

class sophia_value(sophia_untyped): # Abstract element type

	name = 'value'
	types = None

class sophia_boolean(sophia_value): # Boolean type

	name = 'boolean'
	types = bool

class sophia_number(sophia_value): # Abstract number type

	name = 'number'
	types = None

class sophia_integer(sophia_number): # Integer type

	name = 'integer'
	types = int, real

	def __new__(cls, value):
		
		if isinstance(value, cls.types) and value % 1 == 0:
			return value

class sophia_real(sophia_number): # Real type

	name = 'real'
	types = real, int # Abstract data type, remember

class sophia_iterable(sophia_untyped): # Abstract iterable type

	name = 'iterable'
	types = None

class sophia_sequence(sophia_iterable): # Abstract sequence type

	name = 'sequence'
	types = None

	def length(self):

		return len(self)

	length = (length, 'integer', 'sequence')

class sophia_string(sophia_sequence): # String type

	name = 'string'
	types = str

class sophia_list(sophia_sequence): # List type

	name = 'list'
	types = tuple

class sophia_record(sophia_sequence): # Record type

	name = 'record'
	types = dict

class sophia_slice(sophia_sequence): # Slice type

	name = 'slice'
	types = arche.slice

	def reverse(self):

		return reversed(self)

	reverse = (reverse, 'slice', 'slice')

types = {v.name: v for k, v in globals().items() if k.split('_')[0] == 'sophia'}
for key in types:
	types[key].namespace = {k: arche.procedure(*v) for k, v in types[key].__dict__.items() if '__' not in k and k not in ('name', 'types', 'supertype')}
supertypes = {'untyped': ['untyped'], # Suboptimal way to optimise subtype checking
			  'process': ['process', 'untyped'],
			  'routine': ['routine', 'untyped'],
			  'type': ['type', 'routine', 'untyped'],
			  'interface': ['interface', 'routine', 'untyped'],
			  'operator': ['operator', 'routine', 'untyped'],
			  'callable': ['callable', 'routine', 'untyped'],
			  'event': ['event', 'callable', 'routine', 'untyped'],
			  'function': ['function', 'callable', 'routine', 'untyped'],
			  'value': ['value', 'untyped'],
			  'boolean': ['boolean', 'value', 'untyped'],
			  'number': ['number', 'value', 'untyped'],
			  'integer': ['integer', 'number', 'value', 'untyped'],
			  'real': ['real', 'number', 'value', 'untyped'],
			  'iterable': ['iterable', 'untyped'],
			  'sequence': ['sequence', 'iterable', 'untyped'],
			  'string': ['string', 'sequence', 'iterable', 'untyped'],
			  'list': ['list', 'sequence', 'iterable', 'untyped'],
			  'record': ['record', 'sequence', 'iterable', 'untyped'],
			  'slice': ['slice', 'sequence', 'iterable', 'untyped']}