# ☉
# 08/05/2022: Parser implemented (first working version)
# 15/07/2022: Hello world program
# 04/08/2022: Fibonacci program
# 09/08/2022: Basic feature set implemented (0.0)
# 16/08/2022: Basic feature set re-implemented (0.1)
# 20/08/2022: Type system implemented (0.1)

import arche, hemera, kadmos, kleio
import multiprocessing as mp
from multiprocessing import current_process as get_process
from fractions import Fraction as real

class process(mp.Process): # Created by function calls and type checking

	def __init__(self, namespace, routine, *args, link = False): # God objects? What is she objecting to?
		
		super().__init__(name = get_process().name + '.' + routine.name, target = self.execute, args = args)
		self.type = routine.type
		self.supertype = getattr(routine, 'supertype', None) # Supertype of type routine
		self.instances = []
		self.path = [0]
		self.node = routine # Current node; sets initial module as entry point
		self.value = None # Current value
		self.namespace = namespace # Reference to shared namespace hierarchy
		self.reserved = [] # List of reserved names in the current namespace
		self.proxy = sophia_process(self, link = link)
		self.messages, self.proxy.messages = mp.Pipe() # Pipe to receive messages
		self.end, self.proxy.end = mp.Pipe() # Pipe to send return value

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
					self.node(self)
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
			if self.proxy.link:
				self.proxy.end.poll(None) # Hangs for linked modules
			for routine in mp.active_children(): # Makes sure all child processes are finished before terminating
				if routine.supertype: # Type routine
					routine.terminate() # Type routines end just before being removed from the namespace
				else:
					if routine.proxy.link:
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

	def bind(self, name, value, type_value = None): # Creates or updates a name binding in main
		
		if self.namespace[1].read(name) or name in self.reserved: # Quicker and easier to do it here
			return self.error('Bind to reserved name: ' + name)
		namespace = self.namespace[self.pid] # Retrieve routine namespace
		if type_value:
			value = self.cast(value, type_value)
		else:
			type_value = self.namespace[self.pid].read_type(name)
			if type_value:
				value = self.cast(value, type_value)
		namespace.write(name, value) # Mutate namespace
		namespace.write_type(name, type_value)
		self.namespace[0].acquire() # Acquires namespace lock
		self.namespace[self.pid] = namespace # Update shared dict; nested objects don't sync unless you make them
		self.namespace[0].release() # Releases namespace lock

	def unbind(self, name): # Destroys a name binding in the current namespace
		
		namespace = self.namespace[self.pid] # Retrieve routine namespace
		namespace.delete(name) # Delete binding from namespace
		self.namespace[0].acquire() # Acquires namespace lock
		self.namespace[self.pid] = namespace # Update shared dict; nested objects don't sync unless you make them
		self.namespace[0].release() # Releases namespace lock

	def find(self, name, get_type = False): # Retrieves a binding's value in the routine's available namespace
		
		value = self.namespace[1].read(name) # Searches built-ins first; built-ins are independent of namespaces
		if value:
			return value
		pid = self.pid
		while pid in self.namespace:
			if get_type:
				value = self.namespace[pid].read_type(name)
			else:
				value = self.namespace[pid].read(name)
			if value:
				if isinstance(value, sophia_process) and self.namespace[pid].read_type(name) != 'type' and (not value.bound or value.end.poll()): # If the name is associated with an unbound or finished routine:
					value = self.cast(value.get(), value.type) # Block for return value and check type
					self.namespace[pid].write(name, value) # Is it breaking encapsulation if the target routine is finished when this happens?
				return value
			else:
				pid = self.namespace[pid].parent
		return self.error('Undefined name: ' + repr(name))

	def cast(self, operand, type_name): # Checks type of value and returns boolean
		
		value = operand
		if not type_name: # For literals of unspecified type
			return value
		type_routine = self.find(type_name)
		stack = [] # Stack of user-defined types, with the requested type at the bottom
		while isinstance(type_routine, sophia_process):
			stack.append(type_routine)
			type_routine = self.find(type_routine.supertype) # Type routine is guaranteed to be a built-in when loop ends, so it checks that before any of the types on the stack
		if not type_routine.cast(value): # Check built-in type
			return self.error('Failed cast to ' + type_name + ': ' + repr(operand))
		while stack:
			type_routine = stack.pop()
			type_routine.send(value)
			value = type_routine.get()
			if value is None:
				return self.error('Failed cast to ' + type_name + ': ' + repr(operand))
		else:
			return value # Return indicates success; cast() raises an exception on failure

	def error(self, status): # Error handler
		
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
				if (symbol[0] in kadmos.characters or symbol[0] in ("'", '"')) and (symbol not in kadmos.keyword_operators): # Quick test for literal
					if symbol in kadmos.structure_tokens or symbol in kadmos.keyword_tokens:
						token = keyword(symbol)
					else:
						token = literal(symbol)
						if tokens[-1] and isinstance(tokens[-1][-1], literal): # Checks for type
							token_type = tokens[-1].pop().value # Gets type of identifier 
							if token_type in kadmos.sub_types: # Corrects shortened type names
								token_type = kadmos.sub_types[token_type]
							token.type = token_type # Sets type of identifier
				else:
					if symbol in kadmos.parens[0::2]:
						if symbol == '(':
							if isinstance(tokens[-1][-1], literal):
								token = function_call(symbol)
							else:
								token = parenthesis(symbol)
						elif symbol == '[':
							if isinstance(tokens[-1][-1], literal):
								token = sequence_index(symbol)
							else:
								token = sequence_literal(symbol)
						elif symbol == '{':
							token = meta_statement(symbol)
					elif symbol in kadmos.parens[1::2]:
						token = right_bracket(symbol)
					elif tokens[-1] and isinstance(tokens[-1][-1], (literal, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
						if symbol in ('^', ',', ':'):
							token = infix_r(symbol)
						elif symbol == '<-':
							token = bind(symbol)
						elif symbol == '->':
							token = send(symbol)
						else:
							if tokens[-1] and isinstance(tokens[-1][-1], literal) and line[-1] == ':': # Special case for operator definition
								token = literal(symbol)
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
			if not routine.proxy.link:
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

	def __call__(self, routine): # Initialises type routine
		
		type_routine = process(routine.namespace, self) # Create new routine
		type_routine.start() # Start process for routine
		return routine.bind(self.name, type_routine.proxy, 'type')

	def execute(self, routine):
		
		while True: # Execution loop
			routine.bind(self.name, routine.messages.recv(), self.supertype)
			routine.reserved = [self.name] # Reserve cast value
			while routine.path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
				yield
			else: # Default behaviour for no return or yield
				routine.end.send(routine.find(self.name)) # Sends cast value to return queue upon success
				routine.branch(0) # Reset path to initial
				routine.reserved = [] # Unreserve cast value

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
		
		routine.bind(self.name, self, 'operator')
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
		
		routine.bind(self.name, self, 'function')
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
		yield routine.bind(self.value.value, value, self.value.type) # Yields to go up

class if_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())

	def execute(self, routine):

		condition = yield
		if not isinstance(condition, sophia_boolean): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
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
		if not isinstance(condition, sophia_boolean): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			return routine.error('Condition must evaluate to boolean')
		elif not condition:
			yield routine.branch()
		while condition:
			while routine.path[-1] < len(self.nodes): # Continue breaks this condition early
				yield
			routine.branch(0) # Repeat nodes
			condition = yield
			if not isinstance(condition, sophia_boolean): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
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
			if not isinstance(constraint, sophia_boolean):
				return routine.error('Constraint must evaluate to boolean')
			if not constraint:
				routine.end.send(None) # Null return
				routine.node = None

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
			routine.bind(item.value.split('.')[0], module_routine.proxy, 'module')
			module_routine.start()
		yield

class identifier(node): # Generic identifier class

	def __init__(self, value): # Constants can be resolved at parse time

		if value[0] in '.0123456789': # Terrible way to check for a number without using a try/except block
			if '.' in value:
				value = sophia_real(str(value)) # Cast to real by default
			else:
				value = sophia_integer(value) # Cast to int
		elif value[0] in ('"', "'"):
			value = sophia_string(value[1:-1]) # Interpret as string
		elif value in kadmos.sub_values:
			value = kadmos.sub_values[value] # Interpret booleans and null
			if value is not None:
				value = sophia_boolean(value)
		super().__init__(value)
		self.lbp = 0
		self.type = None

class literal(identifier): # Adds literal behaviours to a node

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self, routine): # Terminal nodes
	
		if isinstance(self.value, sophia_untyped) or self.value is None:
			value = self.value
		elif isinstance(self.head, receive): # Yields node to receive operator
			value = self
		else: # If reference:
			try:
				value = routine.find(self.value)
				value = routine.cast(value, self.type) # Type casting
			except (NameError, TypeError) as status:
				if isinstance(self.head, assert_statement) and routine.path[-1] < self.head.length: # Allows assert statements to reference unbound names without error
					value = None
				else:
					return routine.error(status.args[0])
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
		routine.bind(node.value, value, node.type)
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
					yield {value[0]: value[1]}
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
		if not isinstance(value, sophia_process):
			return routine.error('Invalid bind')
		value.bound = True
		routine.bind(self.value.value, value) # Yields to go up
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
		if not isinstance(address, sophia_process):
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
		if isinstance(function, function_statement): # If user-defined:
			routine = process(routine.namespace, function, *args) # Create new routine
			routine.start() # Start process for routine
			value = routine.proxy # Yields proxy object as a promise
		elif hasattr(function, '__call__'): # If built-in:
			if args: # Python doesn't like unpacking empty tuples
				value = function(*args) # Since value is a Python function in this case
			else:
				value = function()
		else:
			return routine.error(function.__name__ + ' is not a function')
		if isinstance(value, sophia_process) and not isinstance(self.head, (assignment, bind, send)):
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
				if isinstance(value, sophia_sequence):
					if i.nodes[1] < -1 * len(value) or i.nodes[1] > len(value): # If out of bounds:
						return routine.error('Index out of bounds')
				else:
					return routine.error('Value not sliceable')
			elif isinstance(value, sophia_record):
				if i not in value:
					return routine.error('Key not in record: ' + i)
			else:
				if i < -1 * len(value) or i >= len(value): # If out of bounds:
					return routine.error('Index out of bounds')
			if isinstance(i, arche.slice):
				if isinstance(value, sophia_string):
					value = sophia_string(''.join([value[n] for n in i.value])) # Constructs slice of string using range
				elif isinstance(value, sophia_list):
					value = sophia_list([value[n] for n in i.value]) # Constructs slice of list using range
				elif isinstance(value, sophia_record):
					value = sophia_record({list(value.keys())[n]: list(value.values())[n] for n in i.value}) # Constructs slice of record using range
			else:
				value = value[i] # Python can handle this bit
		yield value # Return the accessed value

