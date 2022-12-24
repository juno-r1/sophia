from multiprocessing import current_process, parent_process

class namespace: # Base namespace object

	def __init__(self, params, args):

		self.name = current_process().name
		self.parent = parent_process().pid # PID of parent process
		self.__space = {param.value: arg for param, arg in zip(params, args)} # Dict of values for faster access

	def __repr__(self):

		return '===\n' + self.name + '\n---\n' + '\n---\n'.join((name + ' ' + repr(value) for name, value in self.__space.items())) + '\n==='

	def read(self, name):

		try:
			return self.__space[name] # Return binding if it exists in the namespace
		except KeyError:
			return None

	def write(self, name, value):
		
		if name in current_process().reserved: # If the name is bound, or is a loop index:
			raise NameError('Bind to reserved name: ' + name)
		else:
			self.__space[name] = value # Update or create new binding

	def delete(self, name):

		try:
			del self.__space[name] # Delete binding if it exists in the namespace
		except KeyError:
			raise NameError('Undefined name: ' + name)