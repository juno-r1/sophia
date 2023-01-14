from multiprocessing import current_process, parent_process

class namespace: # Base namespace object

	def __init__(self, params, args, types):

		self.name = current_process().name
		if parent_process():
			self.parent = parent_process().pid # PID of parent process
		else:
			self.parent = 1 # Points to builtins
		self.values = dict(zip(params, args)) # Dict of values for faster access
		self.types = dict(zip(params, types)) # Dict of types for correct typing

	def __repr__(self):
		
		return '===\n' + self.name + '\n---\n' + '\n---\n'.join((name + ' ' + str(self.types[name]) + ' ' + repr(value) for name, value in self.values.items())) + '\n==='

	def read(self, name):

		try:
			return self.values[name] # Return binding if it exists in the namespace
		except KeyError:
			return None

	def write(self, name, value):
		
		self.values[name] = value # Update or create new binding

	def read_type(self, name):

		try:
			return self.types[name] # Return binding if it exists in the namespace
		except KeyError:
			return None

	def write_type(self, name, value):
		
		self.types[name] = value # Update or create new binding

	def delete(self, name): # Internal method; should never raise KeyError
		
		del self.values[name] # Delete binding if it exists in the namespace
		del self.types[name]