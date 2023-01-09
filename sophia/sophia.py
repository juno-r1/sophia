# ☉ 0.2 06-01-2023

import arche, hemera, kadmos, kleio
import multiprocessing as mp
from fractions import Fraction as real

class process(mp.Process): # Created by function calls and type checking

	def __init__(self, namespace, routine, *args, link = False): # God objects? What is she objecting to?
		
		super().__init__(name = mp.current_process().name + '.' + routine.name, target = self.execute, args = args)
		self.type = routine.type
		self.supertype = routine.supertype # Supertype of type routine
		self.instances = []
		self.path = [0]
		self.node = routine # Current node; sets initial module as entry point
		self.value = None # Current value
		self.namespace = namespace # Reference to shared namespace hierarchy
		self.reserved = [] # List of reserved names in the current namespace
		self.link = link # For linked modules
		self.proxy = arche.proxy(self)
		self.messages, self.proxy.messages = mp.Pipe() # Pipe to receive messages
		self.end, self.proxy.end = mp.Pipe() # Pipe to send return value
		self.ready = mp.Event() # Signal to indicate that the routine has been initialised successfully

	def __repr__(self):

		return ' '.join((str(getattr(self.node, 'n', 0)).zfill(4), self.name, str(self.path[-1]), repr(self.node)))

	def execute(self, *args): # Target of run()
		
		params = self.node.value[1:] # Gets coroutine name, return type, and parameters
		types = [item.type for item in params] # Get types of params
		if len(params) != len(args):
			return self.error('Expected {0} arguments, received {1}'.format(len(params), len(args)))
		args = [self.cast(arg, params[i].type) for i, arg in enumerate(args)] # Check type of args against params
		params = [item.value for item in params] # Get names of params
		self.reserved = params
		self.namespace[self.pid] = kleio.namespace(params, args, types) # Updates namespace hierarchy
		self.ready.set() # Go!
		self.instances.append(self.node.execute(self)) # Start routine
		self.instances[-1].send(None)
		while self.node: # Runtime loop
			hemera.debug_process(self)
			if self.node.nodes and 0 <= self.path[-1] < len(self.node.nodes): # Walk down
				self.node.nodes[self.path[-1]].head = self.node # Sets child head to self
				self.node = self.node.nodes[self.path[-1]] # Set value to child node
				self.path.append(0)
				self.instances.append(self.node.execute(self)) # Initialises generator
				if isinstance(self.node, coroutine):
					self.branch() # Skips body of routine
				if isinstance(self.node, type_statement): # Initialises type routine
					self.node.prepare(self)
				else:
					self.value = self.instances[-1].send(None) # Somehow, it's never necessary to send a value down the tree
			else: # Walk up
				self.instances.pop() # Removes generator
				self.node = self.node.head # Walk upward
				self.path[-2] = self.path[-2] + 1
				if self.path.pop() != -1: # Skip else statements if not branch
					while self.path[-1] < len(self.node.nodes) and isinstance(self.node.nodes[self.path[-1]], else_statement):
						self.path[-1] = self.path[-1] + 1
				self.value = self.instances[-1].send(self.value)
				if isinstance(self.node, (coroutine, return_statement)) and self.path[-1] == len(self.node.nodes): # Check if finished
					self.node = None # Can't send to self
		else:
			if self.link:
				self.proxy.end.poll(None) # Hangs for linked modules
			for routine in mp.active_children(): # Makes sure all child processes are finished before terminating
				if routine.link:
					routine.end.send(None) # Allows linked modules to end
				routine.join()
			hemera.debug_namespace(self)
			del self.namespace[self.pid] # Clear namespace

	def branch(self, path = -1):

		self.path[-1] = path # Skip nodes

	def control(self, status): # Chaos... control!

		loop = self.node
		while not isinstance(loop, (while_statement, for_statement)): # Traverses up to closest enclosing loop - bootstrap assumes that interpreter is well-written and one exists
			loop = loop.head
			self.instances.pop()
			self.path.pop()
		if status == 'continue':
			self.node = loop
			self.branch(len(self.node.nodes))
			self.instances[-1].send(None) # I mean, it's not pretty, but it works
		elif status == 'break':
			self.node = loop
			self.branch()

	def bind(self, name, value, type_routine = None, pid = None): # Creates or updates a name binding in main
		
		if not pid:
			pid = self.pid
			if self.namespace[1].read(name) or name in self.reserved: # Quicker and easier to do it here
				return self.error('Bind to reserved name: ' + name)
		namespace = self.namespace[pid] # Retrieve routine namespace
		if type_routine:
			namespace.write_type(name, type_routine)
			self.cast(value, type_routine)
		else:
			type_routine = namespace.read_type(name)
			if type_routine:
				self.cast(value, type_routine)
			else:
				namespace.write_type(name, sophia_untyped) # Unnecessary to cast to untyped
		namespace.write(name, value) # Mutate namespace
		self.namespace[0].acquire() # Acquires namespace lock
		self.namespace[pid] = namespace # Update shared dict; nested objects don't sync unless you make them
		self.namespace[0].release() # Releases namespace lock
		return value

	def unbind(self, name): # Destroys a name binding in the current namespace
		
		namespace = self.namespace[self.pid] # Retrieve routine namespace
		namespace.delete(name) # Delete binding from namespace
		self.namespace[0].acquire() # Acquires namespace lock
		self.namespace[self.pid] = namespace # Update shared dict; nested objects don't sync unless you make them
		self.namespace[0].release() # Releases namespace lock

	def find(self, name): # Retrieves a binding's value in its available namespace
		
		names = name.split('.')
		value = self.namespace[1].read(names[0]) # Searches built-ins first; built-ins are independent of namespaces
		if value:
			return value
		pid = self.pid
		while pid in self.namespace:
			value = self.namespace[pid].read(names[0])
			if value:
				if sophia_process(value) and (not value.bound or value.end.poll()): # If the name is associated with an unbound or finished routine:
					value = self.bind(names[0], value.get(), pid = pid) # Is it breaking encapsulation if the target routine is finished when this happens?
				break
			else:
				pid = self.namespace[pid].parent
		for n in names[1:]:
			if sophia_process(value): # Access process namespace
				pid = value.pid
				self.namespace[0].acquire() # Lock is necessary to ensure any outstanding binds are complete
				value = self.namespace[pid].read(n)
				self.namespace[0].release()
			else: # Get type operation instead
				if n != names[-1]: # Type operations have to be the last specified name
					break
				type_routine = self.namespace[pid].read_type(names[-2]) # Guaranteed to exist because it checks on bind
				if isinstance(type_routine, type_statement):
					op = type_routine.namespace.read(n) # Get type operation
				else: # Built-in types are Python types and built-in type operations are Python type methods
					op = getattr(type_routine, n, None) # Get built-in type method
				value = [value, op] # Return list of value and type operation
		else:
			return value
		return self.error('Undefined name: ' + repr(name))

	def cast(self, value, type_routine): # Checks type of value and returns boolean
		
		error = repr(value)
		if not type_routine: # For literals of unspecified type
			return value
		stack = [] # Stack of user-defined types, with the requested type at the bottom
		while isinstance(type_routine, type_statement):
			stack.append(type_routine)
			type_routine = self.find(type_routine.supertype) # Type routine is guaranteed to be a built-in when loop ends, so it checks that before any of the types on the stack
		if type_routine(value) is None: # Check built-in type
			return self.error('Failed cast to ' + type_routine.__name__ + ': ' + error)
		while stack:
			if type_routine(value) is None:
				return self.error('Failed cast to ' + type_routine.name + ': ' + error)
		else:
			return value # Return indicates success; cast() raises an exception on failure

	def error(self, status): # Error handler
		
		if not isinstance(self.node.head, assert_statement): # Suppresses error for assert statement
			hemera.debug_error(self.name, status)
			self.end.send(None) # Null return
			self.node = None # Immediately end routine

