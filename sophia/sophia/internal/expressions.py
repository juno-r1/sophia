from typing import Any

from .nodes import node, lexer
from .instructions import instruction as ins
from .presets import ALIASES, CONSTANTS

class expression(node):
	"""Base expression node."""
	pass

class identifier(expression):
	"""Generic identifier node."""
	def __init__(
		self,
		tokens: Any | None
		) -> None:
		
		super().__init__(tokens)
		self.lbp = 0

class literal(identifier):
	"""Defines a literal."""
	def __init__(
		self,
		tokens: Any | None
		) -> None:
		
		super().__init__(CONSTANTS[tokens] if tokens in CONSTANTS else tokens)

	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self # Gives self as node

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ()

class name(identifier):
	"""Defines a name."""
	def __init__(
		self,
		tokens: str,
		typename: str
		) -> None:
		
		super().__init__(ALIASES[tokens] if tokens in ALIASES else tokens)
		self.type = typename

	def nud(
		self,
		lex: lexer
		) -> expression:

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(
		self
		) -> tuple[ins, ...]:
		
		if self.type and self.register == '0':
			return ins(self.type, '0', (self.value,)),
		else:
			return ()

class keyword(identifier):
	"""Defines a keyword."""
	def __init__(
		self,
		tokens: str
		) -> None:

		super().__init__(tokens)

	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self

	def execute(
		self
		) -> tuple[ins, ...]:

		loop = self
		while type(loop).__name__ not in ('for_statement', 'while_statement'):
			loop = loop.head
		if self.value == 'continue':
			return ins('LOOP'),
		elif self.value == 'break':
			return ins('BREAK', '', (loop.register, loop.value.value if loop.value else '0')),

class operator(expression):
	"""Generic operator node."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(value)
		for i, level in enumerate(operator.binding_power): # Get binding power of symbol
			if value in level:
				self.lbp = i + 1
				break
		else:
			self.lbp = len(operator.binding_power) # Default binding power; 1 less than unary operators

	binding_power = ( # The left-binding power of a binary operator is expressed by its position in this tuple of tuples
		('(', ')', '[', ']', '{', '}'),
		(',',),
		(':',),
		('->',),
		('if',),
		('else',),
		('or', '||',),
		('and', '&&',),
		('xor', '^^'),
		('=', '!=', 'in'),
		('<', '>', '<=', '>='),
		('&', '|'),
		('+', '-'),
		('*', '/', '%'),
		('^',),
		('?',),
		('.')
	)

class prefix(operator):
	"""Defines a prefix."""
	def __init__(
		self,
		tokens: str
		) -> None:

		super().__init__(tokens)
		self.lbp = len(operator.binding_power) + 1 # Highest possible binding power

	def nud(
		self,
		lex: lexer
		) -> expression:
		
		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins(self.value,
				   self.register,
				   (self.nodes[0].register,)),

class bind(prefix):
	"""Defines the bind operator."""
	def __init__(
		self,
		tokens: str
		) -> None:

		super().__init__(tokens)
		self.type = None

	def __str__(self) -> str: return 'bind ' + self.value

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ()

class receive(prefix):
	"""Defines the receive operator."""
	def __str__(self) -> str: return '>' + self.value.value

	def nud(
		self,
		lex: lexer
		) -> expression:

		self.value = lex.parse(self.lbp)
		return self

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('>', self.register),

class resolve(prefix):
	"""Defines the resolution operator."""
	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('*', self.register, (self.nodes[0].register,)),

class infix(operator):
	"""Defines a left-binding infix."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins(self.value, self.register, (self.nodes[0].register, self.nodes[1].register)),

class left_conditional(infix):
	"""Defines the condition of the conditional operator."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(value)
		self.active = 1
		self.block = True

	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		n = lex.parse(self.lbp)
		left, n.nodes[0] = n.nodes[0], left # Swap for initial execution of condition
		self.nodes = [left, n]
		return self

	def start(
		self
		) -> tuple[ins, ...]:
		
		return ins('.branch', self.register, (self.nodes[0].register,)),

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ()

class right_conditional(infix):
	"""Defines the branches of the conditional operator."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(value)
		self.active = 1

	def start(
		self
		) -> tuple[ins, ...]:
		
		return (ins('BIND', '', (self.nodes[0].register,), label = ['null', self.head.register]),
				ins('.branch', self.register),
				ins('END', line = self.line),
				ins('ELSE', line = self.line)) # Enclosed by labels of left conditional

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('BIND', '', (self.nodes[1].register,), label = ['null', self.head.register]),

