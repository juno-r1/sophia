'''
The Kadmos module handles Sophia file parsing and instruction generation.
'''

import hemera
from aletheia import infer
from rationals import Rational as real

characters = '.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz' # Sorted by position in UTF-8
parens = '()[]{}'
comment = '//'
structure_tokens = ('if', 'while', 'for', 'else', 'assert', 'return', 'link', 'start')
keyword_tokens = ('continue', 'break', 'is', 'with', 'extends', 'awaits')
keyword_operators = ('not', 'or', 'and', 'xor', 'in', 'new')
trailing = (';', ',')
sub_types = {'bool': 'boolean', # Lookup table for type names
			 'int': 'integer',
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

class instruction:
	"""Instruction used in the virtual machine"""
	__slots__ = ('name', 'register', 'args', 'line', 'label', 'arity')

	def __init__(self, name, register, args = (), line = 0, label = []):

		self.name = name
		self.register = register
		self.args = args
		self.line = line
		self.label = label
		self.arity = len(args)

	def __str__(self): # Convert instruction to string

		return ' '.join([str(self.line), self.name, self.register] + list(self.args)) + '; ' + ' '.join(self.label)

	@classmethod
	def read(cls, value): # Convert string to instruction

		command, label = value.split(';')
		command, label = command.split(' '), label.split(' ')
		line, name, register, args = int(command[0]), command[1], command[2], tuple(command[3:])
		return cls(name, register, args, line, label)

	@classmethod
	def rewrite(cls, ins, old, new): # Rewrite instruction for subtypes

		args = tuple(new if i == old else i for i in ins.args)
		label = [new if i == old else i for i in ins.label]
		return cls(ins.name, ins.register, args, line = ins.line, label = label)

class translator:
	"""Generates a list of instructions from a syntax tree."""
	def __init__(self, node, constants = 0):
		
		self.start = node
		self.node = node
		self.path = [0]
		self.constant = constants # Constant register counter
		self.instructions = [instruction('START', '', label = [node.name])]
		self.values = {'0': None, '&0': None} # Register namespace
		self.types = {'0': 'null', '&0': 'null'} # Register types

	def generate(self, offset = 0):
		
		self.node.length = len(self.node.nodes)
		while self.node: # Pre-runtime generation of instructions
			if self.path[-1] == self.node.length: # Walk up
				if isinstance(self.node.head, assert_statement) and self.path[-2] < self.node.head.active: # Insert assertion
					self.instructions.append(instruction('.assert',
														 '0',
														 (self.node.register,),
														 line = self.node.line))
				elif isinstance(self.node.head, type_statement) and self.path[-2] >= self.node.head.active: # Insert constraint
					self.instructions.append(instruction('.constraint',
														 '0',
														 (self.node.register,),
														 line = self.node.line,
														 label = [self.node.head.value[0].value] if self.path[-2] == self.node.head.length - 1 else []))
				self.node = self.node.head # Walk upward
				if self.node:
					self.path.pop()
					self.path[-1] = self.path[-1] + 1
				else:
					continue
			else: # Walk down
				self.node.nodes[self.path[-1]].head = self.node # Set head
				self.node = self.node.nodes[self.path[-1]] # Set value to child node
				self.node.register = self.register(offset)
				self.node.length = len(self.node.nodes)
				self.node.scope = len(self.path)
				self.path.append(0)
				if not isinstance(self.node, for_statement):
					if self.node.branch:
						self.instructions.append(instruction('ELSE', '', line = self.node.line))
					elif self.node.block:
						self.instructions.append(instruction('START', '', line = self.node.line))
				if isinstance(self.node, event_statement):
					self.node.value = self.node.value + self.node.nodes[0].value
			if self.path[-1] == self.node.active:
				instructions = self.node.start()
			elif self.path[-1] == self.node.length:
				instructions = self.node.execute()
			else:
				instructions = []
			for x in instructions:
				x.line = self.node.line
			self.instructions.extend(instructions)
			if self.path[-1] == self.node.length and self.node.block:
				self.instructions.append(instruction('END', '', line = self.node.line))
		if len(self.instructions) == 1: # Adds instruction for empty program
			self.instructions.extend(self.start.execute())
		self.instructions.append(instruction('END', ''))
		return self.instructions, self.values, self.types

	def register(self, offset):
		
		if self.node.nodes: # Temporary register
			if isinstance(self.node.head, assert_statement):
				return '0' # 0 is the return register and is assumed to be nullable
			elif isinstance(self.node.head, bind):
				return self.node.head.value # Sure, I guess
			else:
				index = str(sum(self.path) + offset + 1) # Sum of path is a pretty good way to minimise registers
				self.values[index] = None
				self.types[index] = 'untyped'
				return index
		else:
			if isinstance(self.node, name): # Variable register
				return '0' if isinstance(self.node.head, assert_statement) else self.node.value
			elif isinstance(self.node, receive):
				return self.node.value.value
			elif self.node.value is None: # Null value is interned so that instructions can reliably take null as an operand
				return '&0'
			else: # Constant register
				self.constant = self.constant + 1
				index = '&' + str(self.constant)
				value = () if isinstance(self.node, sequence_literal) else self.node.value
				self.values[index] = value
				self.types[index] = infer(value)
				return index

class node:
	"""Base node object."""
	def __init__(self, value, *nodes): # Do not store state in nodes
		
		self.value = value # For operands that shouldn't be evaluated or that should be handled differently
		self.type = None
		self.head = None # Determined by scope parsing
		self.nodes = [i for i in nodes] # For operands that should be evaluated
		self.register = '0' # Register that this node returns to
		self.length = 0 # Performance optimisation
		self.line = 0
		self.scope = 0
		self.active = -1 # Indicates path index for activation of start()
		self.branch = False # Else statement
		self.block = False # Generates start and end labels

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
							token.type = infer(token.value) # Number or integer
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
						elif symbol in ('^', '->', '=>'):
							token = infix_r(symbol)
						elif symbol == '<-':
							bind_name = tokens[-1].pop()
							token = bind(bind_name.value)
							token.type = bind_name.type
						else:
							if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and ('=>' in line or line[-1] == ':'): # Special case for operator definition
								token = name(symbol)
								token_type = tokens[-1].pop().value # Sets return type of operator
								token.type = sub_types[token_type] if token_type in sub_types else token_type
							else:
								token = infix(symbol)
					else:
						if symbol == '>':
							token = receive(symbol)
						elif symbol == '*':
							token = resolve(symbol)
						else:
							if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and ('=>' in line or line[-1] == ':'): # Special case for operator definition
								token = name(symbol)
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
			elif line[-1].value == ':' or '=>' in [token.value for token in line]:
				if line[0].type == 'type' and '(' not in [token.value for token in line[:line.index('=>') if '=>' in line else -1]]:
					token = type_statement(line)
				elif line[1].value == 'awaits':
					token = event_statement(line)
				else:
					token = function_statement(line)
			elif len(line) > 1 and line[1].value == ':':
				token = assignment(line)
			elif len(line) > 1 and line[1].value == 'is':
				token = alias(line)
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

class statement(node):
	"""Base statement node."""
	def __str__(self): return ('else ' if self.branch else '') + type(self).__name__

class coroutine(statement):
	"""Base coroutine node."""
	def __init__(self, value):

		super().__init__(value)
		self.active = 0

	def __str__(self): return str(['{0} {1}'.format(item.type, item.value) for item in self.value])

class module(coroutine):
	"""Base module node. This is always the top node of a syntax tree."""
	def __init__(self, file_name, root = 'sophia', meta = ''):

		super().__init__(None) # Sets initial node to self
		self.type = 'untyped'
		self.active = -1
		if meta:
			self.name = meta
			self.source = None
			self.parse(file_name)
		else:
			with open('{0}\\{1}'.format(root, file_name), 'r') as f: # Binds file data to runtime object
				self.file_data = f.read() # node.parse() takes a string containing newlines
			self.name = file_name.split('.')[0]
			self.source = None
			self.parse(self.file_data) # Here's tree

	def __str__(self): return 'module ' + self.name

	def execute(self): return instruction('.return', '0', ('&0',)), # Default end of module

class type_statement(coroutine):
	"""Defines a type definition."""
	def __init__(self, tokens):
		
		super().__init__([tokens[0]]) # Sets name as value
		self.name, self.type = tokens[0].value, tokens[0].value
		values = [token.value for token in tokens]
		i, supertype, prototype = 1, None, False
		if i < len(tokens) and values[i] == 'extends':
			supertype = values[i + 1]
			supertype, i = sub_types[supertype] if supertype in sub_types else supertype, i + 2
		if i < len(tokens) and values[i] == 'with':
			j = values.index('=>') if '=>' in values else len(tokens)
			self.nodes, i = [lexer(tokens[i + 1:j]).parse()], j
			prototype = True
		if i < len(tokens) and values[i] == '=>':
			self.nodes, i = self.nodes + [lexer(tokens[i + 1:]).parse()], len(tokens)
		self.supertype, self.active = supertype if supertype else 'untyped', int(prototype)

	def start(self):

		if self.active: # Necessary to check type of prototype
			return (instruction(self.supertype, self.register, (self.nodes[0].register,)),
					instruction('.type', self.name, (self.supertype, self.register)),
					instruction('START', '', label = [self.name]))
		else:
			return (instruction('.type', self.name, (self.supertype,)),
					instruction('START', '', label = [self.name]))

	def execute(self): return (instruction('.return', '0', (self.name,)),
							   instruction('END', ''))

class event_statement(coroutine):
	"""Defines an event definition."""
	def __init__(self, tokens):

		super().__init__([tokens[0]]) # Sets name and message parameter as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.message = tokens[2]

	def start(self):

		names = [item.value for item in self.value]
		types = [item.type if item.type else 'untyped' for item in self.value]
		return (instruction('.event', self.name, label = [i for pair in zip(types, names) for i in pair] + [self.message.type, self.message.value]),
				instruction('START', '', label = [self.name]))

	def execute(self):

		if self.type:
			return (instruction(self.type, self.register, ('&0',)),
					instruction('.return', '0', ('&0',)),
					instruction('END', ''))
		else:
			return (instruction('.return', '0', ('&0',)),
					instruction('END', ''))

class function_statement(coroutine):
	"""Defines a function definition."""
	def __init__(self, tokens):

		try: # Single-line function definition
			i = [token.value for token in tokens].index('=>')
			super().__init__([token for token in tokens[0:i:2] if token.value != ')'])
			self.nodes = [return_statement(tokens[i::])]
		except ValueError:
			super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type

	def start(self):
		
		names = [item.value for item in self.value]
		types = [item.type if item.type else 'untyped' for item in self.value]
		return (instruction('.function', self.name, label = [i for pair in zip(types, names) for i in pair]),
				instruction('START', '', label = [self.name]))

	def execute(self): 
		
		if self.type:
			return (instruction(self.type, self.register, ('&0',)),
					instruction('.return', '0', ('&0',)),
					instruction('END', ''))
		else:
			return (instruction('.return', '0', ('&0',)),
					instruction('END', ''))

class assignment(statement):
	"""Defines an assignment."""
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

	def execute(self): return [instruction('.bind',
										   str(int(self.register) + i),
										   (self.nodes[i].register, item.type) if item.type else (self.nodes[i].register,),
										   label = [item.value])
										   for i, item in enumerate(self.value)] + \
							  [instruction(item.type if item.type else 'untyped',
										   item.value,
										   (str(int(self.register) + i),))
										   for i, item in enumerate(self.value)] # Single-line function!

class alias(statement):
	"""Defines a type alias."""
	def __init__(self, tokens): super().__init__(tokens[0], lexer(tokens[2:]).parse())

	def __str__(self): return 'alias ' + str(self.value.value)

	def execute(self): return instruction('.alias', self.value.value, (self.nodes[0].register,)),

class if_statement(statement):
	"""Defines an if statement."""
	def __init__(self, tokens):

		super().__init__(None, lexer(tokens[1:-1]).parse())
		self.active = 1
		self.branch = tokens[0].branch
		self.block = True

	def start(self): return instruction('.branch', self.register, (self.nodes[0].register,)),

	def execute(self): return instruction('.branch', self.register),

class while_statement(statement):
	"""Defines a while statement."""
	def __init__(self, tokens):

		super().__init__(None, lexer(tokens[1:-1]).parse())
		self.active = 1
		self.branch = tokens[0].branch
		self.block = True

	def start(self): return instruction('.branch', self.register, (self.nodes[0].register,)),

	def execute(self): return instruction('.loop', self.register),

class for_statement(statement):
	"""Defines a for statement."""
	def __init__(self, tokens):

		super().__init__(tokens[1], lexer(tokens[3:-1]).parse())
		self.active = 1
		self.branch = tokens[0].branch
		self.block = True

	def start(self): 
		
		adjacent = str(int(self.register) + 1) # Uses the register of the first enclosed statement
		return (instruction('.iterator', self.register, (self.nodes[0].register,)),
				instruction('ELSE' if self.branch else 'START', '', line = self.line),
				instruction('.next', adjacent, (self.register,)),
				instruction('.unloop', '0', (adjacent,), label = [self.value.value]), # Equivalent to Python's StopIteration check
				instruction('.bind', self.value.value, ('0', self.value.type) if self.value.type else ('0',), label = [self.value.value]),
				instruction(self.value.type if self.value.type else 'untyped', self.value.value, (self.value.value,)))

	def execute(self): return instruction('.loop', '0'),

class assert_statement(statement):
	"""Defines an assertion."""
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
		self.active = len(nodes)
		self.branch = tokens[0].branch
		self.block = True

	def start(self): return ()

	def execute(self): return instruction('.branch', self.register),

class return_statement(statement):
	"""Defines a return statement."""
	def __init__(self, tokens):
		
		super().__init__(None, lexer(tokens[1:]).parse()) if len(tokens) > 1 else super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self): 
		
		routine = self
		while not isinstance(routine, coroutine):
			routine = routine.head
		type_name = routine.type
		if type_name and not isinstance(routine, module):
			return (instruction(type_name, self.register, (self.nodes[0].register if self.nodes else self.register,)),
					instruction('.return', '0', (self.nodes[0].register if self.nodes else '&0',)))
		else:
			return instruction('.return', '0', (self.nodes[0].register if self.nodes else '&0',)),