# Parse tree definitions

class node: # Base node object

	n = 0 # Accumulator for unique index; used for debug info

	def __init__(self, value, *nodes): # Do not store state in nodes

		self.n, node.n = node.n, node.n + 1
		self.value = value # For operands that shouldn't be evaluated or that should be handled differently
		self.nodes = [i for i in nodes] # For operands that should be evaluated
		self.scope = 0
		self.head = None

	def __repr__(self):

		return str(self.value)

	def routine(self): # Gets node's routine node

		routine = self
		while not isinstance(routine, coroutine):
			routine = routine.head
		else:
			return routine

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
					else:
						if symbol in '.0123456789': # Terrible way to check for a number without using a try/except block
							if '.' in symbol:
								token = literal(real(symbol)) # Cast to real by default
							else:
								token = literal(int(symbol)) # Cast to int
						elif symbol in kadmos.sub_values:
							token = literal(kadmos.sub_values[symbol]) # Interpret booleans and null
						elif symbol[0] in '\'\"': # Strings have to be resolved at run time because they're indistinguishable from names otherwise
							token = literal(symbol[1:-1])
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
							if isinstance(tokens[-1][-1], name):
								token = function_call(symbol)
							else:
								token = parenthesis(symbol)
						elif symbol == '[':
							if isinstance(tokens[-1][-1], name):
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
		else:
			hemera.debug_tree(self) # Uncomment for parse tree debug information
			return self

