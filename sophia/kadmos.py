'''
The Kadmos module handles Sophia file parsing and instruction generation.
'''

import hemera
from fractions import Fraction as real

characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz' # Sorted by position in UTF-8
parens = '()[]{}'
comment = '//'
structure_tokens = ('if', 'while', 'for', 'else', 'assert', 'return', 'link', 'start')
keyword_tokens = ('continue', 'break', 'is', 'with', 'extends', 'awaits')
keyword_operators = ('not', 'or', 'and', 'xor', 'in')
trailing = (';', ',')
sub_types = {'bool': 'boolean',
			 'int': 'integer', # Lookup table for type names
			 'num': 'number',
			 'str': 'string'}
sub_values = {'true': True, # Lookup table for special values
			  'false': False,
			  'null': None}
binding_power = (('(', ')', '[', ']', '{', '}'), # The left-binding power of a binary operator is expressed by its position in this tuple of tuples
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
				 ('^',))

class node: # Base node object

	def __init__(self, value, *nodes): # Do not store state in nodes
		
		self.value = value # For operands that shouldn't be evaluated or that should be handled differently
		self.type = None
		self.head = None # Determined by scope parsing
		self.nodes = [i for i in nodes] # For operands that should be evaluated
		self.length = 0 # Performance optimisation
		self.scope = 0
		self.line = 0
		self.active = -1 # Indicates path index for activation of start()
		self.branch = False

	def __str__(self): return str(self.value)

	def parse(self, data): # Recursively descends into madness and creates a tree of nodes with self as head
		
		lines = [split(line) for line in group(data.splitlines())] # Splits lines into symbols
		tokens, scopes, i = [], [], 0
		for line in lines: # Tokenises each item in lines
			i = i + 1
			if isinstance(line, str): # Error messages
				hemera.debug_error(self.name, self.source.line if self.source else i, line, ())
				return [] # Executes with empty parse tree
			scope = line.count('\t') # Gets scope level from number of tabs
			if not line[scope:]:
				continue # Skips empty lines
			scopes.append(scope)
			tokens.append([])
			for symbol in line[scope:]: # Skips tabs
				if symbol == '\r': # Increments line count for trailing lines
					i = i + 1
					continue
				elif (symbol[0] in characters or symbol[0] in '\'\"') and (symbol not in keyword_operators): # Quick test for literal
					if symbol in structure_tokens or symbol in keyword_tokens:
						if tokens[-1] and symbol in ('if', 'else') and tokens[-1][-1].value != 'else':
							token = left_conditional(symbol) if symbol == 'if' else right_conditional(symbol)
						else:
							token = keyword(symbol)
							if tokens[-1] and tokens[-1][-1].value == 'else':
								tokens[-1].pop()
								token.branch = True
					else:
						if symbol[0] in '.0123456789': # Terrible way to check for a number without using a try/except block
							token = literal(real(symbol)) # Type of literals is known at parse time
							token.type = 'number'
						elif symbol in sub_values:
							token = literal(sub_values[symbol]) # Interpret booleans and null
							token.type = 'boolean' if isinstance(token.value, bool) else None # Null is caught by untyped
						elif symbol[0] in '\'\"': # Strings have to be resolved at run time because they're indistinguishable from names otherwise
							token = literal(bytes(symbol[1:-1], 'utf-8').decode('unicode_escape')) # Decodes escape characters
							token.type = 'string'
						else:
							token = name(symbol)
							if tokens[-1] and isinstance(tokens[-1][-1], name): # Checks for type
								token_type = tokens[-1].pop().value # Sets type of identifier
								token.type = sub_types[token_type] if token_type in sub_types else token_type # Uses defined name of type
				else:
					if symbol in parens[0::2]:
						if symbol == '(':
							token = function_call(symbol) if tokens[-1] and isinstance(tokens[-1][-1], name) else parenthesis(symbol)
						elif symbol == '[':
							token = sequence_index(symbol) if tokens[-1] and isinstance(tokens[-1][-1], name) else sequence_literal(symbol)
						elif symbol == '{':
							token = meta_statement(symbol)
					elif symbol in parens[1::2]:
						token = right_bracket(symbol)
					elif tokens[-1] and isinstance(tokens[-1][-1], (literal, name, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
						if symbol in (':', ','):
							token = concatenator(symbol)
						elif symbol in ('^', '->'):
							token = infix_r(symbol)
						elif symbol == '<-':
							bind_name = tokens[-1].pop()
							token = bind(bind_name.value)
							token.type = bind_name.type
						else:
							if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and line[-1] == ':': # Special case for operator definition
								token = name(symbol)
								token.type = tokens[-1].pop().value # Sets return type of operator
							else:
								token = infix(symbol)
					else:
						if symbol == '>':
							token = receive(symbol)
						elif symbol == '*':
							token = resolve(symbol)
						else:
							token = prefix(symbol) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
				token.line = i
				tokens[-1].append(token)
				
		parsed = []
		for line in tokens: # Tokenises whole lines
			if line[0].value in structure_tokens:
				token = globals()[line[0].value + '_statement'](line) # Cheeky little hack that makes a node for whatever structure keyword is specified
			elif line[0].value in keyword_tokens:
				token = line[0] # Keywords will get special handling later
			elif line[-1].value == ':':
				if line[0].type == 'type' and '(' not in [token.value for token in line]:
					token = type_statement(line)
				elif line[0].value[0] in characters: # Functions have names and operators have symbols
					if line[1].value == 'awaits':
						token = event_statement(line)
					else:
						token = function_statement(line)
				else:
					token = operator_statement(line)
			elif len(line) > 1 and line[1].value == ':':
				token = assignment(line)
			else: # Tokenises expressions
				token = lexer(line).parse() # Passes control to a lexer object that returns an expression tree when parse() is called
			token.line = line[0].line
			parsed.append(token)

		head, last = self, self # Head token and last line
		for i, line in enumerate(parsed): # Groups lines based on scope
			line.scope = scopes[i] + 1 # Add 1 since main has scope 0
			if line.scope > head.scope + 1: # If entering scope
				head = last # Last line becomes the head node
			elif line.scope < head.scope + 1: # If exiting scope
				if line.scope > 1: # If statement is in local scope:
					for n in parsed[i::-1]: # Find the last line containing the current line in its direct scope, searching backwards from the current line
						if n.scope == line.scope - 1: # If such a line is found:
							head = n # Make it the head node
							break
				else: # If statement is in global scope:
					head = self # Resets head to main node
			head.nodes.append(line) # Link nodes
			last = line
			
		return self

	def generate(self):

		node, node.length, path = self, len(self.nodes), [0]
		instructions = list(self.start())
		while node: # Pre-runtime generation of instructions
			if path[-1] == node.length: # Walk up
				node = node.head # Walk upward
				if node:
					path.pop()
					path[-1] = path[-1] + 1
				else:
					continue
			else: # Walk down
				node.nodes[path[-1]].head = node # Set head
				node = node.nodes[path[-1]] # Set value to child node
				node.length = len(node.nodes) # Set length
				path.append(0)
			if path[-1] == node.active:
				instructions.extend(node.start())
			elif path[-1] == node.length:
				instructions.extend(node.execute())
		if len(instructions) == 1:
			instructions.extend(self.execute())
		return instructions

class coroutine(node): # Base coroutine object

	def __init__(self, value):

		super().__init__(value)
		self.active = 0

	def __str__(self): return str(['{0} {1}'.format(item.type, item.value) for item in self.value])

class module(coroutine): # Module object is always the top level of a syntax tree

	def __init__(self, file_name, root = 'sophia'):

		super().__init__(None) # Sets initial node to self
		with open('{0}\\{1}'.format(root, file_name), 'r') as f: # Binds file data to runtime object
			self.file_data = f.read() # node.parse() takes a string containing newlines
		self.name, self.type = file_name.split('.')[0], 'untyped'
		self.source = None
		self.parse(self.file_data) # Here's tree

	def __str__(self): return 'module ' + self.name

	def start(self): return (self.name, self.type, [], []),

	def execute(self): return (None, -1), ('.return', 1)

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__([tokens[0]]) # Type and type parameter
		self.name, self.type = tokens[0].value, tokens[0].value
		self.supertype = tokens[2].value if len(tokens) > 2 else 'untyped'
		self.interfaces = [token.value for token in tokens[4::2]]
		param = name(tokens[0].value)
		param.type = self.supertype
		self.value.append(param)
		self.namespace = dict() # Persistent namespace of type operations

class event_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([tokens[0]]) # Sets name and message parameter as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.message = tokens[2]
		self.types = [item.type if item.type else 'untyped' for item in self.value]

class operator_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets operator symbol and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.types = [item.type for item in self.value]

class function_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.types = [item.type if item.type else 'untyped' for item in self.value]

class assignment(node):

	def __init__(self, tokens): # Supports multiple assignment
		
		tokens = tokens.copy()
		names, expressions, stack = [], [], []
		names.append(tokens.pop(0)) # Name
		tokens.pop(0) # Colon
		while tokens:
			token = tokens.pop(0)
			if token.value == ';':
				expressions.append(lexer(stack).parse())
				names.append(tokens.pop(0))
				tokens.pop(0)
				stack = []
			else:
				stack.append(token)
		else:
			expressions.append(lexer(stack).parse())
			super().__init__(names, *expressions)

	def __str__(self): return 'assignment ' + str([item.value for item in self.value])

	def execute(self):

		return (([item.type for item in self.value], -1),
				(len(self.nodes), -1),
				('.check', 2),
				([item.value for item in self.value], -1),
				([item.type for item in self.value], -1),
				('.bind', 3))

class statement(node):

	def __str__(self): return ('else ' if self.branch else '') + type(self).__name__

class if_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, lexer(tokens[1:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self):
		
		if self.branch:
			return ('!else', 0), ('!if', 1)
		else:
			return ('!if', 1),

	def execute(self):

		if self.branch:
			return ('!end_if', 0), ('!end_else', 0)
		else:
			return ('!end_if', 0),

class while_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, lexer(tokens[1:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self): return ('!while', 1),

	def execute(self): return ('!end_while', 0),

class for_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1], lexer(tokens[3:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self): return ('!for', 1),

	def execute(self): return ('!end_for', 0),

class assert_statement(statement):

	def __init__(self, tokens):
		
		nodes, sequence, parens = [], [], 0
		for token in tokens[1:-1]: # Collects all expressions in head statement
			if isinstance(token, left_bracket):
				parens = parens + 1
			elif isinstance(token, right_bracket):
				parens = parens - 1
			if token.value == ',' and parens == 0:
				nodes.append(lexer(sequence).parse())
				sequence = []
			else:
				sequence.append(token)
		else:
			nodes.append(lexer(sequence).parse())
		super().__init__(None, *nodes)
		self.branch = tokens[0].branch
		self.active = len(nodes)

	def start(self): return ('.assert', self.active),

	def execute(self): return ('.end_assert', 0),

class return_statement(statement):

	def __init__(self, tokens):
		
		super().__init__(None, lexer(tokens[1:]).parse()) if len(tokens) > 1 else super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self):
		
		if self.nodes:
			return ('.return', 1),
		else:
			return (None, -1), ('.return', 1)

class link_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1::2]) # Allows multiple links
		self.branch = tokens[0].branch

	def __str__(self): return ('else ' if self.branch else '') + 'link_statement ' + str([item.value for item in self.nodes])

class start_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[2::2])
		self.active = 0

	def __str__(self): return 'start ' + str([item.value for item in self.value])

