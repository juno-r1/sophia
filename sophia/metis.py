'''
The Metis module performs static analysis of a compiled program.
This includes type checking, constant folding/propagation, and dispatch verification.
'''

import arche, hemera
from aletheia import descriptor
from kadmos import instruction

class processor:
	"""Static analysis processor for generated instructions."""
	def __init__(self, instructions, values, types):

		self.name = instructions[0].label[0] if instructions else ''
		self.instructions = instructions
		self.result = [self.instructions[0]]
		self.values = arche.builtins | values # Constant in this application
		self.types = arche.types | {k: v.describe(self) for k, v in types.items()}
		self.cache = [None for _ in instructions]
		self.path = int(bool(instructions))
		self.op = None
		self.signature = []

	#def analyse(self): # Disabled until I can figure out how this is meant to work
		
	#	scope = routine(self.name)
	#	"""
	#	Initial pass to validate registers and check for reserved binds.
	#	"""
	#	for op in self.instructions:
	#		if op.register:
	#			if op.register in arche.builtins:
	#				self.op = op
	#				return self.error('BIND', op.register)
	#			scope.add(op)
	#	for name in scope.references:
	#		if name not in self.values:
	#			self.op = op
	#			return self.error('FIND', name)
	#	return self
	#	lol. lmao

	def error(self, status, *args):
		
		hemera.debug_error(self.name, self.op.line, status, args)

class routine:
	"""Routine object that stores data describing its scope."""
	def __init__(self, name, instruction = None):

		self.name = name
		self.namespace = {} # Namespace of the routine at each call site
		self.calls = {} # Instructions that this routine calls that aren't built-ins
		self.addresses = {instruction.register} | set(instruction.label[1::2]) if instruction else set() # Registers that this routine binds to that *are* in the current scope
		self.references = set() # Registers that this routine reads from that *aren't* in the current scope

	def add(self, instruction):
		
		if instruction.name not in self.namespace:
			self.namespace[instruction.name] = self.addresses.copy()
		if instruction.name not in arche.builtins and instruction.name not in self.calls:
			self.calls[instruction.name] = routine(instruction.name, instruction)
		self.references = self.references | set((arg for arg in instruction.args if arg not in self.addresses))
		self.addresses = self.addresses | {instruction.register}

	def __str__(self):

		return '{0}\nCalls\t\t{1}\nAddresses\t{2}\nReferences\t{3}'.format(self.name, self.calls, self.addresses, self.references)