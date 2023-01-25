# ☉ 0.2 06-01-2023

import arche, hemera, kadmos, kleio
import multiprocessing as mp
from fractions import Fraction as real

import cProfile

class process(mp.Process): # Created by function calls and type checking

	def __init__(self, namespace, routine, *args, link = False): # God objects? What is she objecting to?
		
		super().__init__(name = mp.current_process().name + '.' + routine.name, target = self.execute, args = ())
		params = [item.value for item in routine.value[1:]] # Gets coroutine name, return type, and parameters
		types = [item.type for item in routine.value[1:]] # Get types of params
		if len(params) != len(args):
			return self.error('Expected {0} arguments, received {1}'.format(len(params), len(args)))
		self.built_ins = {k.split('_')[1]: v for k, v in globals().items() if k.split('_')[0] == 'sophia'} | arche.operators | arche.functions # No type binding necessary because builtins are never bound to
		self.values = dict(zip(params, args)) # Dict of values for faster access
		self.types = dict(zip(params, types)) # Dict of types for correct typing
		self.supertypes = arche.supertypes # Dict of type hierarchy
		self.namespace = namespace # Reference to shared proxy space
		self.reserved = [item.value for item in routine.value] # List of reserved names in the current namespace
		self.proxy = kleio.proxy(self)
		self.link = link # For linked modules
		self.node = routine # Current node; sets initial module as entry point
		self.path = [0]
		self.data = [] # Unfortunately, a stack
		self.type_data = []

	def execute(self): # Target of run()
		
		pr = cProfile.Profile()
		pr.enable()
		self.namespace[self.pid] = self.proxy # Inserts proxy into namespace hierarchy; PID only exists at runtime
		while self.node: # Runtime loop
			#hemera.debug_process(self)
			if self.path[-1] == -1: # Branch
				self.node = self.node.head # Walk upward
				self.path.pop()
				self.path[-1] = self.path[-1] + 1
			elif self.path[-1] == self.node.length: # Walk up
				self.node = self.node.head # Walk upward
				if self.node:
					self.path.pop()
					self.path[-1] = self.path[-1] + 1
					while self.path[-1] < self.node.length and self.node.nodes[self.path[-1]].branch:
						self.path[-1] = self.path[-1] + 1
				else:
					continue
			else: # Walk down
				self.node = self.node.nodes[self.path[-1]] # Set value to child node
				self.path.append(0)
			if self.path[-1] == self.node.active:
				self.node.start(self)
			elif self.path[-1] == self.node.length:
				self.node.execute(self)
		else:
			if self.link:
				self.proxy.end.poll(None) # Hangs for linked modules
			for routine in mp.active_children(): # Makes sure all child processes are finished before terminating
				if routine.link:
					routine.end.send(None) # Allows linked modules to end
				routine.join()
			hemera.debug_namespace(self)
			del self.namespace[self.pid] # Clear namespace
			pr.disable()
			#pr.print_stats(sort='tottime') # sort as you wish

	def get(self, type_name = 'untyped'): # Data retrieval checks for type

		value = self.data.pop()
		known = self.type_data.pop()
		if known and type_name in self.supertypes[known]: # Instantly succeeds if checked type is supertype of known type
			return value
		else:
			self.cast(value, type_name, known)
			return value

	def send(self, value, type_name = None):
		
		self.data.append(value)
		self.type_data.append(type_name)

	def branch(self, path = -1):

		self.path[-1] = path # Skip nodes

	def bind(self, name, value, type_name = None): # Creates or updates a name binding in main
		
		if name in self.reserved or name in self.built_ins: # Quicker and easier to do it here
			return self.error('Bind to reserved name: ' + name)
		self.values[name] = value # Mutate namespace
		if type_name:
			self.types[name] = type_name
		elif name not in self.types:
			self.types[name] = 'untyped'
		return value

	def unbind(self, name): # Destroys a name binding in the current namespace

		del self.values[name] # Delete binding if it exists in the namespace
		del self.types[name] # Internal method; should never raise KeyError

	def find(self, name, operation = None): # Retrieves a binding's value in its available namespace and optionally checks its type
		
		if name in self.built_ins:
			value = self.built_ins[name]
		elif name in self.values:
			value = self.values[name]
		else:
			return self.error('Undefined name: ' + repr(name))
		if operation:
			type_routine = self.types[name]
			if isinstance(type_routine, type_statement):
				pass
			else:
				operation = getattr(type_routine, operation, None)
				if operation:
					value = [value, operation]
				else:
					return self.error('Undefined type operation: ' + repr(name))
		return value

	def cast(self, value, type_name, known = None): # Checks type of value and returns boolean
		
		type_routine = self.find(type_name)
		stack = [] # Stack of user-defined types, with the requested type at the bottom
		while type_routine.supertype and type_routine is not known: # Known type optimises by truncating stack
			stack.append(type_routine)
			type_routine = self.find(type_routine.supertype) # Type routine is guaranteed to be a built-in when loop ends, so it checks that before any of the types on the stack
		if type_routine(value) is None: # Check built-in type
			return self.error('Failed cast to ' + type_routine.__name__.split('_')[1] + ': ' + repr(value))
		while stack:
			type_routine = stack.pop()
			if type_routine(value) is None:
				return self.error('Failed cast to ' + type_routine.name + ': ' + value)
		else:
			return value # Return indicates success; cast() raises an exception on failure

	def error(self, status): # Error handler
		
		if not isinstance(self.node, assert_statement): # Suppresses error for assert statement
			hemera.debug_error(self.name, status)
			self.end.send(None) # Null return
			self.node = None # Immediately end routine