class coroutine(node): # Base coroutine object

	def __init__(self, value): # Coroutines don't take nodes in __init__()

		super().__init__(value)
		self.supertype = None

	def __repr__(self):
		
		return str([str(item.type) + ' ' + str(item.value) for item in self.value])

class module(coroutine): # Module object is always the top level of a syntax tree

	def __init__(self, file_name):

		super().__init__(self) # Sets initial node to self
		with open(file_name, 'r') as f: # Binds file data to runtime object
			self.file_data = f.read() # node.parse() takes a string containing newlines
		self.value = [file_name.split('.')[0]]
		self.name, self.type = self.value[0], 'untyped'
		self.parse(self.file_data) # Here's tree

	def __repr__(self):

		return 'module ' + self.name

	def execute(self, routine):
		
		while routine.path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
			yield
		else: # Default behaviour for no return or yield
			if not routine.link:
				routine.end.send(None) # Sends value to return queue
			yield

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__([tokens[0]]) # Type
		self.name, self.type = tokens[0].value, tokens[0].value
		if len(tokens) > 2: # Naive check for subtyping
			self.supertype = tokens[2].value
			if self.supertype in kadmos.sub_types: # Corrects shortened type names
				self.supertype = kadmos.sub_types[self.supertype]
		else:
			self.supertype = 'untyped'
		self.namespace = [] # Persistent namespace of type operations

	def __call__(self, routine): # Initialises type routine
		
		type_routine = process(routine.namespace, self) # Create new routine
		type_routine.start() # Start process for routine
		type_routine.ready.wait() # Await routine initialisation
		type_routine.proxy.pid = type_routine.pid
		return routine.bind(self.name, type_routine.proxy, sophia_type)

	def execute(self, routine):
		
		routine.bind(self.name, routine.messages.recv(), self.supertype)
		routine.reserved = [self.name] # Reserve cast value
		while routine.path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
			yield
		else: # Default behaviour for no return or yield
			routine.end.send(routine.find(self.name)) # Sends cast value to return queue upon success
			routine.branch(0) # Reset path to initial
			routine.reserved = [] # Unreserve cast value

	def prepare(self, routine): # Initialises type
		
		routine.bind(self.name, self, sophia_type)
		for node in self.nodes:
			if isinstance(node, function_statement) and node.value[1].value == self.name: # Detect type operation
				self.namespace.append(node)

class operator_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets operator symbol and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type

	def __call__(self, routine, *args):

		x = routine.cast(args[0], self.value[1].type)
		if len(args) > 1:
			y = routine.cast(args[1], self.value[2].type)
			value = process(routine.namespace, self, x, y) # Create new routine
		else:
			value = process(routine.namespace, self, x) # Create new routine
		value.start() # Start process for routine
		return routine.cast(value.proxy.get(), self.type) # Get value immediately

	def execute(self, routine):
		
		routine.bind(self.name, self, sophia_operator)
		while routine.path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
			yield
		else: # Default behaviour for no return or yield
			routine.end.send(None) # Sends value to return queue
			yield

