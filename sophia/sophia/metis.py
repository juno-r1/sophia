from .stdlib import arche
from .datatypes import aletheia
from .internal.instructions import instruction

class processor:
	"""
	Static analysis processor for generated instructions.
	"""
	def __init__(
		self,
		instructions: list[instruction],
		namespace: dict
		) -> None:

		self.name = instructions[0].label[0] if instructions else ''
		self.instructions = instructions
		self.values = arche.stdvalues | namespace
		self.types = arche.stdtypes | {k: aletheia.infer(v) for k, v in namespace.items()}
		self.cache = [None for _ in instructions]
		#self.path = int(bool(instructions))
		#self.op = None
		#self.signature = []
		#self.properties = {}
		## Active state of the program
		#self.state = None
		#self.scope()

#	def analyse(self): # Disabled until I can figure out how this is meant to work
	
#		#[print(i) for i in self.instructions]
#		#print('---')
#		while self.path < len(self.instructions): # This can and does change
#			"""
#			Initial stage to validate registers and check for reserved binds.
#			"""
#			self.op = self.instructions[self.path]
#			print(self.op)
#			self.path = self.path + 1
#			if self.op.name == 'BIND':
#				if self.op.label: # Special case for conditional register assignment
#					self.state.namespace[self.op.label[1]] = self.state.namespace[self.op.args[0]]
#				else:
#					self.bind()
#				continue
#			elif (address := self.op.register):
#				if address in stdlib.builtins:
#					return self.error('BIND', address)
#				try:
#					method, registers = self.values[self.op.name], self.op.args
#					self.signature = [self.state.namespace[arg] for arg in registers]
#				except KeyError as e: # Capture unbound name
#					return self.error('FIND', e.args[0])
#			else: # Labels
#				if self.op.name == 'START' or self.op.name == 'ELSE':
#					self.scope()
#				elif self.op.name == 'END' and self.path < len(self.instructions):
#					try:
#						self.unscope()
#					except NameError as e:
#						self.error('COND', e.args[0])
#				elif self.op.name == 'LIST':
#					self.sequence(self.op.label[0], self.op.args)
#				elif self.op.name == 'RECORD':
#					self.sequence(self.op.label[0], self.op.args[1::2])
#				continue
#			"""
#			Multiple dispatch algorithm, with help from Julia:
#			https://github.com/JeffBezanson/phdthesis
#			Binary search tree yields closest key for method, then key is verified.
#			"""
#			tree = method.tree.true if registers else method.tree.false # Here's tree
#			while tree: # Traverse tree; terminates upon reaching leaf node
#				tree = tree.true if (tree.index < self.op.arity) and tree.op(self.signature[tree.index]) else tree.false
#			if tree is None:
#				self.error('DISP', method.name, self.signature)
#				continue
#			final = tree.final
#			try:
#				for i, item in enumerate(self.signature): # Verify type signature
#					if item.type is None or item > tree.signature[i]:
#						raise IndexError
#			except IndexError:
#				self.error('DISP', method.name, self.signature)
#				continue
#			"""
#			Execute instruction and update registers.
#			"""
#			self.cache[self.path - 1] = cache(tree)
#			if final.type is None:
#				if self.op.name == '.index':
#					self.properties.type = self.signature[0].member
#			if final.type != '!': # Suppress write
#				final = self.complete(self.properties, final)
#				self.state.namespace[address], self.properties = final, self.state.namespace[address] if address in self.types else descriptor()
#				self.properties.type, self.properties.member, self.properties.length = None, None, None
#		#[print(i) for i in self.cache]
#		return self

#	def complete(self, descriptor, final): # Completes descriptor with properties and inferred type of value
		
#		descriptor.type = descriptor.type or final.type
#		descriptor.supertypes = self.state.routines[descriptor.type or 'null'].supertypes
#		if 'sequence' in descriptor.supertypes:
#			descriptor.member = descriptor.member or final.member
#			descriptor.length = descriptor.length if descriptor.length is not None else final.length
#		descriptor.supermember = self.state.routines[descriptor.member or 'null'].supertypes
#		return descriptor

