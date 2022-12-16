from multiprocessing import Process, Lock, current_process, parent_process

class namespace: # Base namespace object

	def __init__(self, *args):

		self.name = current_process().name
		self.parent = parent_process().pid # PID of parent process
		self._space = {arg.name: arg for arg in args} # Dict of definitions for faster access

	def __str__(self):

		return '===\n' + '\n---\n'.join((str(item) for item in self._space)) + '\n==='

	def read(self, name):

		try:
			return self._space[name] # Return binding if it exists in the namespace
		except KeyError:
			return None

	def write(self, definition):

		try: # Updates existing binding
			item = self._space[definition.name]
			if item.reserved: # If the name is bound, or is a loop index:
				raise NameError('Bind to reserved name: ' + definition.name)
			else:
				item.value = definition.value
				if definition.type != 'untyped':
					item.type = definition.type
		except KeyError: # Creates new binding
			self._space[definition.name] = definition

	def delete(self, name):

		try:
			del self._space[name] # Delete binding if it exists in the namespace
		except KeyError:
			raise NameError('Undefined name: ' + name)