class function_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type

	def execute(self, routine):
		
		routine.bind(self.name, self, sophia_function)
		while routine.path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
			yield
		else: # Default behaviour for no return or yield
			routine.end.send(None) # Sends value to return queue
			yield

class statement(node):

	def __repr__(self):

		return type(self).__name__

class assignment(statement):

	def __init__(self, tokens):

		super().__init__(tokens[0], kadmos.lexer(tokens[2:]).parse())

	def __repr__(self):

		return 'assignment ' + repr(self.value)

	def execute(self, routine):
		
		value = yield # Yields to main
		if self.value.type:
			type_routine = routine.find(self.value.type)
		else:
			type_routine = None
		yield routine.bind(self.value.value, value, type_routine) # Yields to go up

class if_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())

	def execute(self, routine):

		condition = yield
		if not sophia_boolean(condition): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			return routine.error('Condition must evaluate to boolean')
		elif condition:
			while routine.path[-1] <= len(self.nodes):
				yield
		else:
			yield routine.branch()

class while_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())

	def execute(self, routine):

		condition = yield
		if not sophia_boolean(condition): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			return routine.error('Condition must evaluate to boolean')
		elif not condition:
			yield routine.branch()
		while condition:
			while routine.path[-1] < len(self.nodes): # Continue breaks this condition early
				yield
			routine.branch(0) # Repeat nodes
			condition = yield
			if not sophia_boolean(condition): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
				return routine.error('Condition must evaluate to boolean')
		else:
			yield routine.branch(len(self.nodes)) # Skip nodes

class for_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1], kadmos.lexer(tokens[3:-1]).parse())

	def execute(self, routine):

		index = self.value
		sequence = yield
		sequence = iter(sequence) # Enables fast slice
		try:
			while True: # Loop until the iterator is exhausted
				routine.bind(index.value, next(sequence), index.type) # Binds the next value of the sequence to the loop index
				while routine.path[-1] < len(self.nodes): # Continue breaks this condition early
					yield
				routine.branch(1) # Repeat nodes
		except StopIteration: # Break
			routine.unbind(index.value) # Unbinds the index
			yield routine.branch(len(self.nodes)) # Skip nodes

class else_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		if len(tokens) > 2: # Non-final else
			head = globals()[tokens[1].value + '_statement'](tokens[1:]) # Tokenise head statement
			self.value, self.nodes, self.execute = head.value, head.nodes, head.execute # Else statement pretends to be its head statement
			del head # So no head?

	def execute(self, routine): # Final else statement; gets overridden for non-final
		
		while routine.path[-1] <= len(self.nodes):
			yield

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
			self.length = len(nodes)

	def execute(self, routine):
		
		while routine.path[-1] < self.length: # Evaluates all head statement nodes
			value = yield
			if value is None: # Catches null expressions
				yield routine.branch()
		while routine.path[-1] <= len(self.nodes):
			yield
	
class constraint_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)

	def execute(self, routine):

		while routine.path[-1] <= len(self.nodes):
			constraint = yield
			if not sophia_boolean(constraint):
				return routine.error('Constraint must evaluate to boolean')
			if not constraint:
				return routine.error('Failed constraint')

class return_statement(statement):

	def __init__(self, tokens):
		
		if len(tokens) > 1:
			super().__init__(None, kadmos.lexer(tokens[1:]).parse())
		else:
			super().__init__(None)

	def execute(self, routine):
		
		if self.nodes:
			value = yield
		else:
			value = None
		yield routine.end.send(value) # Sends value to return queue

class link_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1::2]) # Allows multiple links

	def __repr__(self):

		return 'link_statement ' + str([repr(item) for item in self.nodes])

	def execute(self, routine):

		for item in self.value:
			name = item.value
			if '.' not in name:
				name = name + '.sophia'
			module_routine = process(routine.namespace, module(name), link = True)
			module_routine.start()
			module_routine.ready.wait() # Await routine initialisation
			module_routine.proxy.pid = module_routine.pid
			module_routine.proxy.bound = True
			routine.bind(item.value.split('.')[0], module_routine.proxy, sophia_process)
		yield

