class meta(type):

	def __instancecheck__(self, instance):
	
		return self.__name__ in [cls.__name__ for cls in type(instance).__mro__]

	def new(cls, value):
		
		cls_dict = {name: attr for name, attr in list(cls.__dict__.items()) if name != '__new__'}
		if len(type(value).__mro__) > 2:
			value = type(value).__mro__[-2](value)
		if len(cls.__mro__) > 2:
			value = meta.new(cls.__mro__[1], value)
		return meta(cls.__name__, type(value).__mro__, cls_dict)(value)

abstract = meta('abstract', (), {'__new__': meta.new})

class boolean(abstract): # Boolean type

	def __new__(cls, value): # Hatred

		if value is True or value is False or isinstance(value, cls):
			return super().__new__(cls, value)
		
	def __bool__(self): # Spoofs being a true boolean
		
		return self != 0

	def __str__(self):
		
		return str(bool(self)).lower()

a = boolean(True)
b = boolean(False)
c = boolean(a)
print(a, type(a).__mro__)
print(b, type(b).__mro__)
print(c, type(c).__mro__)