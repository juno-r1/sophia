from multiprocessing import Process, current_process, parent_process

class namespace: # Base namespace object

	def __init__(self, *args):

		self.name = current_process().name
		self.parent = parent_process().pid # PID of parent process
		self._space = [arg for arg in args] # List of definitions

	def __str__(self):

		return '===\n' + '\n---\n'.join((str(item) for item in self._space)) + '\n==='

	def read(self, name):

		for item in self._space:
			if item.name == name: # If the name is bound in the runtime:
				if isinstance(item.value, Process) and not item.value.bound: # If the name is associated with an unbound routine:
					item.value = current_process().cast(item.value.end.get(), item.type) # Block for return value and check type
				return item # Return the binding

	def write(self, definition):

		for item in self._space: # Finds and updates a name binding
			if item.name == definition.name:
				if item.reserved: # If the name is bound, or is a loop index:
					raise NameError('Bind to reserved name: ' + definition.name)
				else:
					item.value = definition.value
					if definition.type != 'untyped':
						item.type = definition.type
				break
		else: # Creates a new name binding
			self._space.append(definition)