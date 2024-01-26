from ..datatypes.mathos import real
from ..internal.presets import DATATYPES

class to_boolean:

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

class to_number:

	@classmethod
	def __boolean__(cls, value): return real(int(value))

	@classmethod
	def __number__(cls, value): return value

	@classmethod
	def __string__(cls, value): return real.read(value)

	@classmethod
	def __future__(cls, value): return real(value.pid)

class to_string:

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

	@classmethod
	def __list__(cls, value): return '[' + ', '.join([cast(i, 'string') for i in value]) + ']'

	@classmethod
	def __record__(cls, value): return '[' + ', '.join([cast(k, 'string') + ': ' + cast(v, 'string') for k, v in value.items()]) + ']'

	@classmethod
	def __slice__(cls, value): return '{0}:{1}:{2}'.format(value.start, value.stop, value.step)

	@classmethod
	def __future__(cls, value): return value.name

class to_list:

	@classmethod
	def __string__(cls, value): return tuple(i for i in value)

	@classmethod
	def __list__(cls, value): return value

	@classmethod
	def __record__(cls, value): return tuple(value.items())

	@classmethod
	def __slice__(cls, value): return tuple(value)

def cast(value, target):

	if target not in targets:
		return None
	routine = getattr(targets[target], '__{0}__'.format(DATATYPES[type(value).__name__]), None)
	return routine(value) if routine else None

targets = {
	'boolean': to_boolean,
	'number': to_number,
	'string': to_string,
	'list': to_list,
}