from sys import stderr

class node:
	"""Base node object."""
	def __init__(
		self,
		*nodes: tuple):
		
		self.head = None # Determined by scope parsing
		self.nodes = [i for i in nodes] # Node operands
		self.length = 0 # Performance optimisation
		self.register = '0' # Register that this node returns to
		self.scope = 0
		self.active = -1 # Indicates path index for activation of start()
		self.branch = False # Else statement
		self.block = False # Generates start and end labels

	def debug(
		self,
		level: int = 0
		) -> None:
	
		print(('. ' * level) + str(self), file = stderr)
		if self.nodes: # True for non-terminals, false for terminals
			level += 1 # This actually works, because parameters are just local variables, for some reason
			for item in self.nodes:
				item.debug(level)
		if level == 1:
			print('===', file = stderr)