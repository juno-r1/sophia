'''
The Aletheia module defines built-in types and type operations.
'''

from functools import reduce

class descriptor:
	"""Type descriptor that holds the properties of a given value."""
	__slots__ = ('type', 'member', 'length')

	def __init__(self, name = None, member = 'untyped', length = None):

		self.type = name
		self.member = member
		self.length = length

	def __str__(self):
		
		attributes = [self.type]
		if self.member != 'untyped':
			attributes.append(self.member)
		if self.length:
			attributes.append(str(self.length))
		return '.'.join(attributes)

	#__repr__ = __str__

	@classmethod
	def read(cls, string):

		values = string.split('.')
		member, length, l = 'untyped', None, len(values)
		if l == 3:
			member, length = values[1], int(values[2])
		elif l == 2:
			try:
				length = int(values[1])
			except ValueError:
				member = values[1]
		return cls(values[0], member, length)

	@classmethod
	def convert(cls, record):
		
		return cls(record['type'], record['member'] if record['member'] else 'untyped', record['length'])

def infer(value): # Infers type of value
	
	name, member = type(value).__name__, 'untyped'
	if name in names:
		name = names[name]
		if name == 'number' and value % 1 == 0:
			name = 'integer'
		elif name == 'string':
			member = 'string'
		elif name == 'slice':
			member = 'integer'
		elif name == 'list':
			member = reduce(supertype, [infer(item).type for item in value]) if value else 'untyped'
		elif name == 'record':
			member = reduce(supertype, [infer(item).type for item in value.values()]) if value else 'untyped'
	else:
		name = 'untyped' # Applies to all internal types
	try:
		length = len(value)
	except TypeError:
		length = None
	return descriptor(name, member, length)

def supertype(a, b): # Must be named function due to limitations of multiprocessing

	return [i for i in supertypes[a] if i in supertypes[b]][0]

names = {
	'NoneType': 'null',
	'type_method': 'type',
	'event_method': 'event',
	'function_method': 'function',
	'bool': 'boolean',
	'real': 'number',
	'str': 'string',
	'tuple': 'list',
	'dict': 'record',
	'slice': 'slice',
	'reference': 'future'
}
supertypes = {
	'null': ['null'],
	'untyped': ['untyped'],
	'type': ['type', 'untyped'],
	'event': ['event', 'untyped'],
	'function': ['function', 'untyped'],
	'boolean': ['boolean', 'untyped'],
	'number': ['number', 'untyped'],
	'integer': ['integer', 'number', 'untyped'],
	'string': ['string', 'untyped'],
	'list': ['list', 'untyped'],
	'record': ['record', 'untyped'],
	'slice': ['slice', 'untyped'],
	'future': ['future', 'untyped']
}