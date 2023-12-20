from sys import stderr
from typing import Any

class node:
	"""Base node object."""
	def __init__(
		self,
		value: Any | None,
		*nodes: tuple):
		
		self.value = value # For operands that shouldn't be evaluated or that should be handled differently
		self.head = None # Determined by scope parsing
		self.nodes = [i for i in nodes] # For operands that should be evaluated
		self.length = 0 # Performance optimisation
		self.register = '0' # Register that this node returns to
		self.line = 0
		self.column = 0
		self.scope = 0
		self.active = -1 # Indicates path index for activation of start()
		self.branch = False # Else statement
		self.block = False # Generates start and end labels

	def __str__(self) -> str: return str(self.value)

	def debug(
		self,
		level: int = 0
		) -> None:
	
		print(str(self.line).zfill(4) + '\t' + ('  ' * level) + str(self), file = stderr)
		if self.nodes: # True for non-terminals, false for terminals
			level += 1 # This actually works, because parameters are just local variables, for some reason
			for item in self.nodes:
				item.debug(level)
		if level == 1:
			print('===', file = stderr)

class lexer:
	"""
	Implements a Pratt parser for expressions.
	These sources helped with expression parsing:
	https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
	https://abarker.github.io/typped/pratt_parsing_intro.html
	https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
	https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html
	"""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		self.lexes = (iter(tokens), iter(tokens))
		self.token = None
		self.peek = next(self.lexes[1])

	def use( # Gets the next tokens
		self
		) -> None:

		self.token = next(self.lexes[0])
		try:
			self.peek = next(self.lexes[1])
		except StopIteration:
			self.peek = eol()

	def parse( # LBP stands for "left-binding power"
		self,
		lbp: int = 0
		) -> node:

		self.use()
		if isinstance(self.peek, eol): # Detects end of expression
			return self.token # End-of-line token
		left = self.token.nud(self) # Executes null denotation of current token
		while lbp < self.peek.lbp:
			self.use()
			left = self.token.led(self, left) # Executes left denotation of current token
			if isinstance(self.peek, eol): # Detects end of expression
				return left # Returns expression tree
		else:
			return left # Preserves state of next_token for higher-level calls

class eol:
	"""Sentinel object for the lexer."""
	def __init__(self) -> None: self.lbp = -1