class link_statement(statement):
	"""Defines a link."""
	def __init__(self, tokens):

		super().__init__(tokens[1::2]) # Allows multiple links
		self.branch = tokens[0].branch

	def __str__(self): return ('else ' if self.branch else '') + 'link_statement ' + str([item.value for item in self.nodes])

	def execute(self): return [instruction('.link', item.value) for item in self.value]

class start_statement(statement):
	"""Defines an initial."""
	def __init__(self, tokens): super().__init__(tokens[2::2])

	def __str__(self): return 'start ' + str([item.value for item in self.value])

	def execute(self): return (instruction('.return', '0', ('&0',)),
							   instruction('END', ''),
							   instruction('EVENT', '', label = [self.head.message.value]),
							   instruction(self.head.message.type, self.head.message.value, (self.head.message.value,)))

class else_statement(statement):
	"""Defines an else statement."""
	def __init__(self, tokens):

		super().__init__(None)
		self.branch = True
		self.block = True

	def execute(self): return ()

class identifier(node):
	"""Generic identifier node."""
	def __init__(self, tokens):
		
		super().__init__(tokens)
		self.lbp = 0

class literal(identifier):
	"""Defines a literal."""
	def nud(self, lex): return self # Gives self as node

	def execute(self): return ()

class name(identifier):
	"""Defines a name."""
	def __init__(self, tokens):
		
		super().__init__(sub_types[tokens] if tokens in sub_types else tokens)

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self):
		
		if self.type and self.register == '0':
			return instruction(self.type, '0', (self.value,)),
		else:
			return ()

