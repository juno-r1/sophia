'''
The Aletheia module defines built-in types and type operations.
'''

from functools import reduce

class descriptor:
	"""Type descriptor that holds the properties of a given value."""
	#__slots__ = ('type', 'member', 'length', 'supertypes', 'supermember', 'specificity')
	criteria = 3

	def __init__(self, type = None, member = None, length = None, prepare = False):

		self.type = type
		self.member = member
		self.length = length
		if prepare:
			self.supertypes = supertypes[self.type if self.type and self.type != '!' else 'null']
			self.supermember = supertypes[self.member or 'null']
			self.specificity = (specificity[self.type] if self.type and self.type != '!' else 0,
								specificity[self.member] if self.member else 0,
								int(self.length is not None))
		else:
			self.supertypes = []
			self.supermember = []
			self.specificity = (0, 0, 0)

	def __eq__(self, other): # Implements equality

		return (self.type == other.type) and \
			   (self.member == other.member) and \
			   (self.length == other.length)

	def __lt__(self, other): # Implements supertype relation
		
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

	def merge(self, other): # Because Python loves to keep references to mutable objects where it shouldn't

		self.__dict__.update(other.__dict__)

	def complete(self, other, value): # Completes descriptor with properties and inferred type of value
		
		self.type = self.type or other.type or infer_type(value)
		self.member = self.member or other.member
		self.length = self.length if self.length is not None else other.length
		if self.type in ('string', 'list', 'record', 'slice'):
			self.member = self.member or infer_member(value, self.type)
			self.length = self.length if self.length is not None else len(value)
		return self

	def mutual(self, other): # Implements mutual supertype relation
		
		mutuals = [i for i in self.supertypes if i in other.supertypes]
		final = descriptor(mutuals[0])
		final.supertypes = mutuals
		return final

class dispatch:
	"""
	Multiple dispatch object that implements a singly linked binary search
	tree. It is only ever necessary to traverse downward.
	"""
	__slots__ = ('true', 'false', 'value', 'index', 'op')

	def __init__(self, value, condition = None, index = 0):
		
		self.true = None # Path or method if true
		self.false = None # Path or method if false
		self.value = value # Condition value
		self.index = index # Signature index
		if condition == 'type':
			self.op = self.supertype
		elif condition == 'member':
			self.op = self.supermember
		elif condition == 'length':
			self.op = self.length
		else:
			self.op = self.zero

	def __bool__(self): return True

	def __str__(self): return '{0} {1} {2}'.format(self.index, self.value, self.op.__name__)

	def supertype(self, signature): return self.value in signature.supertypes

	def supermember(self, signature): return self.value in signature.supermember

	def length(self, signature): return self.value == signature.length

	def zero(self, signature): return True # Never actually gets called

	def collect(self): # Collect all leaf nodes (order not important)

		x, y = self.true, self.false
		x = x.collect() if x else ([x] if x is not None else [])
		y = y.collect() if y else ([y] if y is not None else [])
		return x + y

	def extend(self, routine, final, signature): # Add node to tree
		
		new = leaf(routine, final, signature)
		if not signature: # Null method
			self.false = new
			return
		if self.true is None: # Empty tree
			self.true = new
			return
		value = new
		while self: # Traverse tree to closest leaf node
			index = self.index
			try:
				branch = self.op(signature[index])
			except IndexError:
				branch = False
			head, self = self, self.true if branch else self.false
		# self becomes a leaf node object halfway through this method. I know
		if signature != self.signature: # If signatures do not match:
			item, other = signature[index], self.signature[index]
			while item == other:
				index = index + 1
				try:
					item = signature[index]
				except IndexError: # Criteria too specific
					for i in range(index): # Find most significant criterion from the signatures
						if signature[i] != self.signature[i]:
							value = dispatch.generate(signature[i], self.signature[i], i)
							break
					branch = head.op(signature[head.index]) # Reset branch for new head
					value.true, value.false = new, head.true if branch else head.false
					break
				try:
					other = self.signature[index]
				except IndexError: # Increment index
					value = dispatch('untyped', 'type', index)
					value.true, value.false = new, self
					break
			else:
				value = dispatch.generate(item, other, index)
				value.true, value.false = new, self
		if branch:
			head.true = value
		else:
			head.false = value

	@classmethod
	def generate(cls, item, other, index):

		if item.type != other.type:
			return cls(item.type, 'type', index)
		elif item.member != other.member:
			return cls(item.member, 'member', index)
		else:
			return cls(item.length, 'length', index)

class leaf:
	"""
	Leaf node of dispatch tree.
	"""
	__slots__ = ('routine', 'final', 'signature')

	def __init__(self, routine, final, signature):

		self.routine = routine
		self.final = final
		self.signature = signature

	def __bool__(self): return False

	def __str__(self):
		
		try:
			return self.routine.__name__
		except AttributeError:
			return self.routine.name

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
			member = reduce(supertype, [infer_type(item) for item in value]) if value else 'untyped'
		elif name == 'record':
			member = reduce(supertype, [infer_type(item) for item in value.values()]) if value else 'untyped'
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