# Parse tree definitions

class node: # Base node object

	n = 0 # Accumulator for unique index; used for debug info

	def __init__(self, value, *nodes): # Do not store state in nodes
		
		self.n, node.n = node.n, node.n + 1
		self.value = value # For operands that shouldn't be evaluated or that should be handled differently
		self.type = None
		self.head = None # Determined by scope parsing
		self.nodes = [i for i in nodes] # For operands that should be evaluated
		self.length = 0 # Performance optimisation
		self.scope = 0
		self.active = -1 # Indicates path index for activation of start()
		self.branch = False
		self.routine = None

	def __repr__(self):

		return str(self.value)

	def parse(self, data): # Recursively descends into madness and creates a tree of nodes with self as head

		lines, tokens, scopes = [kadmos.line_split(line) for line in data.splitlines() if line], [], [] # Splits lines into symbols and filters empty lines
		for line in lines: # Tokenises each item in lines
			scope = line.count('\t') # Gets scope level from number of tabs
			if not line[scope:]:
				continue # Skips empty lines
			tokens.append([])
			scopes.append(scope)
			for n, symbol in enumerate(line[scope:]): # Skips tabs
				if (symbol[0] in kadmos.characters or symbol[0] in '\'\"') and (symbol not in kadmos.keyword_operators): # Quick test for literal
					if symbol in kadmos.structure_tokens or symbol in kadmos.keyword_tokens:
						token = keyword(symbol)
						if tokens[-1] and tokens[-1][-1].value == 'else':
							tokens[-1].pop()
							token.branch = True
					else:
						if symbol[0] in '.0123456789': # Terrible way to check for a number without using a try/except block
							if '.' in symbol:
								token = literal(real(symbol)) # Cast to real by default
								token.type = 'real' # Type of literal is known at parse time
							else:
								token = literal(int(symbol)) # Cast to int
								token.type = 'integer'
						elif symbol in kadmos.sub_values:
							token = literal(kadmos.sub_values[symbol]) # Interpret booleans and null
							if isinstance(token.value, bool):
								token.type = 'boolean'
							else:
								token.type = None
						elif symbol[0] in '\'\"': # Strings have to be resolved at run time because they're indistinguishable from names otherwise
							token = literal(symbol[1:-1])
							token.type = 'string'
						else:
							token = name(symbol)
							if tokens[-1] and isinstance(tokens[-1][-1], name): # Checks for type
								token_type = tokens[-1].pop().value # Gets type of identifier 
								if token_type in kadmos.sub_types: # Corrects shortened type names
									token_type = kadmos.sub_types[token_type]
								token.type = token_type # Sets type of identifier
				else:
					if symbol in kadmos.parens[0::2]:
						if symbol == '(':
							if tokens[-1] and isinstance(tokens[-1][-1], name):
								token = function_call(symbol)
							else:
								token = parenthesis(symbol)
						elif symbol == '[':
							if tokens[-1] and isinstance(tokens[-1][-1], name):
								token = sequence_index(symbol)
							else:
								token = sequence_literal(symbol)
						elif symbol == '{':
							token = meta_statement(symbol)
					elif symbol in kadmos.parens[1::2]:
						token = right_bracket(symbol)
					elif tokens[-1] and isinstance(tokens[-1][-1], (identifier, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
						if symbol in ('^', ',', ':'):
							token = infix_r(symbol)
						elif symbol == '<-':
							token = bind(symbol)
						elif symbol == '->':
							token = send(symbol)
						else:
							if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and line[-1] == ':': # Special case for operator definition
								token = name(symbol)
								token_type = tokens[-1].pop().value # Gets type of identifier 
								if token_type in kadmos.sub_types: # Corrects shortened type names
									token_type = kadmos.sub_types[token_type]
								token.type = token_type # Sets type of identifier
							else:
								token = infix(symbol)
					else:
						if symbol == '*':
							token = receive(symbol)
						else:
							token = prefix(symbol) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
				tokens[-1].append(token)
				
		parsed = []
		for line in tokens: # Tokenises whole lines
			if line[0].value in kadmos.structure_tokens:
				token = globals()[line[0].value + '_statement'](line) # Cheeky little hack that makes a node for whatever structure keyword is specified
			elif line[0].value in kadmos.keyword_tokens:
				token = line[0] # Keywords will get special handling later
			elif line[-1].value == ':':
				if line[0].type == 'type' and '(' not in [token.value for token in line]:
					token = type_statement(line)
				elif line[0].value[0] in kadmos.characters: # Functions have names and operators have symbols
					token = function_statement(line)
				else:
					token = operator_statement(line)
			elif len(line) > 1 and line[1].value == ':':
				token = assignment(line)
			else: # Tokenises expressions
				token = kadmos.lexer(line).parse() # Passes control to a lexer object that returns an expression tree when parse() is called
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

		node, node.length, path, routines = self, len(self.nodes), [0], [self]
		while node: # Pre-runtime loop completes node linking and sets length
			if path[-1] == node.length: # Walk up
				if isinstance(node, coroutine):
					routines.pop()
				node = node.head # Walk upward
				if node:
					path.pop()
					path[-1] = path[-1] + 1
			else: # Walk down
				node.nodes[path[-1]].head = node # Set head
				node.routine = routines[-1] # Set routine
				node = node.nodes[path[-1]] # Set value to child node
				node.length = len(node.nodes) # Set length
				path.append(0)
				if isinstance(node, coroutine):
					routines.append(self)
		else:
			#hemera.debug_tree(self) # Uncomment for parse tree debug information
			return self

class coroutine(node): # Base coroutine object

	def __init__(self, value):

		super().__init__(value)
		self.active = 0

	def __repr__(self):
		
		return str([str(item.type) + ' ' + str(item.value) for item in self.value])

class module(coroutine): # Module object is always the top level of a syntax tree

	def __init__(self, file_name):

		super().__init__(value = [self]) # Sets initial node to self
		with open(file_name, 'r') as f: # Binds file data to runtime object
			self.file_data = f.read() # node.parse() takes a string containing newlines
		self.name = file_name.split('.')[0]
		self.active = -1
		self.parse(self.file_data) # Here's tree

	def __repr__(self):

		return 'module ' + self.name

	def execute(self, routine):

		if not routine.link:
			routine.end.send(None) # Sends value to return queue
		routine.node = None

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__([tokens[0]]) # Type
		self.name = tokens[0].value
		if len(tokens) > 2: # Naive check for subtyping
			self.supertype = tokens[2].value
			if self.supertype in kadmos.sub_types: # Corrects shortened type names
				self.supertype = kadmos.sub_types[self.supertype]
		else:
			self.supertype = 'untyped'
		self.namespace = [] # Persistent namespace of type operations

	def __call__(self, routine, value): # Initialises type routine
		
		type_routine = process(routine.namespace, self, value) # Create new routine
		type_routine.start() # Start process for routine

	def start(self, routine): # Initialises type
		
		routine.bind(self.name, self, sophia_type)
		for node in self.nodes:
			if isinstance(node, function_statement) and node.value[1].value == self.name: # Detect type operation
				self.namespace.append(node)
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.end.send(routine.find(self.name)) # Sends cast value to return queue upon success
		routine.node = None

class operator_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets operator symbol and a list of parameters as self.value
		self.name = tokens[0].value
		self.types = [item.type for item in self.value]

	def __call__(self, routine, *args):

		x = routine.cast(args[0], self.value[1].type)
		if len(args) > 1:
			y = routine.cast(args[1], self.value[2].type)
			value = process(routine.namespace, self, x, y) # Create new routine
		else:
			value = process(routine.namespace, self, x) # Create new routine
		value.start() # Start process for routine
		return routine.cast(value.proxy.get(), self.type) # Get value immediately

	def start(self, routine):
		
		routine.bind(self.name, self, sophia_operator)
		routine.branch() # Skips body of routine

	def execute(self, routine):

		routine.end.send(None) # Sends value to return queue
		routine.node = None

class function_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name = tokens[0].value

	def start(self, routine):
		
		routine.bind(self.name, self, sophia_function)
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.end.send(None) # Sends value to return queue
		routine.node = None

class assignment(node):

	def __init__(self, tokens): # Supports multiple assignment
		
		names, expressions, stack = [], [], []
		names.append(tokens.pop(0)) # Name
		tokens.pop(0) # Colon
		while tokens:
			token = tokens.pop(0)
			if token.value == ';':
				expressions.append(kadmos.lexer(stack).parse())
				names.append(tokens.pop(0))
				tokens.pop(0)
				stack = []
			else:
				stack.append(token)
		else:
			expressions.append(kadmos.lexer(stack).parse())
			super().__init__(names, *expressions)

	def __repr__(self):

		return 'assignment ' + repr([item.value for item in self.value])

	def execute(self, routine):

		values = []
		types = []
		for i in range(self.length - 1, -1, -1):
			type_name = self.value[i].type
			if not type_name:
				if self.value[i].value in routine.types:
					type_name = routine.types[self.value[i].value]
				else:
					type_name = 'untyped'
			values.append(routine.get(type_name))
			types.append(type_name)
		for i, name in enumerate(self.value):
			routine.bind(name.value, values[-1 - i], types[-1 - i])

class statement(node):

	def __repr__(self):

		if self.branch:
			return 'else ' + type(self).__name__
		else:
			return type(self).__name__

class if_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self, routine):

		condition = routine.get('boolean')
		if not condition:
			routine.branch()

	def execute(self, routine):
		
		return

class while_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self, routine):

		condition = routine.get('boolean')
		if not condition:
			routine.node = routine.node.head # Walk upward
			if routine.node:
				routine.path.pop()
				routine.path[-1] = routine.path[-1] + 1
				while routine.path[-1] < routine.node.length and routine.node.nodes[routine.path[-1]].branch:
					routine.path[-1] = routine.path[-1] + 1

	def execute(self, routine):

		routine.branch(0)

