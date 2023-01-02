from multiprocessing import current_process, parent_process

class namespace: # Base namespace object

	def __init__(self, params, args):

		self.name = current_process().name
		if parent_process():
			self.parent = parent_process().pid # PID of parent process
		else:
			self.parent = 1 # Points to builtins
		self.space = dict(zip(params, args)) # Dict of values for faster access

	def __repr__(self):

		return '===\n' + self.name + '\n---\n' + '\n---\n'.join((name + ' ' + repr(value) for name, value in self.space.items())) + '\n==='

	def read(self, name):

		try:
			return self.space[name] # Return binding if it exists in the namespace
		except KeyError:
			return None

	def write(self, name, value):
		
		self.space[name] = value # Update or create new binding

	def delete(self, name):

		try:
			del self.space[name] # Delete binding if it exists in the namespace
		except KeyError:
			raise NameError('Undefined name: ' + name)