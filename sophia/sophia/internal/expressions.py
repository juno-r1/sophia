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

	def use(self) -> None:
		"""
		Gets the next tokens, ignoring whitespace.
		The iterator has a guaranteed sentinel value, so no exception will be raised.
		"""
		self.token, self.peek = self.peek, next(self.iterator)
		value = self.peek.group()
		match self.peek.lastgroup:
			case 'sentinel': # End of string
				token = eol()
			case 'env':
				token = name(value)
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
			case 'l_parens' if value == '(' and self.prefix():
				value = self.collect(value)
				if re.fullmatch(presets.REGEX_TYPE_EXPR, value):
					token = type_expression(value)
				elif re.fullmatch(presets.REGEX_EVNT_EXPR, value):
					token = event_expression(value)
				elif re.fullmatch(presets.REGEX_FUNC_EXPR, value):
					token = function_expression(value)
				else:
					token = parenthesis(value)
			case 'l_parens' if value == '(':
				token = function_call(value)
			case 'l_parens' if value == '[' and self.prefix():
				token = sequence_literal(self.collect(value))
			case 'l_parens' if value == '[':
				token = sequence_index(value)
			case 'l_parens' if value == '{':
				token = meta(self.collect(value))
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

	def collect(
		self,
		symbol: str
		) -> str:
		"""
		Collects the contents of a set of brackets.
		"""
		string, count = '', 1
		while count:
			value = next(self.iterator).group()
			if value == symbol:
				count = count + 1
			elif value == presets.PARENS[symbol]:
				count = count - 1
				if not count:
					break
			string = string + ' ' + value
		return string.strip()

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

	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self

class literal(identifier):
	"""Defines a literal."""
	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self # Gives self as node

	def execute(self) -> tuple[ins, ...]:
		
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
	def nud(
		self,
		lex: lexer
		) -> expression:

		return self # Gives self as node

	def execute(self) -> tuple[ins, ...]:
		
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
	def execute(self) -> tuple[ins, ...]:

		loop = self
		while type(loop).__name__ not in ('for_statement', 'while_statement'):
			loop = loop.head
		return ins('.continue', '0'),

class keyword_break(identifier):
	"""Defines the break keyword."""
	def execute(self) -> tuple[ins, ...]:

		loop = self
		while type(loop).__name__ not in ('for_statement', 'while_statement'):
			loop = loop.head
		return ins('.break', '0', [loop.register, loop.index if hasattr(loop, 'index') else '0']),

class parenthesis(identifier):
	"""Defines a parenthetical expression."""
	def __init__(
		self,
		value: Any
		) -> None:
		
		super().__init__('(')
		self.nodes = [lexer(value).parse()] if value else []

	def execute(self) -> tuple[ins, ...]:
		
		return ()

class sequence_literal(identifier):
	"""Defines a sequence constructor."""
	def __init__(
		self,
		value: Any
		) -> None:
		
		super().__init__('[')
		if not value: # Accounts for empty brackets
			self.nodes = []
		else:
			expr = lexer(value).parse()
			self.nodes = expr.nodes if expr.value == ',' else [expr]

	def execute(self) -> tuple[ins, ...]:
		
		if self.nodes and self.nodes[0].value == ':' and len(self.nodes[0].nodes) == 3:
			return ins('.range', self.register, [i.register for i in self.nodes[0].nodes]),
		elif self.nodes and self.nodes[0].value == ':':
			return ins('.record', self.register, [i.nodes[1].register for i in self.nodes], label = [i.nodes[0].register for i in self.nodes]),
		elif self.nodes:
			return ins('.list', self.register, [i.register for i in self.nodes]),
		else:
			return () # Empty list is a constant

class meta(identifier):
	"""Defines a meta-expression."""
	def __init__(
		self,
		value: Any
		) -> None:
		
		super().__init__('{')
		self.nodes = [lexer(value).parse()]

	def execute(self) -> tuple[ins, ...]:
		
		return ins('.meta', self.register, [self.nodes[0].register]),

class anonymous(identifier):
	"""Defines an anonymous routine."""
	def __init__(
		self,
		name: str,
		final: str,
		params: dict[str, str]
		) -> None:

		super().__init__(name)
		self.active = 0
		self.name = name
		self.final = final
		self.params = params

