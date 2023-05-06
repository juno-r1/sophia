'''
The Aletheia module defines built-in types and type operations.
'''

names = {
	'NoneType': 'null',
	'type_method': 'type',
	'event_method': 'event',
	'function_method': 'function',
	'bool': 'boolean',
	'Rational': 'number',
	'str': 'string',
	'tuple': 'list',
	'dict': 'record',
	'slice': 'slice',
	'reference': 'future'
}

def cast(task, target, value):

	while target.supertype:
		target = target.supertype
	return getattr(target, '__{0}__'.format(names[type(value).__name__]))(value)

def infer(value): # Infers type of value

	name = type(value).__name__
	if name in names:
		if name == 'Rational' and value % 1 == 0:
			return 'integer'
		else:
			return names[name]
	else:
		return 'untyped' # Applies to all internal types

import arche, kleio # Important to avoid recursive import
from rationals import Rational as real

# Built-in types

class sophia_null: # Null type

	name = 'null'
	types = type(None)
	supertype = None

	def __new__(cls, task, value): return

t_null = arche.type_method('null', [])
t_null.register(sophia_null,
				'null',
				('null',))

class sophia_untyped: # Non-abstract base class

	name = 'untyped'
	types = object
	supertype = None
	
	def __new__(cls, task, value): # Type check disguised as an object constructor
		
		if isinstance(value, cls.types):
			return value
		else:
			task.override = 'null'
			return task.error('CAST', cls.name, str(value))

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

t_untyped = arche.type_method('untyped', [])
t_untyped.register(sophia_untyped,
				   'untyped',
				   ('untyped',))

class sophia_type(sophia_untyped): # Type type
	
	name = 'type'
	types = arche.type_method

t_type = arche.type_method('type', ['untyped'])
t_type.register(sophia_type,
				'type',
				('untyped',))

class sophia_event(sophia_untyped): # Event type

	name = 'event'
	types = arche.event_method

t_event = arche.type_method('event', ['untyped'])
t_event.register(sophia_event,
				 'event',
				 ('untyped',))

class sophia_function(sophia_untyped): # Function type

	name = 'function'
	types = arche.function_method

t_function = arche.type_method('function', ['untyped'])
t_function.register(sophia_function,
					'function',
					('untyped',))

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

t_boolean = arche.type_method('boolean', ['untyped'])
t_boolean.register(sophia_boolean,
				   'boolean',
				   ('untyped',))

class sophia_number(sophia_untyped): # Abstract number type

	name = 'number'
	types = real

	@classmethod
	def __boolean__(cls, value): return 1 if value else 0

	@classmethod
	def __number__(cls, value): return value

	@classmethod
	def __string__(cls, value): return real(value)

t_number = arche.type_method('number', ['untyped'])
t_number.register(sophia_number,
				  'number',
				  ('untyped',))

class sophia_integer(sophia_number): # Integer type

	name = 'integer'
	types = real

	def __new__(cls, task, value):
		
		if isinstance(value, cls.types) and value % 1 == 0:
			return value
		else:
			task.override = 'null'
			return task.error('CAST', cls.name, str(value))

t_integer = arche.type_method('integer', ['number', 'untyped'])
t_integer.register(sophia_integer,
				   'integer',
				   ('untyped',))

class sophia_string(sophia_untyped): # String type

	name = 'string'
	types = str

	@classmethod
	def __null__(cls, value): return 'null'

	@classmethod
	def __type__(cls, value): return 'type {0}'.format(value.name)

	@classmethod
	def __event__(cls, value): return 'event {0}'.format(value.name)

	@classmethod
	def __operator__(cls, value): return 'operator {0}'.format(value.name)

	@classmethod
	def __function__(cls, value): return 'function {0}'.format(value.name)

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
	def __slice__(cls, value): return '{0}:{1}:{2}'.format(value.start, value.stop, value.step)

	@classmethod
	def __future__(cls, value): return 'future ' + value.name

	@classmethod
	def __stream__(cls, value): return 'stream ' + value.name

t_string = arche.type_method('string', ['untyped'])
t_string.register(sophia_string,
				  'string',
				  ('untyped',))

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

t_list = arche.type_method('list', ['untyped'])
t_list.register(sophia_list,
				'list',
				('untyped',))

class sophia_record(sophia_untyped): # Record type

	name = 'record'
	types = dict

t_record = arche.type_method('record', ['untyped'])
t_record.register(sophia_record,
				  'record',
				  ('untyped',))

class sophia_slice(sophia_untyped): # Slice type

	name = 'slice'
	types = arche.slice

t_slice = arche.type_method('slice', ['untyped'])
t_slice.register(sophia_slice,
				 'slice',
				 ('untyped',))

class sophia_future(sophia_untyped): # Process type
	
	name = 'future'
	types = kleio.reference

t_future = arche.type_method('future', ['untyped'])
t_future.register(sophia_future,
				  'future',
				  ('untyped'))

# Namespace composition

types = {v.name: v for k, v in globals().items() if k.split('_')[0] == 't'}