class keyword(identifier):
	"""Defines a keyword."""
	def __init__(self, tokens):

		super().__init__(tokens)

	def nud(self, lex): return self

	def execute(self):

		loop = self
		while not isinstance(loop, (while_statement, for_statement)):
			loop = loop.head
		if self.value == 'continue':
			return instruction('.loop', '0'),
		elif self.value == 'break':
			return instruction('.break', loop.value.value if isinstance(loop, for_statement) else '0', (loop.register,)),

class operator(node):
	"""Generic operator node."""
	def __init__(self, value):

		super().__init__(value)
		self.lbp = bp(value) # Gets binding power of symbol

class prefix(operator):
	"""Defines a prefix."""
	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = len(binding_power) + 1 # Highest possible binding power

	def nud(self, lex):
		
		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self): return instruction(self.value,
										  self.register,
										  (self.nodes[0].register,)),

class bind(prefix):
	"""Defines the bind operator."""
	def __str__(self): return 'bind ' + self.value

	def execute(self): return ()

class receive(prefix):
	"""Defines the receive operator."""
	def __str__(self): return '>' + self.value.value

	def nud(self, lex):

		self.value = lex.parse(self.lbp)
		return self

	def execute(self): return instruction('>', self.register),

class resolve(prefix):
	"""Defines the resolution operator."""
	def execute(self): return instruction('*', self.register, (self.nodes[0].register,)),

