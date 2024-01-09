import re
from typing import Any

from . import presets
from .nodes import node
from .instructions import instruction as ins
from ..datatypes.mathos import real

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
		string: str
		) -> None:
		
		self.iterator = re.finditer(presets.REGEX_LEXER, string.strip())
		self.token = None
		self.peek = None
		self.use()

	def use(
		self
		) -> None:
		"""
		Gets the next tokens, ignoring whitespace.
		The iterator has a guaranteed sentinel value, so no exception will be raised.
		"""
		self.token, self.peek = self.peek, next(self.iterator)
		value = self.peek.group()
		match self.peek.lastgroup:
			case 'sentinel': # End of string
				token = eol()
			case 'number':
				token = number(value)
			case 'string':
				token = string(value)
			case 'literal' if value in presets.KEYWORDS_INFIX:
				token = infix(value)
			case 'literal' if value in presets.KEYWORDS_PREFIX:
				token = prefix(value)
			case 'literal' if value in presets.CONSTANTS:
				token = constant(value)
			case 'literal' if value == 'if' and self.token:
				token = left_conditional(value)
			case 'literal' if value == 'else':
				token = right_conditional(value)
			case 'literal':
				token = name(value)
			case 'l_parens' if value == '(':
				token = parenthesis(value) if self.prefix() else function_call(value)
			case 'l_parens' if value == '[':
				token = sequence_literal(value) if self.prefix() else sequence_index(value)
			case 'l_parens' if value == '{':
				token = meta_statement(value)
			case 'r_parens':
				token = right_bracket(value)
			case 'operator' if value in (':', ','): # Same regardless of context
				token = concatenator(value)
			case 'operator' if self.prefix(): # Prefixes
				if value == '>':
					token = receive(value)
				elif value == '*':
					token = resolve(value)
				else:
					token = prefix(value)
			case 'operator' if value in presets.INFIX_R: # Infixes
				token = infix_r(value)
			case 'operator':
				if value == '<-':
					token = bind(value)
				else:
					token = infix(value)
		self.peek = token
			#case 'operator' if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and ('=>' in line or line[-1] == ':'): # Special case for operator definition
			#	pass
			#	token = nodes.name(value)
			#if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and ('=>' in line or line[-1] == ':'): # Special case for operator definition
			#	token = name(symbol)
			#	token_type = tokens[-1].pop().value # Sets return type of operator
			#	token.type = sub_types[token_type] if token_type in sub_types else token_type

	def parse(
		self,
		lbp: int = 0
		) -> node:
		"""
		LBP: left-binding power
		NUD: null denotation (prefixes)
		LED: left denotation (infixes)
		"""
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

	def prefix(
		self,
		) -> bool:
		"""
		Determines whether a symbol is a prefix based on the properties of the last token.
		"""
		return not self.token \
			   or isinstance(self.token, operator) \
			   and not isinstance(self.token, right_bracket)

class eol:
	"""Sentinel object for the lexer."""
	def __init__(self) -> None: self.lbp = -1

class expression(node):
	"""Base expression node."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__()
		self.value = value # Node representation

	def __str__(self) -> str: return self.value

class identifier(expression):
	"""Generic identifier node."""
	def __init__(
		self,
		value: Any
		) -> None:
		
		super().__init__(value)
		self.lbp = 0

class literal(identifier):
	"""Defines a literal."""
	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self # Gives self as node

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ()

class number(literal):
	"""Defines a number."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(real.read(value))

	def __str__(self) -> str: return str(self.value)

class string(literal):
	"""Defines a string."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(bytes(value[1:-1], 'utf-8').decode('unicode_escape'))

class constant(literal):
	"""Defines a constant literal."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(presets.CONSTANTS[value])

	def __str__(self) -> str: return str(self.value)

class name(identifier):
	"""Defines a name."""
	def __init__(
		self,
		value: str
		) -> None:
		
		super().__init__(presets.ALIASES[value] if value in presets.ALIASES else value)

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
		
		return ()

class keyword(identifier):
	"""Defines a keyword."""
	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self

class keyword_continue(keyword):
	"""Defines the continue keyword."""
	def execute(
		self
		) -> tuple[ins, ...]:

		loop = self
		while type(loop).__name__ not in ('for_statement', 'while_statement'):
			loop = loop.head
		return ins('.continue', '0'),

class keyword_break(identifier):
	"""Defines the break keyword."""
	def execute(
		self
		) -> tuple[ins, ...]:

		loop = self
		while type(loop).__name__ not in ('for_statement', 'while_statement'):
			loop = loop.head
		return ins('.break', '0', (loop.register, loop.index if hasattr(loop, 'index') else '0')),

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
		('<-',),
		('.')
	)

class prefix(operator):
	"""
	Defines a prefix.
	All unary operators have the highest possible left-binding power.
	NEGATION TAKES PRECEDENCE OVER EXPONENTIATION.
	"""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(value)
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
		
		return ins('if', self.register, (self.nodes[0].register,)),

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
		
		return (ins('.bind', '0', (self.nodes[0].register,), label = [self.head.register]),
				ins('if', self.register),
				ins('END'),
				ins('ELSE')) # Enclosed by labels of left conditional

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('.bind', '0', (self.nodes[1].register,), label = [self.head.register]),

class bind(infix):
	"""Defines the bind operator."""
	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('.future', self.register, tuple([self.nodes[0].register] + [i.register for i in self.nodes[1].nodes])),

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
			return ins('.slice', self.register, tuple(item.register for item in self.nodes)),
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
		
		return ins(self.nodes[0].register, self.register, tuple(item.register for item in self.nodes[1:])),

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
		
		return [ins('[', self.register, (self.nodes[0].register, self.nodes[1].register))] + \
			   [ins('[', self.register, (self.register, item.register)) for item in self.nodes[2:]]

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
			return ins('.record', self.register, tuple(i.nodes[1].register for i in self.nodes), label = [i.nodes[0].register for i in self.nodes]),
		elif self.nodes:
			return ins('.list', self.register, tuple(i.register for i in self.nodes)),
		else:
			return () # Empty list is a constant

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