class identifier(node): # Generic identifier class

	def __init__(self, value):

		super().__init__(value)
		self.lbp = 0
		self.type = None

class literal(identifier): # Adds literal behaviours to a node

	def nud(self, lex):

		return self # Gives self as node

	def execute(self, routine): # Literal values are evaluated at parse time

		yield self.value # Send value to main

class name(identifier): # Adds name behaviours to a node

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self, routine): # Terminal nodes
	
		if isinstance(self.head, receive): # Yields node to receive operator
			value = self
		else: # If reference:
			value = routine.find(self.value)
		yield value # Send value to main

class keyword(identifier): # Adds keyword behaviours to a node

	def nud(self, lex):

		return self

	def execute(self, routine):

		yield routine.control(self.value) # Control object handling continue and break

class operator(node): # Generic operator node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = kadmos.bp(value) # Gets binding power of symbol

class prefix(operator): # Adds prefix behaviours to a node

	def nud(self, lex):

		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self, routine): # Unary operators

		op = routine.find(self.value) # Gets the operator definition
		x = yield
		yield op(routine, x)

class receive(prefix): # Defines the receive operator

	def execute(self, routine):

		node = yield
		value = routine.messages.recv()
		if node.type:
			type_routine = routine.find(node.type)
		else:
			type_routine = None
		routine.bind(node.value, value, type_routine)
		yield value

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self, routine):
		
		op = routine.find(self.value) # Gets the operator definition
		x = yield
		y = yield
		yield op(routine, x, y)

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self, routine):

		if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a slice object or a dictionary
			x = yield
			y = yield
			if self.nodes and self.nodes[1].value == ':':
				value = [x] + y
			else:
				value = [x, y]
			if self.head.value == ':':
				yield value
			else:
				if len(value) == 2:
					yield arche.element(value)
				else:
					yield arche.slice(value)
		elif self.value == ',': # Sorts out comma-separated parameters by returning them as a list
			x = yield
			y = yield
			if self.nodes and self.nodes[1].value == ',':
				value = [x] + y
			else:
				value = [x, y]
			yield value
		else: # Binary operators
			op = routine.find(self.value) # Gets the operator definition
			x = yield
			y = yield
			yield op(routine, x, y)

class bind(operator): # Defines the bind operator

	def __repr__(self):

		return 'bind ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the left operand like assignment
		
		self.value, self.nodes = left, [lex.parse(self.lbp)]
		return self

	def execute(self, routine):

		value = yield # Yields to main
		if not sophia_process(value):
			return routine.error('Invalid bind')
		value.bound = True
		routine.bind(self.value.value, value, sophia_process) # Binds routine
		yield value

class send(operator): # Defines the send operator

	def __repr__(self):

		return 'send ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the right operand like assignment
		
		self.nodes, self.value = [left], lex.parse(self.lbp)
		return self

	def execute(self, routine):

		value = yield # Sending only ever takes 1 argument
		value = routine.cast(value, self.routine().type) # Enforce output type for send value
		address = routine.find(self.value.value)
		if not sophia_process(address):
			return routine.error('Invalid send')
		if address.name == routine.name:
			return routine.error('Send source and destination are the same')
		address.send(value) # Sends value to destination queue
		yield address

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

		function = yield
		if len(self.nodes) > 1:
			args = yield
		else:
			args = []
		if not isinstance(args, list): # Type correction
			args = [args] # Very tiresome type correction, at that
		if isinstance(function, list): # If type operation:
			args = [function[0]] + args # Shuffle arguments
			function = function[1] # Get actual function
		if isinstance(function, function_statement): # If user-defined:
			routine = process(routine.namespace, function, *args) # Create new routine
			routine.start() # Start process for routine
			routine.ready.wait()
			value = routine.proxy # Yields proxy object as a promise
			value.pid = routine.pid # Updates PID
		elif hasattr(function, '__call__'): # If built-in:
			if args: # Python doesn't like unpacking empty tuples
				value = function(*args) # Since value is a Python function in this case
			else:
				value = function()
		else:
			return routine.error(function.__name__ + ' is not a function')
		if sophia_process(value) and not isinstance(self.head, (assignment, bind, send)):
			yield value.get() # Blocks until function returns
		else:
			yield value

