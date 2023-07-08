'''
The Aletheia module defines built-in types and type operations.
'''

from functools import reduce

class descriptor:
	"""Type descriptor that holds the properties of a given value."""
	__slots__ = ('type', 'member', 'length', 'supertypes', 'supermember', 'specificity')
	criteria = 3

	def __init__(self, type = None, member = None, length = None, prepare = False):

		self.type = type
		self.member = member
		self.length = length
		if prepare:
			self.supertypes = supertypes[self.type or 'null']
			self.supermember = supertypes[self.member or 'null']
			self.specificity = (specificity[self.type] if self.type else 0,
								specificity[self.member] if self.member else 0,
								int(self.length is not None))
		else:
			self.supertypes = []
			self.supermember = []
			self.specificity = (0, 0, 0)

	def __lt__(self, other): # Implements supertype relation for descriptors
		
		return (other.type in self.supertypes) and \
			   (other.member is None or other.member in self.supermember) and \
			   (other.length is None or other.length == self.length)

	def __str__(self):
		
		attributes = [self.type or 'null']
		if self.member and self.member != 'untyped':
			attributes.append(self.member)
		if self.length:
			attributes.append(str(self.length))
		return '.'.join(attributes)

	__repr__ = __str__
	#def __repr__(self): return str(self.__dict__)
	#__str__ = __repr__

	@classmethod
	def read(cls, string):
		
		values = string.split('.')
		member, length, l = None, None, len(values)
		if l == 3:
			member, length = values[1], int(values[2])
		elif l == 2:
			try:
				length = int(values[1])
			except ValueError:
				member = values[1]
		return cls(values[0], member, length)

	def merge(self, other):
		self.type = other.type or self.type
		self.member = other.member or self.member
		self.length = other.length if other.length is not None else self.length
		return self

	def complete(self, value): # Completes descriptor with inferred type of value
		
		self.type = self.type or infer_type(value)
		if self.type in ('string', 'list', 'record', 'slice'):
			self.member = self.member or infer_member(value, self.type)
			self.length = self.length if self.length is not None else len(value)
		return self

def infer(value): # Infers type descriptor of value
	
	name, member = type(value).__name__, None
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

def infer_type(value): # Infers type of value

	name = type(value).__name__
	if name in names:
		name = names[name]
		return 'integer' if name == 'number' and value % 1 == 0 else name
	else:
		return 'untyped'

def infer_member(value, name): # Infers member type of value
	
	if name == 'string':
		return 'string'
	elif name == 'slice':
		return 'integer'
	elif name == 'list':
		return reduce(supertype, [infer(item).type for item in value]) if value else 'untyped'
	elif name == 'record':
		return reduce(supertype, [infer(item).type for item in value.values()]) if value else 'untyped'

def subtype(task, value): return value

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
specificity = {
	'null': 1,
	'untyped': 1,
	'type': 2,
	'event': 2,
	'function': 2,
	'boolean': 2,
	'number': 2,
	'integer': 3,
	'string': 2,
	'list': 2,
	'record': 2,
	'slice': 2,
	'future': 2
}