class sequence_literal(left_bracket):

	def execute(self):
		
		if self.nodes:
			items = yield
		else:
			items = []
		if not isinstance(items, (list, arche.slice)):
			items = [items]
		if isinstance(items[0], dict) and not isinstance(items[0], sophia_record): # If items is a key-item pair in a record
			yield sophia_record({list(item.keys())[0]: list(item.values())[0] for item in items}) # Stupid way to merge a list of dicts
		if isinstance(items, list): # If list:
			yield sophia_list(items)
		if isinstance(items, arche.slice): # If slice:
			yield sophia_list(items.execute()) # Gives slice expansion

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

# Value definitions

class sophia_untyped: # Abstract base class

	@classmethod
	def cast(cls, value):
		
		if isinstance(value, cls):
			return True

class sophia_process(arche.proxy, sophia_untyped): pass # Proxy object pretending to be a process

class sophia_routine(sophia_untyped): pass # Abstract routine type

class sophia_module(arche.proxy, sophia_routine): # Module type

	@classmethod
	def cast(cls, value):

		if isinstance(value, arche.proxy):
			return True

class sophia_type(arche.proxy, sophia_routine): # Type type

	@classmethod
	def cast(cls, value):

		if isinstance(value, (arche.proxy, type)):
			return True

class sophia_operator(arche.operator, sophia_routine): # Operator type

	def __call__(self, routine, *args):

		x = routine.cast(args[0], self.types[1])
		if len(args) > 1:
			y = routine.cast(args[1], self.types[2])
			value = self.binary(x, y)
		else:
			value = self.unary(x)
		if value is not None and not isinstance(value, sophia_untyped): # Normalise value to Sophia type
			type_name = type(value).__name__
			if type_name in kadmos.sub_types:
				type_name = kadmos.sub_types[type_name]
			type_routine = routine.find(type_name)
			value = type_routine(value) # Attempt conversion to Sophia type
		return routine.cast(value, self.types[0])

	@classmethod
	def cast(cls, value):

		if isinstance(value, (cls, operator_statement)):
			return True