class type_expression(anonymous):
	"""Defines a type expression."""
	def __init__(
		self, 
		string: str
		) -> None:
		
		string, expression = re.split(r'=>\s*', string, 1)
		name = '@'
		supertype = re.split(' ', re.search(r'extends \w+', string).group(), 1)[1]
		prototype = re.split(' ', re.search(r'with .+', string).group(), 1)[1] if 'with' in string else ''
		super().__init__(name, name, {name: supertype})
		if prototype:
			self.nodes.append(lexer(prototype).parse())
		if expression:
			self.nodes.append(lexer(expression).parse())
		self.active = int(bool(prototype))

	def start(self) -> tuple[ins, ...]:
		
		if self.active: # Necessary to check type of prototype
			return (ins('.check', self.register, [self.nodes[0].register, self.params[self.name]]),
					ins('.type', self.register, [self.params[self.name], self.register], label = [self.name]),
					ins('START', label = [self.name]))
		else:
			return (ins('.type', self.register, [self.params[self.name]], label = [self.name]),
					ins('START', label = [self.name]))

	def execute(self) -> tuple[ins, ...]:
		
		return (ins('.constraint', '0'),
				ins('END'))

class event_expression(anonymous):
	"""Defines a type expression."""
	def __init__(
		self,
		string: str
		) -> None:

		string, expression = re.split(r'\s*=>\s*', string, 1)
		expression, final = re.split(r'\s*=>\s*(?=\w+$)', expression, 1) if re.search(r'(?<==>)\s*\w+$', expression) else (expression, 'any')
		string = re.split(' ', re.search(r'awaits \w+( \w+)?', string).group(), 1)[1]
		check, message = re.split(r' ', string, 1) if ' ' in string else ('any', string)
		params = {'@': final, message: check}
		super().__init__('@', final, params)
		self.nodes = [lexer(expression).parse()]

	def start(self) -> tuple[ins, ...]:
		
		message, check = list(self.params.items())[1]
		return (ins('.event', self.register, list(self.params.values()), label = list(self.params.keys())),
				ins('START', label = [self.name]),
				ins('return', '0'),
				ins('END'),
				ins('EVENT', label = [message]),
				ins('BIND'),
				ins('.check', message, [message, check]),
				ins('.bind', '0', label = [message]))

	def execute(self) -> tuple[ins, ...]:
		
		return (ins('return', '0', [self.nodes[0].register]),
				ins('END'))

class function_expression(anonymous):
	"""Defines a type expression."""
	def __init__(
		self,
		string: str
		) -> None:
		
		string, expression = re.split(r'\s*=>\s*', string, 1)
		expression, final = re.split(r'\s*=>\s*(?=\w+$)', expression, 1) if re.search(r'(?<==>)\s*\w+$', expression) else (expression, 'any')
		params = {'@': final}
		for value in re.finditer(r'\w+( \w+)?', string):
			param = value.group()
			typename, param = re.split(r' ', param, 1) if ' ' in param else ('any', param)
			params[param] = typename
		super().__init__('@', final, params)
		self.nodes = [lexer(expression).parse()]

	def start(self) -> tuple[ins, ...]:
		
		return (ins('.function', self.register, list(self.params.values()), label = list(self.params.keys())),
				ins('START', label = [self.name]))

	def execute(self) -> tuple[ins, ...]:
		
		return (ins('return', '0', [self.nodes[0].register]),
				ins('END'))