class for_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1], kadmos.lexer(tokens[3:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self, routine):
		
		sequence = arche.iterable(routine.get('sequence')) # Enables fast slice
		try:
			value = next(sequence)
			type_name = self.value.type
			if not type_name:
				if self.value.value in routine.types:
					type_name = routine.types[self.value.value]
				else:
					type_name = 'untyped'
			routine.cast(value, type_name)
			routine.bind(self.value.value, value, type_name)
			routine.send(sequence, 'iterable') # Stack trickery
		except StopIteration:
			routine.branch(self.node.length)

	def execute(self, routine):
		
		sequence = routine.data.pop() # Don't check for type
		type_name = routine.type_data.pop()
		while type_name != 'iterable':
			sequence = routine.data.pop()
			type_name = routine.type_data.pop()
		try:
			value = next(sequence)
			routine.cast(value, routine.types[self.value.value])
			routine.bind(self.value.value, value)
			routine.send(sequence, 'iterable') # Iterable isn't even a type
			routine.branch(1) # Skip start
		except StopIteration:
			routine.unbind(self.value.value)

class assert_statement(statement):

	def __init__(self, tokens):

		nodes, sequence = [], []
		for token in tokens[1:-1]: # Collects all expressions in head statement
			if token.value == ',':
				nodes.append(kadmos.lexer(sequence).parse())
				sequence = []
			else:
				sequence.append(token)
		else:
			nodes.append(kadmos.lexer(sequence).parse())
			super().__init__(None, *nodes)
			self.branch = tokens[0].branch
			self.active = len(nodes)

	def start(self, routine):

		for i in range(self.active):
			if routine.get() is None:
				return routine.branch()

	def execute(self, routine):
		
		return
	
class constraint_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self, routine):
		
		for constraint in self.nodes:
			constraint = routine.get('boolean')
			if not constraint:
				return routine.error('Failed constraint: ' + self.routine.name)