class else_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		self.branch = True
		self.active = 0

	def start(self): return ('!else', 0),

	def execute(self): return ('!end_else', 0),

class identifier(node): # Generic identifier class

	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = 0

class literal(identifier): # Adds literal behaviours to a node

	def nud(self, lex): return self # Gives self as node

	def execute(self): return (self.value, -1),

class name(identifier): # Adds name behaviours to a node

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self): return (self.value, -1), (self.type, -1), ('!name', 1)

class keyword(identifier): # Adds keyword behaviours to a node

	def __init__(self, tokens):

		super().__init__(tokens)
		self.active = 0

	def nud(self, lex): return self

	def execute(self): return ('!' + self.value, 0),

class operator(node): # Generic operator node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = bp(value) # Gets binding power of symbol

class prefix(operator): # Adds prefix behaviours to a node

	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = len(binding_power) + 1 # Highest possible binding power

	def nud(self, lex):
		
		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self): return (self.value, 1),

class bind(prefix): # Defines the bind operator

	def __str__(self): return 'bind ' + self.value

	def execute(self): return (self.value, -1), ('<-', 2)

class receive(prefix): # Defines the receive operator

	def __str__(self): return '>' + self.value.value

	def nud(self, lex):

		self.value = lex.parse(self.lbp)
		return self

	def execute(self): return (self.value.value, -1), ('>', 1)