class operator(expression):
	"""Generic operator node."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(value)
		for i, level in enumerate(presets.BP): # Get binding power of symbol
			if value in level:
				self.lbp = i + 1
				break
		else:
			self.lbp = len(presets.BP) # Default binding power; 1 less than unary operators

class prefix(operator):
	"""
	Defines a prefix.
	All unary operators have the same left-binding power.
	NEGATION TAKES PRECEDENCE OVER EXPONENTIATION.
	"""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(value)
		for i, level in enumerate(presets.BP): # Pre-determined binding power
			if 'PREFIX' in level:
				self.lbp = i + 1
				break

	def nud(
		self,
		lex: lexer
		) -> expression:
		
		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self) -> tuple[ins, ...]:
		
		return ins(self.value,
				   self.register,
				   [self.nodes[0].register]),

class receive(prefix):
	"""Defines the receive operator."""
	def __str__(self) -> str: return '>' + self.value.value

	def nud(
		self,
		lex: lexer
		) -> expression:

		self.value = lex.parse(self.lbp)
		return self

	def execute(self) -> tuple[ins, ...]:
		
		return ins('>', self.register),

class resolve(prefix):
	"""Defines the resolution operator."""
	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('*', self.register, [self.nodes[0].register]),

class infix(operator):
	"""Defines a left-binding infix."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self) -> tuple[ins, ...]:
		
		return ins(self.value, self.register, [self.nodes[0].register, self.nodes[1].register]),

class bind(infix):
	"""Defines the bind operator."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		self.nodes = [left]
		right = lex.parse(self.lbp)
		if not right.nodes: # Unpack parenthesis
			return self
		elif right.nodes[0].value == ',':
			self.nodes = self.nodes + right.nodes[0].nodes
		else:
			self.nodes = self.nodes + [right.nodes[0]]
		return self

	def execute(self) -> tuple[ins, ...]:
		
		return ins('.future', self.register, [i.register for i in self.nodes]),

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

	def start(self) -> tuple[ins, ...]:
		
		return ins('if', self.register, [self.nodes[0].register]),

	def execute(self) -> tuple[ins, ...]:
		
		return ()

class right_conditional(infix):
	"""Defines the branches of the conditional operator."""
	def __init__(
		self,
		value: str
		) -> None:

		super().__init__(value)
		self.active = 1

	def start(self) -> tuple[ins, ...]:
		
		return (ins('.bind', '0', [self.nodes[0].register], label = [self.head.register]),
				ins('if', self.register),
				ins('END'),
				ins('ELSE')) # Enclosed by labels of left conditional

	def execute(self) -> tuple[ins, ...]:
		
		return ins('.bind', '0', [self.nodes[1].register], label = [self.head.register]),

class infix_r(operator):
	"""Defines a right-binding infix."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self) -> tuple[ins, ...]:
		
		return ins(self.value, self.register, [self.nodes[0].register, self.nodes[1].register]),

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

	def execute(self) -> tuple[ins, ...]:
		
		if self.value == ':' and len(self.nodes) == 3:
			return ins('.slice', self.register, [item.register for item in self.nodes]),
		else:
			return ()

class left_bracket(operator):
	"""
	Generic bracket node.
	Brackets have unbalanced binding power;
	they bind high on the left side and low on the right side.
	"""
	def nud(
		self,
		lex: lexer
		) -> expression:
		
		self.nodes = [] if isinstance(lex.peek, right_bracket) else [lex.parse(1)] # Accounts for empty brackets
		#lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

class function_call(left_bracket):
	"""Defines a function call."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		if isinstance(lex.peek, right_bracket): # Accounts for empty brackets
			self.nodes = [left]
		else:
			right = lex.parse(1) # Unbalanced binding power
			self.nodes = [left] + right.nodes if right.value == ',' else [left, right]
		lex.use()
		return self

	def execute(self) -> tuple[ins, ...]:
		
		return ins(self.nodes[0].register, self.register, [item.register for item in self.nodes[1:]]),

class sequence_index(left_bracket):
	"""Defines a sequence index."""
	def led(
		self,
		lex: lexer,
		left: expression
		) -> expression:
		
		if isinstance(lex.peek, right_bracket): # Accounts for empty brackets
			self.nodes = [left]
		else:
			right = lex.parse(1) # Unbalanced binding power
			self.nodes = [left] + right.nodes if right.value == ',' else [left, right]
		lex.use()
		return self

	def execute(self) -> tuple[ins, ...]:
		
		return [ins('[', self.register, [self.nodes[0].register, self.nodes[1].register])] + \
			   [ins('[', self.register, [self.register, item.register]) for item in self.nodes[2:]]

class right_bracket(operator):
	"""Defines a right bracket."""
	def nud(
		self,
		lex: lexer
		) -> expression:
		
		return self