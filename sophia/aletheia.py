'''
The Aletheia module defines built-in types and type operations.
'''

class descriptor:
	"""Type descriptor that holds the properties of a given value."""
	__slots__ = ('type', 'member', 'length')

	def __init__(self, name = None, member = None, length = None):

		self.type = name
		self.member = member
		self.length = length

	def __str__(self):

		attributes = [self.type]
		if self.member:
			attributes.append(self.member)
		if self.length:
			attributes.append(str(self.length))
		return '.'.join(attributes)

	__repr__ = __str__

	@classmethod
	def read(cls, string):

		values = string.split('.')
		member, length, l = None, None, len(values)
		if l == 3:
			member, length = values[1], int(values[2])
		elif l == 2:
			try:
				member, length = None, int(values[1])
			except ValueError:
				member, length = values[1], None
		return cls(values[0], member = member, length = length)

	@classmethod
	def convert(cls, record):
		
		return cls(name = record['type'], member = record['member'], length = record['length'])

def infer(value): # Infers type of value

	name = type(value).__name__
	member, length = None, None
	if name in names:
		if name == 'str':
			name, member, length = 'string', 'string', len(value)
		elif name == 'tuple': # Cheap (but not complete) member type evaluation
			name = 'list'
			types = [infer(item).type for item in value]
			first = types[0]
			member = first if all(i == first for i in types) else 'untyped'
			length = len(value)
		elif name == 'dict':
			name = 'record'
			types = [infer(item).type for item in value.values()]
			first = types[0]
			member = first if all(i == first for i in types) else 'untyped'
			length = len(value)
		elif name == 'slice':
			member, length = 'integer', len(value)
		elif name == 'Rational' and value % 1 == 0:
			name = 'integer'
		else:
			name = names[name]
	else:
		name = 'untyped' # Applies to all internal types
	return descriptor(name, member = member, length = length)

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