class parenthesis(left_bracket):

	def execute(self, routine):

		x = yield
		yield x

class sequence_index(left_bracket):

	def execute(self, routine):
		
		value = yield
		subscript = yield
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
		yield value # Return the accessed value

class sequence_literal(left_bracket):

	def execute(self, routine):
		
		if self.nodes:
			items = yield
		else:
			items = []
		if not isinstance(items, (list, arche.slice)):
			items = [items]
		if isinstance(items[0], arche.element): # If items is a key-item pair in a record
			yield dict(iter(items)) # Better way to merge a list of key-value pairs into a record
		else: # If list or slice:
			yield tuple(items) # Tuple expands slice

class meta_statement(left_bracket):

	def execute(self, routine):
		
		if len(self.nodes) > 1:
			return routine.error('Meta-statement forms invalid expression')
		data = yield # Evaluate string
		self.parse(data) # Run-time parser stage
		value = yield # Yield into evaluated statement or expression
		self.nodes = [self.nodes[0]]
		yield value # Yield value, if it has one

class right_bracket(operator): # Adds right-bracket behaviours to a node

	def __init__(self, value):

		super().__init__(value)

# Type definitions

class sophia_untyped: # Abstract base class

	types = object
	
	def __new__(cls, value): # Type check disguised as an object constructor
		
		if cls.types:
			if isinstance(value, cls.types):
				return value
		else:
			for subclass in cls.__subclasses__():
				if subclass(value):
					return value

class sophia_routine(sophia_untyped): # Abstract routine type

	types = None # Null types makes __new__ check the types of a type's subclasses

class sophia_process(sophia_routine): # Process/module type
	
	types = arche.proxy

class sophia_type(sophia_routine): # Type type
	
	types = type, type_statement

class sophia_operator(sophia_routine): # Operator type

	types = arche.operator, operator_statement

class sophia_function(sophia_routine): # Function type

	types = sophia_untyped.__init__.__class__, function_statement # Hatred

class sophia_value(sophia_untyped): # Abstract element type

	types = None

class sophia_boolean(sophia_value): # Boolean type

	types = bool

	def __repr__(self):

		return str(self).lower()

	def __str__(self):

		return str(self).lower()

class sophia_number(sophia_value): pass # Abstract number type

class sophia_integer(sophia_number): # Integer type

	types = int

class sophia_float(sophia_number): # Float type

	types = float

class sophia_real(sophia_number): # Real type

	types = real

class sophia_sequence(sophia_untyped): # Abstract sequence type

	types = None

	def length(self):

		return len(self)

class sophia_string(sophia_sequence): # String type

	types = str

class sophia_list(sophia_sequence): # List type

	types = tuple

class sophia_record(sophia_sequence): # Record type

	types = dict

if __name__ == '__main__': # Hatred

	with mp.Manager() as runtime: # The stupidest global state you've ever seen in your life
		
		mp.current_process().name = 'runtime'
		types = [(k.split('_')[1], v, sophia_type) for k, v in globals().items() if k.split('_')[0] == 'sophia']
		operators = [(v[0], arche.operator(*v), sophia_operator) for k, v in arche.__dict__.items() if k.split('_')[0] == 'op']
		functions = [(k.split('_')[1], v, sophia_function) for k, v in arche.__dict__.items() if k.split('_')[0] == 'f']
		built_ins = types + operators + functions
		namespace = runtime.dict({0: runtime.Lock()}) # Unfortunate namespace hierarchy, but at least processes never write to the same memory
		namespace[1] = kleio.namespace((i[0] for i in built_ins), (i[1] for i in built_ins), (i[2] for i in built_ins)) # Built-ins
		main = process(namespace, module('test.sophia')) # Spawn initial process
		main.start() # Start initial process
		main.join() # Prevent exit until initial process ends