class resolve(prefix): # Defines the resolution operator

	def execute(self): return ('.resolve', 1),

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self): return (self.value, 2),

class left_conditional(infix): # Defines the conditional operator

	def __init__(self, value):

		super().__init__(value)
		self.active = 1

	def led(self, lex, left):
		
		n = lex.parse(self.lbp)
		left, n.nodes[0] = n.nodes[0], left # Swap for initial execution of condition
		self.nodes = [left, n]
		return self

	def execute(self): return ('.if', 1),

class right_conditional(infix): # Defines the conditional operator

	def __init__(self, value):

		super().__init__(value)
		self.active = 1

	def start(self): return ('.end_if', 0), ('.else', 0)

	def execute(self): return ('.end_else', 0),

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self): return (self.value, 2),

class concatenator(operator): # Adds comma behaviours to a node

	def led(self, lex, left):

		n = lex.parse(self.lbp - 1)
		if n.value == self.value:
			self.nodes = [left] + n.nodes
		else:
			self.nodes = [left, n]
		return self

	def execute(self):
		
		if self.value == ':':
			return (self.value, len(self.nodes)),
		else:
			return (len(self.nodes), -1), ('.concatenate', 1) # n-ary comma operator

class left_bracket(operator): # Adds left-bracket behaviours to a node

	def nud(self, lex): # For normal parentheses
		
		self.nodes = [] if isinstance(lex.peek, right_bracket) else [lex.parse(self.lbp)] # Accounts for empty brackets
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

	def led(self, lex, left): # For function calls
		
		self.nodes = [left] if isinstance(lex.peek, right_bracket) else [left, lex.parse(self.lbp)] # Accounts for empty brackets
		lex.use()
		return self