class return_statement(statement):

	def __init__(self, tokens):
		
		if len(tokens) > 1:
			super().__init__(None, kadmos.lexer(tokens[1:]).parse())
		else:
			super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self, routine):
		
		if self.nodes:
			value = routine.get(self.routine.type)
		else:
			value = None
		routine.end.send(value) # Sends value to return queue
		routine.node = None

class link_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1::2]) # Allows multiple links
		self.branch = tokens[0].branch

	def __repr__(self):

		if self.branch:
			return 'else link_statement ' + str([repr(item) for item in self.nodes])
		else:
			return 'link_statement ' + str([repr(item) for item in self.nodes])

	def execute(self, routine):

		for item in self.value:
			name = item.value
			if '.' not in name:
				name = name + '.sophia'
			module_routine = process(routine.namespace, module(name), link = True)
			module_routine.start()
			module_routine.proxy.bound = True
			routine.bind(item.value.split('.')[0], module_routine.proxy, sophia_process)

class else_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		self.branch = True

	def execute(self, routine): # Final else statement
		
		return

class identifier(node): # Generic identifier class

	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = 0

class literal(identifier): # Adds literal behaviours to a node

	def nud(self, lex):

		return self # Gives self as node

	def execute(self, routine): # Literal values are evaluated at parse time
		
		routine.send(self.value, self.type) # Send value to main