class infix(operator):
	"""Defines a left-binding infix."""
	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self): return instruction(self.value,
										  self.register,
										  (self.nodes[0].register, self.nodes[1].register)),

class left_conditional(infix):
	"""Defines the condition of the conditional operator."""
	def __init__(self, value):

		super().__init__(value)
		self.active = 1
		self.block = True

	def led(self, lex, left):
		
		n = lex.parse(self.lbp)
		left, n.nodes[0] = n.nodes[0], left # Swap for initial execution of condition
		self.nodes = [left, n]
		return self

	def start(self): return instruction('.branch', self.register, (self.nodes[0].register,)),

	def execute(self): return ()

class right_conditional(infix):
	"""Defines the branches of the conditional operator."""
	def __init__(self, value):

		super().__init__(value)
		self.active = 1

	def start(self): return (instruction('untyped', self.head.register, (self.nodes[0].register,)),
						     instruction('.branch', self.register),
							 instruction('END', '', line = self.line),
							 instruction('ELSE', '', line = self.line)) # Enclosed by labels of left conditional

	def execute(self): return instruction('untyped', self.head.register, (self.nodes[1].register,)),

class infix_r(operator):
	"""Defines a right-binding infix."""
	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self): return instruction(self.value,
										  self.register,
										  (self.nodes[0].register, self.nodes[1].register)),

