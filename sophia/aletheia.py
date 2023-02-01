import arche, kleio
from sophia import type_statement, operator_statement, function_statement # Not a circular dependency
from multiprocessing import current_process
from fractions import Fraction as real

class sophia_untyped: # Non-abstract base class

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

class sophia_process(sophia_untyped): # Process/module type
	
	types = kleio.reference

class sophia_routine(sophia_untyped): # Abstract routine type

	types = None # Null types makes __new__ check the types of a type's subclasses

class sophia_type(sophia_routine): # Type type
	
	types = type, type_statement

	def cast(self, value): # Type conversion
		
		type_routine = self
		if type_routine.supertype:
			current_process().cast(value, type_routine.name) # Check validity 
		while type_routine.supertype:
			type_routine = type_routine.supertype
		if type_routine.types and issubclass(type_routine, (sophia_value, sophia_sequence)):
			try:
				return type_routine.types(value)
			except TypeError:
				return current_process().error('Failed conversion to ' + type_routine.__name__.split('_')[1] + ': ' + str(value))
		else:
			return current_process().error('Unsupported conversion to ' + type_routine.__name__.split('_')[1] + ': ' + str(value))

class sophia_operator(sophia_routine): # Operator type

	types = arche.operator, operator_statement

class sophia_function(sophia_routine): # Function type

	types = sophia_untyped.__new__.__class__, function_statement # Hatred

class sophia_value(sophia_untyped): # Abstract element type

	types = None

class sophia_boolean(sophia_value): # Boolean type

	types = bool

class sophia_number(sophia_value): # Abstract number type

	types = None

class sophia_integer(sophia_number): # Integer type

	types = int

class sophia_real(sophia_number): # Real type

	types = real

class sophia_iterable(sophia_untyped): # Abstract iterable type

	types = None

class sophia_slice(sophia_iterable): # Slice type

	types = arche.slice

class sophia_sequence(sophia_iterable): # Abstract sequence type

	types = None

	def length(self):

		return len(self)

class sophia_string(sophia_sequence): # String type

	types = str

class sophia_list(sophia_sequence): # List type

	types = tuple

class sophia_record(sophia_sequence): # Record type

	types = dict

types = {k.split('_')[1]: v for k, v in globals().items() if k.split('_')[0] == 'sophia'}