#	def scope(self): # Creates new state
		
#		if self.state:
#			self.state = state(self.state)
#		else:
#			self.state = state()
#			self.state.routines = self.values.copy()
#			self.state.namespace = self.types.copy()

#	def unscope(self): # Resolves inner states and unwinds to outer state

#		self.state.outer.inner.append(self.state) # Lol. Lmao
#		self.state = self.state.outer
#		if self.instructions[self.path].name != 'ELSE':
#			self.state.resolve()

#	def bind(self):
#		"""
#		Evaluates type checking for name binding, removing instructions
#		if the type check is known to succeed.
#		"""
#		i, addresses = 0, []
#		while (op := self.instructions[self.path + i]).name != 'BIND':
#			register, name = op.args[0], op.label[0]
#			signature = self.state.namespace[register]
#			item_type = self.state.routines[signature.type]
#			check_type = (self.state.routines[self.state.namespace[name].type] if name in self.state.namespace else item_type) if op.name == 'null' else self.state.routines[op.name]
#			if op.name == 'null' and name not in self.state.namespace: # Untyped, unbound
#				final = signature
#				del self.instructions[self.path + i], self.cache[self.path + i]
#			elif check_type.name in item_type.supertypes: # Successful type check
#				final = check_type.descriptor
#				del self.instructions[self.path + i], self.cache[self.path + i]
#			else: # Unsuccessful type check (delegates check to runtime)
#				final = check_type.descriptor
#				op.name = final.type
#				register = op.register
#				i = i + 1
#			self.state.namespace[name] = final
#			addresses.append(register)
#			op.label = [] # Clear name from label
#		else:
#			op.args = tuple(addresses)
#			op.label = [i for pair in zip([self.state.namespace[name].type for name in op.label], op.label) for i in pair]
#			del self.instructions[self.path - 1], self.cache[self.path - 1]
#			self.path = self.path + i

#	def sequence(self, address, registers):
		
#		signature = [self.state.namespace[i] for i in registers]
#		member = reduce(descriptor.mutual, signature).type
#		signature = descriptor('list', member, len(signature))
#		signature.supertypes = self.state.routines['list'].supertypes
#		signature.supermember = self.state.routines[signature.member].supertypes
#		self.state.namespace[address] = signature

#	def error(self, status, *args):
		
#		debug.debug_error(self.name, self.op.line, status, args)

#class state:
#	"""State object representing the current scope of the program."""
#	def __init__(self, outer = None):

#		if outer:
#			self.routines = outer.routines.copy()
#			self.namespace = outer.namespace.copy()
#			self.outer = outer
#		else:
#			self.routines = {}
#			self.namespace = {}
#			self.outer = None
#		self.inner = [] # Inner states are collected after they are complete

#	def resolve(self):

#		namespace = {}
#		length = len(self.inner)
#		for item in self.inner: # Collect options 
#			for name, option in item.namespace.items():
#				if name in stdlib.builtins:
#					continue
#				if name in namespace:
#					namespace[name].append(option)
#				else:
#					namespace[name] = [option]
#			if len(namespace[name]) < length: # Name not defined in all branches
#				if name in self.namespace:
#					namespace[name].append(self.namespace[name])
#				else:
#					raise NameError(name)
#		for name in namespace: # Take mutual supertype of all options
#			namespace[name] = reduce(descriptor.mutual, namespace[name])
#		self.namespace.update(namespace)
#		self.inner = []

#class cache:
#	"""Cache object describing the pre-determined properties of an instruction."""
#	def __init__(self, tree):

#		self.routine = tree.routine
#		self.final = tree.final
#		self.signature = tree.signature

#	def __str__(self):

#		return ' '.join((str(self.routine), str(self.final), str(self.signature)))