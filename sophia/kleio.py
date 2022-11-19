class coroutine: # Created by function calls and coroutine binding

	def __init__(self, name, entry = None, exit = None, *args):
		
		self.name = name
		self.value = None
		self.entry = entry
		self.exit = exit
		self.namespace = [arg for arg in args]
		self.instances = []
		self.path = [0]

class definition: # Created by assignment

	def __init__(self, name, value, type_value = 'untyped', reserved = False):

		self.name = name
		self.value = value
		self.type = type_value
		self.reserved = reserved