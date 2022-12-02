class definition: # Created by assignment

	def __init__(self, name, value, type_value = 'untyped', reserved = False):

		self.name = name
		self.value = value
		self.type = type_value
		self.reserved = reserved

class coroutine(definition): # Created by function calls and coroutine binding

	def __init__(self, name, entry = None, exit = None, type_value = 'untyped', *args):
		
		super().__init__(name, None, type_value)
		self.entry = entry
		self.exit = exit
		self.namespace = [arg for arg in args]
		self.instances = []
		self.path = [0]