import arche

class sophia_untyped: # Abstract base class

	types = object

	def __new__(cls, value): # Using __new__ for casting

		if isinstance(value, sophia_untyped):
			value = value.value
		if issubclass(type(value), cls.types):
			return object.__new__(cls)

	def __init__(self, value):

		self.value = value

class sophia_string(sophia_untyped):

	types = str

class sophia_integer(sophia_untyped): # Integer type

	types = int

	def __new__(cls, value):
		
		if isinstance(value, sophia_untyped):
			value = value.value
		print(cls.__mro__)
		if issubclass(type(value), cls.__mro__[0].types) and int(value) == value:
			return object.__new__(cls)

	def __init__(self, value):

		if isinstance(value, (bool, float)) and int(value) == value:
			value = int(value)
		self.value = value

a = 'a'
print(a.split('.'))