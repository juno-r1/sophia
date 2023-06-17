'''
The Aletheia module defines built-in types and type operations.
'''

class descriptor:
	"""Type descriptor that holds the properties of a given value."""
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
	
	name = type(value).__name__
	member, length = 'untyped', None
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
		elif name == 'real' and value % 1 == 0:
			name = 'integer'
		else:
			name = names[name]
	else:
		name = 'untyped' # Applies to all internal types
	return descriptor(name, member, length)

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