class name(identifier): # Adds name behaviours to a node

	def __init__(self, tokens):

		if '.' in tokens:
			super().__init__(tokens.split('.')[0])
			self.operation = tokens.split('.')[1]
		else:
			super().__init__(tokens)
			self.operation = None

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self, routine): # Terminal nodes

		if self.value in routine.types:
			type_name = routine.types[self.value]
		else:
			type_name = self.type
		routine.send(routine.find(self.value, self.operation), type_name)

class keyword(identifier): # Adds keyword behaviours to a node

	def __init__(self, tokens):

		super().__init__(tokens)
		self.active = 0

	def nud(self, lex):

		return self

	def start(self, routine):

		loop = routine.node
		while not isinstance(loop, (while_statement, for_statement)): # Traverses up to closest enclosing loop - bootstrap assumes that interpreter is well-written and one exists
			loop = loop.head
			routine.path.pop()
		routine.node = loop
		if self.value == 'continue':
			if loop.value: # For loop
				if 'iterable' in routine.type_data: # Tests if loop is unbound
					loop.execute(routine)
				else:
					routine.branch(loop.length)
			else:
				routine.branch(0)
		elif self.value == 'break':
			routine.branch()
			if loop.value: # End for loop correctly
				routine.data.pop() # Don't check for type
				type_name = routine.type_data.pop()
				while type_name != 'iterable':
					routine.data.pop()
					type_name = routine.type_data.pop()
				routine.unbind(self.value.value)

	def execute(self, routine):

		return # Shouldn't ever be called anyway

class operator(node): # Generic operator node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = kadmos.bp(value) # Gets binding power of symbol

