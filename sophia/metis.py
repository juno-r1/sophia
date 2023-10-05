'''
The Metis module performs static analysis of a compiled program.
This includes type checking, constant folding/propagation, and dispatch verification.
'''

import arche, hemera

class processor:
	"""Static analysis processor for generated instructions."""
	def __init__(self, instructions, values, types):

		self.name = instructions[0].label[0] if instructions else ''
		self.instructions = instructions
		self.values = arche.builtins | values
		self.types = arche.types | {k: v.describe(self) for k, v in types.items()}
		self.cache = []

	def analyse(self):

		instructions, cache, reserved = [], [], [list(self.values.keys())]
		scope = 0
		for i, op in enumerate(self.instructions): # No backtracking required
			"""
			Prepare instruction, method, and signature.
			"""
			if not op.register: # Labels
				if op.name == 'START':
					scope = scope + 1
				elif op.name == 'END':
					scope = scope - 1
				instructions.append(op)
				cache.append(None)
				continue
			try:
				method, args = self.values[op.name], op.args
				tree = method.tree.true if args else method.tree.false # Here's tree
				signature = [self.types[arg] for arg in args]
			except KeyError:
				self.error('FIND', op.name)
				break
			"""
			Perform dispatch algorithm using known types.
			"""
			while tree: # Traverse tree; terminates upon reaching leaf node
				try:
					tree = tree.true if tree.op(signature[tree.index]) else tree.false
				except IndexError:
					tree = tree.false
			if tree is None:
				break
			routine, final, types = tree.routine, tree.final, tree.signature
			if len(args) != len(types): # Check arity
				break
			for i, item in enumerate(signature): # Verify type signature
				if not item < types[i]:
					break
			"""
			Analyse characteristics of instruction.
			"""
			if final.type != '!': # Suppress write
				self.types[op.register] = final.describe(self)
			if cache[-1] is not None and cache[-1].final.type is None:
				instructions.append(op)
				cache.append(None)
			else:
				instructions.append(op)
				cache.append(tree)
		#[print(i) for i in cache]
		self.instructions, self.cache = instructions, cache
		return self

	def error(self, status, args):
		
		hemera.debug_error(self.name, self.op.line, status, args)