class concatenator(operator):
	"""Defines a concatenator."""
	def led(self, lex, left):

		n = lex.parse(self.lbp - 1)
		self.nodes = [left] + n.nodes if n.value == self.value else [left, n]
		return self

	def execute(self):
		
		if self.value == ':':
			return instruction(':', self.register, tuple(item.register for item in self.nodes)),
		else:
			return [instruction('.concatenate',
								self.register,
								(self.nodes[0].register,) if i == 0 else (self.register, item.register))
								for i, item in enumerate(self.nodes)]

class left_bracket(operator):
	"""Generic bracket node."""
	def nud(self, lex): # For normal parentheses
		
		self.nodes = [] if isinstance(lex.peek, right_bracket) else [lex.parse(self.lbp)] # Accounts for empty brackets
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

	def led(self, lex, left): # For function calls
		
		self.nodes = [left] if isinstance(lex.peek, right_bracket) else [left, lex.parse(self.lbp)] # Accounts for empty brackets
		lex.use()
		return self

class function_call(left_bracket):
	"""Defines a function call."""
	def execute(self):
		
		if isinstance(self.nodes[1], concatenator): # Unpack concatenator
			self.nodes = [self.nodes[0]] + self.nodes[1].nodes
		args = tuple(item.register for item in self.nodes[1:])
		if isinstance(self.head, bind):
			return instruction(self.nodes[0].value, self.register, args, label = ['.bind', self.head.value]),
		else:
			names = self.nodes[0].value.split('.')[::-1]
			return [instruction(names[0], self.register, args)] + \
				   [instruction(item, self.register, (self.register,)) for item in names[1:]]

class parenthesis(left_bracket):
	"""Defines a set of parentheses."""
	def execute(self): return ()

class sequence_index(left_bracket):
	"""Defines a sequence index."""
	def led(self, lex, left): # Remove comma operator
		
		if isinstance(lex.peek, right_bracket): # Accounts for empty brackets
			self.nodes = [left]
		else:
			self.nodes = [left, lex.parse(self.lbp)]
			if self.nodes[1].value == ',':
				self.nodes = [left] + [i for i in self.nodes[1].nodes] # Unpack concatenator
		lex.use()
		return self

	def execute(self): return [instruction('.index', # Own register is not guaranteed to be the same as the register of the first index
										   self.register,
										   (self.nodes[0].register, self.nodes[1].register))] + \
							  [instruction('.index',
										   self.register,
										   (self.register, item.register))
										   for item in self.nodes[2:]]

class sequence_literal(left_bracket):
	"""Defines a sequence constructor."""
	def execute(self):
		
		return (instruction('.sequence', self.register, (self.nodes[0].register,)),) if self.nodes else ()

class meta_statement(left_bracket):
	"""Defines a meta-statement."""
	def __init__(self, value): super().__init__(value)

	def execute(self): return (instruction('.meta', self.register, (self.nodes[0].register)),
							   instruction('START', '', label = ['.meta']),
							   instruction('END', ''))

class right_bracket(operator):
	"""Defines a right bracket."""
	def nud(self, lex): return self

class lexer:
	"""
	Implements a Pratt parser for expressions.
	"""
	# These sources helped with expression parsing:
	# https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
	# https://abarker.github.io/typped/pratt_parsing_intro.html
	# https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
	# https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

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

class eol:
	"""Sentinel object for the lexer."""
	def __init__(self): self.lbp = -1

def group(lines): # Groups lines with trailing characters and splits single-line definitions

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
					return 'UQTE' # Unmatched quotes
			elif not line or (symbol[-1] in characters) != (line[0] in characters): # XOR for last and next character being part of an operator
				shift = True
		else:
			tokens.append(symbol)
	return tokens

def balanced(tokens): # Takes a string and checks if its parentheses are balanced
	
	opening, closing = parens[0::2], parens[1::2] # Gets all opening parentheses from string
	string, stack = '', []
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