class infix_r(operator):
	"""Defines a right-binding infix."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins(self.value, self.register, (self.nodes[0].register, self.nodes[1].register)),

class concatenator(operator):
	"""Defines a concatenator."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:

		n = lex.parse(self.lbp - 1)
		self.nodes = [left] + n.nodes if n.value == self.value else [left, n]
		return self

	def execute(
		self
		) -> tuple[ins, ...]:
		
		if self.value == ':' and len(self.nodes) == 3:
			return ins(':', self.register, tuple(item.register for item in self.nodes)),
		else:
			return ()

class left_bracket(operator):
	"""Generic bracket node."""
	def nud(
		self,
		lex: lexer
		) -> expression: # For normal parentheses
		
		self.nodes = [] if isinstance(lex.peek, right_bracket) else [lex.parse(self.lbp)] # Accounts for empty brackets
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression: # For function calls
		
		self.nodes = [left] if isinstance(lex.peek, right_bracket) else [left, lex.parse(self.lbp)] # Accounts for empty brackets
		lex.use()
		return self

class function_call(left_bracket):
	"""Defines a function call."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression: # For function calls
		
		self.nodes = [left] if isinstance(lex.peek, right_bracket) else [left, lex.parse(self.lbp)] # Accounts for empty brackets
		if len(self.nodes) > 1 and isinstance(self.nodes[1], concatenator): # Unpack concatenator
			self.nodes = [self.nodes[0]] + self.nodes[1].nodes
		lex.use()
		return self

	def execute(
		self
		) -> tuple[ins, ...]:
		
		args = tuple(item.register for item in self.nodes[1:])
		if isinstance(self.head, bind):
			return ins(self.nodes[0].value, self.register, args, label = ['.bind', self.head.value]),
		else:
			names = self.nodes[0].value.split('.')[::-1]
			return [ins(names[0], self.register, args)] + \
				   [ins(item, self.register, (self.register,)) for item in names[1:]]

class parenthesis(left_bracket):
	"""Defines a set of parentheses."""
	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ()

class sequence_index(left_bracket):
	"""Defines a sequence index."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression: # Remove comma operator
		
		if isinstance(lex.peek, right_bracket): # Accounts for empty brackets
			self.nodes = [left]
		else:
			self.nodes = [left, lex.parse(self.lbp)]
			if self.nodes[1].value == ',':
				self.nodes = [left] + [i for i in self.nodes[1].nodes] # Unpack concatenator
		lex.use()
		return self

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return [ins('.index', # Own register is not guaranteed to be the same as the register of the first index
					self.register,
					(self.nodes[0].register, self.nodes[1].register))] + \
			   [ins('.index',
					self.register,
					(self.register, item.register))
				for item in self.nodes[2:]]

class sequence_literal(left_bracket):
	"""Defines a sequence constructor."""

	def nud(
		self,
		lex: lexer
		) -> expression: # For normal parentheses
		
		self.nodes = [] if isinstance(lex.peek, right_bracket) else [lex.parse(self.lbp)] # Accounts for empty brackets
		if self.nodes and self.nodes[0].value == ',': # Unpack concatenator
			self.nodes = self.nodes[0].nodes
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

	def execute(
		self
		) -> tuple[ins, ...]:

		if self.nodes and self.nodes[0].value == ':' and len(self.nodes[0].nodes) == 3:
			return ins('.range', self.register, tuple(i.register for i in self.nodes[0].nodes)),
		elif self.nodes and self.nodes[0].value == ':':
			registers = []
			for item in self.nodes:
				registers = registers + [item.nodes[0].register, item.nodes[1].register]
			return ins('RECORD', '', tuple(registers), label = [self.register]),
		elif self.nodes:
			return ins('LIST', '', tuple(i.register for i in self.nodes), label = [self.register]),
		else:
			return ()

class meta_statement(left_bracket):
	"""Defines a meta-statement."""

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return (ins('.meta', self.register, (self.nodes[0].register)),
				ins('START', label = ['.meta']),
				ins('END'))

class right_bracket(operator):
	"""Defines a right bracket."""
	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self
