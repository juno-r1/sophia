'''
The Aletheia module defines built-in types and type operations.
'''

import arche, kleio
from rationals import Rational as real

# Built-in types

class sophia_untyped: # Non-abstract base class

	name = 'untyped'
	types = object
	supertype = None
	
	def __new__(cls, value): # Type check disguised as an object constructor
		
		return value if isinstance(value, cls.types) else None

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
	def __future__(cls, value): return

	@classmethod
	def __stream__(cls, value): return

class sophia_type(sophia_untyped): # Type type
	
	name = 'type'
	types = type

class sophia_function(sophia_untyped): # Function type

	name = 'function'
	types = arche.method

class sophia_boolean(sophia_untyped): # Boolean type

	name = 'boolean'
	types = bool

	@classmethod
	def __boolean__(cls, value): return value

	@classmethod
	def __number__(cls, value): return True if value != 0 else False

	@classmethod
	def __string__(cls, value): return True if value != '' else False

	@classmethod
	def __list__(cls, value): return True if value != [] else False

	@classmethod
	def __record__(cls, value): return True if value != {} else False

	@classmethod
	def __slice__(cls, value): return True if len(value) != 0 else False

class sophia_number(sophia_untyped): # Abstract number type

	name = 'number'
	types = real

	@classmethod
	def __boolean__(cls, value): return 1 if value else 0

	@classmethod
	def __number__(cls, value): return value

	@classmethod
	def __string__(cls, value): return real(value)

class sophia_integer(sophia_number): # Integer type

	name = 'integer'
	types = real

	def __new__(cls, value):
		
		return value if isinstance(value, real) and value % 1 == 0 else None

class sophia_string(sophia_untyped): # String type

	name = 'string'
	types = str

	@classmethod
	def __null__(cls, value): return 'null'

	@classmethod
	def __type__(cls, value): return 'type ' + value.name

	@classmethod
	def __event__(cls, value): return 'event ' + value.name

	@classmethod
	def __operator__(cls, value): return 'operator ' + value.name

	@classmethod
	def __function__(cls, value): return 'function ' + value.name

	@classmethod
	def __boolean__(cls, value): return 'true' if value else 'false'

	@classmethod
	def __number__(cls, value): return str(value)

	@classmethod
	def __string__(cls, value): return value

	@classmethod
	def __list__(cls, value): return '[' + ', '.join([arche.cast_type_untyped(cls, i) for i in value]) + ']'

	@classmethod
	def __record__(cls, value): return '[' + ', '.join([arche.cast_type_untyped(cls, k) + ': ' + arche.cast_type_untyped(cls, v) for k, v in value.items()]) + ']'

	@classmethod
	def __slice__(cls, value): return '{0}:{1}:{2}'.format(*value.indices)

	@classmethod
	def __future__(cls, value): return 'future ' + value.name

	@classmethod
	def __stream__(cls, value): return 'stream ' + value.name

class sophia_list(sophia_untyped): # List type

	name = 'list'
	types = tuple

	@classmethod
	def __string__(cls, value): return tuple(i for i in value)

	@classmethod
	def __list__(cls, value): return value

	@classmethod
	def __record__(cls, value): return tuple(value.items())

	@classmethod
	def __slice__(cls, value): return tuple(value.value)

class sophia_record(sophia_untyped): # Record type

	name = 'record'
	types = dict

class sophia_slice(sophia_untyped): # Slice type

	name = 'slice'
	types = arche.slice

class sophia_future(sophia_untyped): # Process type
	
	name = 'future'
	types = kleio.reference

# Namespace composition

types = {v.name: v for k, v in globals().items() if k.split('_')[0] == 'sophia'}
supertypes = {
	'null': ('null',),
	'untyped': ('untyped',),
	'type': ('type', 'untyped'),
	'function': ('function', 'untyped'),
	'boolean': ('boolean', 'untyped'),
	'number': ('number', 'untyped'),
	'integer': ('integer', 'number', 'untyped'),
	'string': ('string', 'untyped'),
	'list': ('list', 'untyped'),
	'record': ('record', 'untyped'),
	'slice': ('slice', 'untyped'),
	'future': ('future', 'untyped')

}
specificity = {k: len(v) for k, v in supertypes.items()} # Length of supertypes is equivalent to specificity of subtype