class sophia_function(sophia_routine): # Function type

	@classmethod
	def cast(cls, value):

		if isinstance(value, (cls.__init__.__class__, function_statement)): # Hatred
			return True

class sophia_value(sophia_untyped): pass # Abstract element type

class sophia_boolean(int, sophia_value): # Boolean type

	def __bool__(self): # Hell

		if self == 1:
			return True
		else:
			return False

	def __repr__(self):

		return str(bool(self)).lower()

	def __str__(self):

		return str(bool(self)).lower()

class sophia_number(sophia_value): pass # Abstract number type

class sophia_integer(int, sophia_number): pass # Integer type

class sophia_float(float, sophia_number): pass # Float type

class sophia_real(real, sophia_number): pass # Real type

class sophia_sequence(sophia_untyped): pass # Abstract sequence type

class sophia_string(str, sophia_sequence): pass # String type

class sophia_list(tuple, sophia_sequence): pass # List type

class sophia_record(dict, sophia_sequence): pass # Record type

if __name__ == '__main__': # Hatred

	with mp.Manager() as runtime: # The stupidest global state you've ever seen in your life
		
		get_process().name = 'runtime'
		types = [(k.split('_')[1], v, 'type') for k, v in globals().items() if k.split('_')[0] == 'sophia']
		operators = [(v[0], sophia_operator(*v), 'operator') for k, v in arche.__dict__.items() if k.split('_')[0] == 'op']
		functions = [(k.split('_')[1], v, 'function') for k, v in arche.__dict__.items() if k.split('_')[0] == 'f']
		built_ins = types + operators + functions
		namespace = runtime.dict({0: runtime.Lock()}) # Unfortunate namespace hierarchy, but at least processes never write to the same memory
		namespace[1] = kleio.namespace((i[0] for i in built_ins), (i[1] for i in built_ins), (i[2] for i in built_ins)) # Built-ins
		main = process(namespace, module('test.sophia')) # Spawn initial process
		main.start() # Start initial process
		main.join() # Prevent exit until initial process ends