class prefix(operator): # Adds prefix behaviours to a node

	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = len(kadmos.binding_power) + 1 # Highest possible binding power

	def nud(self, lex):
		
		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self, routine): # Unary operators

		op = routine.find(self.value) # Gets the operator definition
		x = routine.get(op.types[1])
		routine.send(op.unary(x), op.types[0]) # Equivalent for all operators

class receive(prefix): # Defines the receive operator

	def nud(self, lex):

		self.value = lex.parse(self.lbp)
		return self

	def execute(self, routine):
		
		value = routine.messages.recv()
		if self.value.type:
			type_routine = self.value.type
		else:
			type_routine = None
		routine.bind(self.value.value, value, type_routine)
		routine.send(value)

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self, routine):
		
		op = routine.find(self.value) # Gets the operator definition
		x = routine.get(op.types[2])
		y = routine.get(op.types[1]) # Operands are received in reverse order
		routine.send(op.binary(y, x), op.types[0])

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self, routine):

		if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a slice object or a dictionary
			x = routine.get()
			y = routine.get()
			if self.nodes and self.nodes[1].value == ':':
				value = [y] + x
			else:
				value = [y, x]
			if self.head.value == ':':
				routine.send(value)
			else:
				if len(value) == 2:
					routine.send(arche.element(value))
				else:
					routine.send(arche.slice(value))
		elif self.value == ',': # Sorts out comma-separated parameters by returning them as a list
			x = routine.get()
			y = routine.get()
			if self.nodes and self.nodes[1].value == ',':
				value = [y] + x
			else:
				value = [y, x]
			routine.send(value)
		else: # Binary operators
			op = routine.find(self.value) # Gets the operator definition
			x = routine.get(op.types[2])
			y = routine.get(op.types[1])
			routine.send(op.binary(y, x), op.types[0])

class bind(operator): # Defines the bind operator

	def __repr__(self):

		return 'bind ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the left operand like assignment
		
		self.value, self.nodes = left, [lex.parse(self.lbp)]
		return self

	def execute(self, routine):

		value = routine.get() # Yields to main
		if not sophia_process(value):
			return routine.error('Invalid bind')
		value.bound = True
		routine.bind(self.value.value, value, sophia_process) # Binds routine

class send(operator): # Defines the send operator

	def __repr__(self):

		return 'send ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the right operand like assignment
		
		self.nodes, self.value = [left], lex.parse(self.lbp)
		return self

	def execute(self, routine):
		
		value = routine.get(self.routine.type) # Enforce output type for send value
		address = routine.find(self.value.value)
		if not sophia_process(address):
			return routine.error('Invalid send')
		if address.name == routine.name:
			return routine.error('Send source and destination are the same')
		address.send(value, ) # Sends value to destination queue

class left_bracket(operator): # Adds left-bracket behaviours to a node

	def nud(self, lex): # For normal parentheses
		
		if isinstance(lex.peek, right_bracket): # Empty brackets
			self.nodes = []
		else:
			self.nodes = [lex.parse(self.lbp)]
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

	def led(self, lex, left): # For function calls
		
		if isinstance(lex.peek, right_bracket): # Empty brackets
			self.nodes = [left]
		else:
			self.nodes = [left, lex.parse(self.lbp)]
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

class function_call(left_bracket):

	def execute(self, routine):

		if self.length > 1:
			args = routine.get()
			if not isinstance(args, list): # Type correction
				args = [args] # Very tiresome type correction, at that
		else:
			args = []
		function = routine.get()
		if isinstance(function, list): # If type operation:
			args = [function[0]] + args # Shuffle arguments
			function = function[1] # Get actual function
		if isinstance(function, function_statement): # If user-defined:
			routine = process(routine.namespace, function, *args) # Create new routine
			value = kleio.reference(routine.proxy) # Creates future from routine proxy
			routine.start() # Start process for routine
			value.pid = routine.pid # Updates PID
		elif hasattr(function, '__call__'): # If built-in:
			if args: # Python doesn't like unpacking empty tuples
				value = function(*args) # Since value is a Python function in this case
			else:
				value = function()
		else:
			return routine.error(function.__name__ + ' is not a function')
		if sophia_process(value) and not isinstance(self.head, (assignment, bind, send)):
			routine.send(value.get()) # Blocks until function returns
		else:
			routine.send(value)