class function_call(left_bracket):

	def execute(self): return ('.call' if isinstance(self.head, bind) else '.spawn', 2),

class parenthesis(left_bracket): pass

class sequence_index(left_bracket):

	def execute(self): return ('.index', 2),

class sequence_literal(left_bracket):

	def execute(self):
		
		if self.nodes:
			return ('.sequence', 1),
		else:
			return ([], -1), ('.sequence', 1)

class meta_statement(left_bracket):

	def __init__(self, value):

		super().__init__(value)
		self.active = 1

	def execute(self): return ('.meta', 1)

class right_bracket(operator): # Adds right-bracket behaviours to a node

	def nud(self, lex): return self

class lexer: # Lex object to get around not being able to peek the next value of an iterator

	def __init__(self, tokens):

		self.lexes = (iter(tokens), iter(tokens))
		self.token = None
		self.peek = next(self.lexes[1])

	def use(self): # Gets the next tokens

		self.token = next(self.lexes[0])
		try:
			self.peek = next(self.lexes[1])
		except StopIteration:
			self.peek = eol()

	def parse(self, lbp = 0): # Pratt parser for expressions - takes a lex construct and the left-binding power

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

	# https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
	# https://abarker.github.io/typped/pratt_parsing_intro.html
	# https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
	# https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

class eol: # Sentinel object

	def __init__(self): self.lbp = -1

def group(lines): # Groups lines with trailing characters

	if not lines:
		return []
	grouped = [lines[0]]
	for line in lines[1:]:
		if grouped[-1] and grouped[-1][-1] in trailing:
			i = 0
			while line[i] in ('\t', ' '):
				i = i + 1
			grouped[-1] = grouped[-1] + '\r' +  line[i:]
		else:
			grouped.append(line)
	return grouped

def split(line): # Takes a line from the file data and splits it into tokens
	
	tokens = []
	if not balanced(line):
		return 'UPRN' # Unmatched parentheses
	while line:
		shift = False # Push flag
		symbol = ''
		while not shift: # Constructs token
			symbol, line = symbol + line[0], line[1:]
			if symbol == comment: # Comments
				return tokens # Comment ends line
			elif symbol[-1] == ' ':
				symbol = symbol[:-1]
				if symbol:
					shift = True
				else:
					break
			elif symbol in ('\t', '\n', ':', ';', ',') or (symbol in parens) or (line and line[0] in parens):
				shift = True
			elif symbol in '\'\"': # Strings
				try:
					end = line.index(symbol) + 1 # Everything before this index is inside a string
					symbol, line = symbol + line[0:end], line[end:]
					shift = True
				except ValueError:
					return 'UQTE' # Unmatched parentheses
			elif not line or (symbol[-1] in characters) != (line[0] in characters): # XOR for last and next character being part of an operator
				shift = True
		else:
			tokens.append(symbol)
	return tokens

def balanced(tokens): # Takes a string and checks if its parentheses are balanced
	
	opening = parens[0::2] # Gets all opening parentheses from string
	closing = parens[1::2] # Gets all closing parentheses from string
	string = ''
	stack = [] # Guess

	for token in tokens:
		if string:
			if token == string:
				string = ''
			else:
				continue
		elif token in '\'\"':
			string = token
		if token in opening: # If character is an opening parenthesis:
			stack.append(token) # Add to stack
		elif token in closing: # If character is a closing parenthesis:
			if not stack or token != closing[opening.index(stack.pop())]: # If the stack is empty or c doesn't match the item popped off the stack:
				return False # Parentheses are unbalanced
	else:	
		return not stack # Interprets stack as a boolean, where an empty stack is falsy

	# https://stackoverflow.com/questions/6701853/parentheses-pairing-issue

def bp(symbol):

	for i, level in enumerate(binding_power):
		if symbol in level:
			return i + 1
	else:
		return len(binding_power) # Default binding power; 1 less than unary operators