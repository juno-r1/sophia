'''
The Metis module performs static analysis of a compiled program.
This includes type checking, constant folding/propagation, and dispatch verification.
'''

import aletheia, arche, hemera
from kadmos import instruction

class processor:
	"""Static analysis processor for generated instructions."""
	def __init__(self, instructions, values, types):

		self.name = instructions[0].label[0] if instructions else ''
		self.instructions = instructions
		self.values = arche.builtins | values # Constant in this application
		self.types = arche.types | {k: v.describe(self) for k, v in types.items()}
		self.routines = self.values.copy()
		self.namespace = self.types.copy()
		self.cache = [None for _ in instructions]
		self.path = int(bool(instructions))
		self.op = None
		self.signature = []

	def analyse(self): # Disabled until I can figure out how this is meant to work
	
		[print(i) for i in self.instructions]
		while self.path < len(self.instructions): # This can and does change
			"""
			Initial stage to validate registers and check for reserved binds.
			"""
			self.op = self.instructions[self.path]
			self.path = self.path + 1
			if self.op.name == 'BIND':
				self.bind()
				continue
			elif (address := self.op.register):
				if address in arche.builtins:
					return self.error('BIND', address)
				try:
					method, registers = self.values[self.op.name], self.op.args
					self.signature = [self.namespace[arg] for arg in registers]
				except KeyError as e: # Capture unbound name
					return self.error('FIND', e.args[0])
			else: # Labels
				continue
			"""
			Multiple dispatch algorithm, with help from Julia:
			https://github.com/JeffBezanson/phdthesis
			Binary search tree yields closest key for method, then key is verified.
			"""
			tree = method.tree.true if registers else method.tree.false # Here's tree
			while tree: # Traverse tree; terminates upon reaching leaf node
				tree = tree.true if (tree.index < self.op.arity) and tree.op(self.signature[tree.index]) else tree.false
			if tree is None:
				self.error('DISP', method.name, self.signature)
				continue
			final = tree.final
			try:
				for i, item in enumerate(self.signature): # Verify type signature
					if item > tree.signature[i]:
						self.error('DISP', method.name, self.signature)
						continue
			except IndexError:
				self.error('DISP', method.name, self.signature)
				continue
			"""
			Execute instruction and update registers.
			"""
			self.cache[self.path - 1] = cache(tree)
			self.namespace[address] = final
		#[print(i) for i in self.cache]
		return self

	def complete(self, descriptor, final, value): # Completes descriptor with properties and inferred type of value
		
		descriptor.type = descriptor.type or final.type or aletheia.infer_type(value)
		descriptor.supertypes = self.values[descriptor.type or 'null'].supertypes
		if 'sequence' in descriptor.supertypes:
			descriptor.member = descriptor.member or final.member or aletheia.infer_member(value)
			descriptor.length = descriptor.length or final.length or len(value)
		descriptor.supermember = self.values[descriptor.member or 'null'].supertypes
		return descriptor

	def bind(self):
		"""
		Evaluates type checking for name binding, removing instructions
		if the type check is known to succeed.
		"""
		i, addresses = 0, []
		while (op := self.instructions[self.path + i]).name != 'BIND':
			register, name = op.args[0], op.label[0]
			signature = self.namespace[register]
			item_type = self.routines[signature.type]
			check_type = (self.routines[self.namespace[name].type] if name in self.namespace else item_type) if op.name == 'null' else self.routines[op.name]
			if op.name == 'null' and name not in self.namespace: # Untyped, unbound
				final = signature
				del self.instructions[self.path + i], self.cache[self.path + i]
			elif check_type.name in item_type.supertypes: # Successful type check
				final = check_type.descriptor
				del self.instructions[self.path + i], self.cache[self.path + i]
			else: # Unsuccessful type check (delegates check to runtime)
				final = check_type.descriptor
				op.name = final.type
				register = op.register
				i = i + 1
			self.namespace[name] = final
			addresses.append(register)
			op.label = [] # Clear name from label
		else:
			op.args = tuple(addresses)
			op.label = [i for pair in zip(op.label, [self.namespace[name].type for name in op.label]) for i in pair]
			del self.instructions[self.path - 1], self.cache[self.path - 1]
			self.path = self.path + i

	def error(self, status, *args):
		
		hemera.debug_error(self.name, self.op.line, status, args)

class cache:
	"""Cache object describing the pre-determined properties of an instruction."""
	def __init__(self, tree):

		self.routine = tree.routine
		self.final = tree.final
		self.signature = tree.signature

	def __str__(self):

		return ' '.join((str(self.routine), str(self.final), str(self.signature)))