class parenthesis(left_bracket):

	def execute(self, routine):

		return

class sequence_index(left_bracket):

	def execute(self, routine):
		
		subscript = routine.get()
		value = routine.get()
		if not isinstance(subscript, list):
			subscript = [subscript]
		for i in subscript: # Iteratively accesses the sequence
			if isinstance(i, arche.slice):
				if sophia_sequence(value):
					if i.nodes[1] < -1 * len(value) or i.nodes[1] > len(value): # If out of bounds:
						return routine.error('Index out of bounds')
				else:
					return routine.error('Value not sliceable')
			elif sophia_record(value):
				if i not in value:
					return routine.error('Key not in record: ' + i)
			else:
				if i < -1 * len(value) or i >= len(value): # If out of bounds:
					return routine.error('Index out of bounds')
			if isinstance(i, arche.slice):
				if sophia_string(value):
					value = ''.join([value[n] for n in i]) # Constructs slice of string using range
				elif sophia_list(value):
					value = tuple([value[n] for n in i]) # Constructs slice of list using range
				elif sophia_record(value):
					items = list(value.items())
					value = dict([items[n] for n in i]) # Constructs slice of record using range
			else:
				value = value[i] # Python can handle this bit
		routine.send(value) # Return the accessed value

class sequence_literal(left_bracket):

	def execute(self, routine):
		
		if self.nodes:
			items = routine.get()
		else:
			items = []
		if not isinstance(items, (list, arche.slice)):
			items = [items]
		if items and not isinstance(items, arche.slice) and isinstance(items[0], arche.element): # If items is a key-item pair in a record
			routine.send(dict(iter(items))) # Better way to merge a list of key-value pairs into a record
		else: # If list or slice:
			routine.send(tuple(items)) # Tuple expands slice

class meta_statement(left_bracket):

	def execute(self, routine):
		
		if len(self.nodes) > 1:
			return routine.error('Meta-statement forms invalid expression')
		data = routine.get() # Evaluate string
		self.parse(data) # Run-time parser stage
		self.nodes = [self.nodes[0]]

class right_bracket(operator): # Adds right-bracket behaviours to a node

	def __init__(self, value):

		super().__init__(value)

# Type definitions

class sophia_untyped: # Abstract base class

	types = object
	supertype = None
	
	def __new__(cls, value): # Type check disguised as an object constructor
		
		if cls.types:
			if isinstance(value, cls.types):
				return value
		else:
			for subclass in cls.__subclasses__():
				if subclass(value) is not None:
					return value

class sophia_process(sophia_untyped): # Process/module type
	
	types = kleio.reference

class sophia_routine(sophia_untyped): # Abstract routine type

	types = None # Null types makes __new__ check the types of a type's subclasses

class sophia_type(sophia_routine): # Type type
	
	types = type, type_statement

class sophia_operator(sophia_routine): # Operator type

	types = arche.operator, operator_statement

class sophia_function(sophia_routine): # Function type

	types = sophia_untyped.__new__.__class__, function_statement # Hatred

class sophia_value(sophia_untyped): # Abstract element type

	types = None

class sophia_boolean(sophia_value): # Boolean type

	types = bool

class sophia_number(sophia_value): # Abstract number type

	types = None

class sophia_integer(sophia_number): # Integer type

	types = int

class sophia_real(sophia_number): # Real type

	types = real

class sophia_sequence(sophia_untyped): # Abstract sequence type

	types = None

	def length(self):

		return len(self)

class sophia_string(sophia_sequence): # String type

	types = str

class sophia_list(sophia_sequence): # List type

	types = tuple, arche.slice

class sophia_record(sophia_sequence): # Record type

	types = dict

if __name__ == '__main__': # Hatred
	
	with mp.Manager() as runtime: # The stupidest global state you've ever seen in your life
		
		mp.current_process().name = 'runtime'
		namespace = runtime.dict()
		main = process(namespace, module('test.sophia')) # Spawn initial process
		main.start() # Start initial process
		main.join() # Prevent exit until initial process ends