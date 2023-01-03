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

	def __init__(self, namespace, routine, *args): # God objects? What is she objecting to?
		
		super().__init__(name = get_process().name + '.' + routine.name, target = self.execute, args = args)
		self.type = routine.type
		self.instances = []
		self.path = [0]
		self.node = routine # Current node; sets initial module as entry point
		self.value = None # Current value
		self.namespace = namespace # Reference to shared namespace hierarchy
		self.reserved = [] # List of reserved names in the current namespace
		self.proxy = sophia_process(self)
		self.messages, self.proxy.messages = mp.Pipe() # Pipe to receive messages
		self.end, self.proxy.end = mp.Pipe() # Pipe to send return value

	def __repr__(self):

		return ' '.join((str(getattr(self.node, 'n', 0)).zfill(4), self.name, str(self.path[-1]), repr(self.node)))

	def execute(self, *args): # Target of run()
		
		params = self.node.value[1:] # Gets coroutine name, return type, and parameters
		if len(params) != len(args):
			return self.error('Expected {0} arguments, received {1}'.format(len(params), len(args)))
		args = [self.cast(arg, params[i].type) for i, arg in enumerate(args)] # Check type of args against params
		params = [item.value for item in params] # Get names of params
		self.reserved = params
		self.namespace[self.pid] = kleio.namespace(params, args) # Updates namespace hierarchy
		self.instances.append(self.node.execute()) # Start routine
		while self.node: # Runtime loop
			hemera.debug_process(self)
			if self.node.nodes and 0 <= self.path[-1] < len(self.node.nodes): # Walk down
				self.node.nodes[self.path[-1]].head = self.node # Sets child head to self
				self.node = self.node.nodes[self.path[-1]] # Set value to child node
				self.path.append(0)
				if isinstance(self.node, coroutine):
					self.branch() # Skips body of routine
				self.instances.append(self.node.execute()) # Initialises generator
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
			for routine in mp.active_children(): # Makes sure all child processes are finished before terminating
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

	def bind(self, name, value): # Creates or updates a name binding in main
		
		if self.namespace[1].read(name) or name in self.reserved: # Quicker and easier to do it here
			return self.error('Bind to reserved name: ' + name)
		namespace = self.namespace[self.pid] # Retrieve routine namespace
		namespace.write(name, value) # Mutate namespace
		self.namespace[0].acquire() # Acquires namespace lock
		self.namespace[self.pid] = namespace # Update shared dict; nested objects don't sync unless you make them
		self.namespace[0].release() # Releases namespace lock

	def unbind(self, name): # Destroys a name binding in the current namespace
		
		namespace = self.namespace[self.pid] # Retrieve routine namespace
		namespace.delete(name) # Delete binding from namespace
		self.namespace[0].acquire() # Acquires namespace lock
		self.namespace[self.pid] = namespace # Update shared dict; nested objects don't sync unless you make them
		self.namespace[0].release() # Releases namespace lock

	def find(self, name): # Retrieves a binding in the routine's available namespace
		
		value = self.namespace[1].read(name) # Searches built-ins first; built-ins are independent of namespaces
		if value:
			return value
		pid = self.pid
		while pid in self.namespace:
			self.namespace[0].acquire()
			value = self.namespace[pid].read(name)
			self.namespace[0].release()
			if value:
				if isinstance(value, sophia_process) and (not value.bound or value.end.poll()): # If the name is associated with an unbound or finished routine:
					value = self.cast(value.get(), value.type) # Block for return value and check type
					self.namespace[pid].write(name, value) # Is it breaking encapsulation if the target routine is finished when this happens?
				return value
			else:
				pid = self.namespace[pid].parent
		return self.error('Undefined name: ' + name)

	def cast(self, operand, type_name): # Checks type of value and returns boolean
		
		value = operand
		if not type_name: # For literals of unspecified type
			return value
		type_routine = self.find(type_name)
		while type_routine:
			value = type_routine(value) # Invokes type check
			if value is None:
				return self.error('Failed cast to ' + type_name + ': ' + repr(operand))
			type_routine = type_routine.supertype() # Returns null for built-ins
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
						if symbol == 'type' and n != 0 and line[-1] != ':': # Special keyword
							token = literal(symbol)
						else:
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
				if line[0].value[0] in kadmos.characters: # Functions have names and operators have symbols
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

		return type(self).__name__ + ' ' + str([item.type + ' ' + item.value for item in self.value])

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

	def execute(self):
		
		while get_process().path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
			yield
		else: # Default behaviour for no return or yield
			get_process().end.send(None) # Sends value to return queue
			yield

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__([tokens[1]]) # Type
		self.name, self.type = tokens[1].value, tokens[1].value
		if len(tokens) > 3: # Naive check for subtyping
			self.supertype = tokens[3].value
			if self.supertype in kadmos.sub_types: # Corrects shortened type names
				self.supertype = kadmos.sub_types[self.supertype]
		else:
			self.supertype = 'untyped'

	def execute(self):

		routine = process(get_process().namespace, self) # Create new routine
		routine.start() # Start process for routine
		if isinstance(self.head, (assignment, bind, send)):
			yield routine.proxy # Yields proxy object as a promise
		else:
			yield routine.proxy.get() # Blocks until function returns
		get_process().bind(self.value[0].value, sophia_type(self))
		while True: # Execution loop
			while get_process().path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
				yield
			else: # Default behaviour for no return or yield
				get_process().end.send(None) # Sends value to return queue
				routine().branch(0) # Reset path to initial
				yield

class operator_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets operator symbol and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type

	def execute(self):
		
		get_process().bind(self.value[0].value, sophia_operator(self))
		while True: # Execution loop
			while get_process().path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
				yield
			else: # Default behaviour for no return or yield
				get_process().end.send(None) # Sends value to return queue
				yield

class function_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type

	def execute(self):
		
		get_process().bind(self.name, sophia_function(self))
		while True: # Execution loop
			while get_process().path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
				yield
			else: # Default behaviour for no return or yield
				get_process().end.send(None) # Sends value to return queue
				yield

class statement(node):

	def __repr__(self):

		return type(self).__name__

class assignment(statement):

	def __init__(self, tokens):

		super().__init__(tokens[0], kadmos.lexer(tokens[2:]).parse())

	def __repr__(self):

		return 'assignment ' + repr(self.value)

	def execute(self):
		
		value = yield # Yields to main
		value = get_process().cast(value, self.value.type) # Type cast
		yield get_process().bind(self.value.value, value) # Yields to go up

class if_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())

	def execute(self):

		condition = yield
		if not isinstance(condition, sophia_boolean): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			return get_process().error('Condition must evaluate to boolean')
		elif condition:
			while get_process().path[-1] <= len(self.nodes):
				yield
		else:
			yield get_process().branch()

class while_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())

	def execute(self):

		condition = yield
		if not isinstance(condition, sophia_boolean): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			return get_process().error('Condition must evaluate to boolean')
		elif not condition:
			yield get_process().branch()
		while condition:
			while get_process().path[-1] < len(self.nodes): # Continue breaks this condition early
				yield
			get_process().branch(0) # Repeat nodes
			condition = yield
			if not isinstance(condition, sophia_boolean): # Over-specify on purpose to implement Sophia's specific requirement for a boolean
				return get_process().error('Condition must evaluate to boolean')
		else:
			yield get_process().branch(len(self.nodes)) # Skip nodes

class for_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1], kadmos.lexer(tokens[3:-1]).parse())

	def execute(self):

		index = self.value
		sequence = yield
		sequence = iter(sequence) # Enables fast slice
		try:
			while True: # Loop until the iterator is exhausted
				get_process().bind(index.value, next(sequence), index.type) # Binds the next value of the sequence to the loop index
				while get_process().path[-1] < len(self.nodes): # Continue breaks this condition early
					yield
				get_process().branch(1) # Repeat nodes
		except StopIteration: # Break
			get_process().unbind(index.value) # Unbinds the index
			yield get_process().branch(len(self.nodes)) # Skip nodes

class else_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		if len(tokens) > 2: # Non-final else
			head = globals()[tokens[1].value + '_statement'](tokens[1:]) # Tokenise head statement
			self.value, self.nodes, self.execute = head.value, head.nodes, head.execute # Else statement pretends to be its head statement
			del head # So no head?

	def execute(self): # Final else statement; gets overridden for non-final
		
		while get_process().path[-1] <= len(self.nodes):
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

	def execute(self):
		
		while get_process().path[-1] < self.length: # Evaluates all head statement nodes
			value = yield
			if value is None: # Catches null expressions
				yield get_process().branch()
		while get_process().path[-1] <= len(self.nodes):
			yield
	
class constraint_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)

	def execute(self):

		while main.routines[-1].path[-1] < len(self.nodes):
			constraint = yield
			if not isinstance(constraint, sophia_boolean):
				return get_process().error('Constraint must evaluate to boolean')
			if not constraint:
				yield main.terminate(None)
		yield

class return_statement(statement):

	def __init__(self, tokens):
		
		if len(tokens) > 1:
			super().__init__(None, kadmos.lexer(tokens[1:]).parse())
		else:
			super().__init__(None)

	def execute(self):
		
		if self.nodes:
			value = yield
		else:
			value = None
		yield get_process().end.send(value) # Sends value to return queue

class link_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, *tokens[1::2]) # Allows multiple links

	def __repr__(self):

		return 'link_statement ' + str([repr(item) for item in self.nodes])

	def execute(self):

		pass # I don't know how to implement this yet

class identifier(node): # Generic identifier class

	def __init__(self, value): # Constants can be resolved at parse time

		if value[0] in '.0123456789': # Terrible way to check for a number without using a try/except block
			if '.' in value:
				value = sophia_real(real(str(value))) # Cast to real by default
			else:
				value = sophia_integer(int(value)) # Cast to int
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

	def execute(self): # Terminal nodes
	
		if isinstance(self.value, sophia_untyped):
			value = self.value
		elif isinstance(self.head, receive): # Yields node to receive operator
			value = self
		else: # If reference:
			try:
				value = get_process().find(self.value)
				value = get_process().cast(value, self.type) # Type casting
			except (NameError, TypeError) as status:
				if isinstance(self.head, assert_statement) and get_process().path[-1] < self.head.length: # Allows assert statements to reference unbound names without error
					value = None
				else:
					return get_process().error(status.args[0])
		yield value # Send value to main

class keyword(identifier): # Adds keyword behaviours to a node

	def nud(self, lex):

		return self

	def execute(self):

		yield get_process().control(self.value) # Control object handling continue and break

class operator(node): # Generic operator node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = kadmos.bp(value) # Gets binding power of symbol

class prefix(operator): # Adds prefix behaviours to a node

	def nud(self, lex):

		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self): # Unary operators

		op = get_process().find(self.value) # Gets the operator definition
		x = yield
		yield op(x) # Implements unary operator

class receive(prefix): # Defines the receive operator

	def execute(self):

		node = yield
		value = get_process().messages.recv()
		value = get_process().cast(value, node.type)
		get_process().bind(node.value, value)
		yield value

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self):
		
		op = get_process().find(self.value) # Gets the operator definition
		x = yield
		y = yield
		yield op(x, y) # Implements left-binding binary operator

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self):

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
			op = get_process().find(self.value) # Gets the operator definition
			x = yield
			y = yield
			yield op(x, y) # Implements right-binding binary operator

class bind(operator): # Defines the bind operator

	def __repr__(self):

		return 'bind ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the left operand like assignment
		
		self.value, self.nodes = left, [lex.parse(self.lbp)]
		return self

	def execute(self):

		value = yield # Yields to main
		if not isinstance(value, sophia_process):
			return get_process().error('Invalid bind')
		value.bound = True
		get_process().bind(self.value.value, value) # Yields to go up
		yield value

class send(operator): # Defines the send operator

	def __repr__(self):

		return 'send ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the right operand like assignment
		
		self.nodes, self.value = [left], lex.parse(self.lbp)
		return self

	def execute(self):

		value = yield # Sending only ever takes 1 argument
		value = get_process().cast(value, self.routine().type) # Enforce output type for send value
		address = get_process().find(self.value.value)
		if not isinstance(address, sophia_process):
			return get_process().error('Invalid send')
		if address.name == get_process().name:
			return get_process().error('Send source and destination are the same')
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

	def execute(self):

		function = yield
		if len(self.nodes) > 1:
			args = yield
		else:
			args = []
		if not isinstance(args, list): # Type correction
			args = [args] # Very tiresome type correction, at that
		if isinstance(function, sophia_function):
			value = function(*args) # Behaves like a Python function
			if isinstance(value, sophia_process) and not isinstance(self.head, (assignment, bind, send)):
				yield value.get() # Blocks until function returns
			else:
				yield value
		else:
			return get_process().error(function.__name__ + ' is not a function')

class parenthesis(left_bracket):

	def execute(self):

		x = yield
		yield x

class sequence_index(left_bracket):

	def execute(self):
		
		value = yield
		subscript = yield
		if not isinstance(subscript, list):
			subscript = [subscript]
		for i in subscript: # Iteratively accesses the sequence
			if isinstance(i, arche.slice):
				if isinstance(value, sophia_sequence):
					if i.nodes[1] < -1 * len(value) or i.nodes[1] > len(value): # If out of bounds:
						return get_process().error('Index out of bounds')
				else:
					return get_process().error('Value not sliceable')
			elif isinstance(value, sophia_record):
				if i not in value:
					return get_process().error('Key not in record: ' + i)
			else:
				if i < -1 * len(value) or i >= len(value): # If out of bounds:
					return get_process().error('Index out of bounds')
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
		if isinstance(items[0], dict): # If items is a key-item pair in a record
			yield sophia_record({list(item.keys())[0]: list(item.values())[0] for item in items}) # Stupid way to merge a list of dicts
		if isinstance(items, list): # If list:
			yield sophia_list(items)
		if isinstance(items, arche.slice): # If slice:
			yield sophia_list(items.execute()) # Gives slice expansion

class meta_statement(left_bracket):

	def execute(self):
		
		if len(self.nodes) > 1:
			return get_process().error('Meta-statement forms invalid expression')
		data = yield # Evaluate string
		self.parse(data) # Run-time parser stage
		value = yield # Yield into evaluated statement or expression
		self.nodes = [self.nodes[0]]
		yield value # Yield value, if it has one

class right_bracket(operator): # Adds right-bracket behaviours to a node

	def __init__(self, value):

		super().__init__(value)

# Type definitions

class sophia_untyped: # Non-abstract base class

	types = object # Type or tuple of types that the class instance's value can be

	def __new__(cls, value): # Using __new__ for casting; this allows a separate __init__ and returns null for failed casts

		if isinstance(value, sophia_untyped) and cls is not sophia_process: # Normalises Sophia values
			value = value.value
		if isinstance(value, cls.types):
			return object.__new__(cls)

	def __init__(self, value): # Default __init__()

		if isinstance(value, sophia_untyped): # Normalises Sophia values
			value = value.value
		self.value = value

	@classmethod
	def __cast__(cls, value): # Default __cast__(); untyped doesn't convert values by definition

		value = cls(value)
		if value:
			return value
		else:
			return get_process.error('Invalid type conversion')

	def __getnewargs__(self): # Handles unpickling; return value is passed to __new__()

		return (self.value,)

	def __repr__(self):

		return repr(self.value)

class sophia_routine(sophia_untyped): # Abstract routine type

	types = coroutine # Currently user-defined only

	def __new__(cls, value): # Using __new__ for casting; this allows a separate __init__ and returns null for failed casts

		if isinstance(value, sophia_untyped) and cls is not sophia_process: # Normalises Sophia values
			value = value.value
		if isinstance(value, cls.types):
			return object.__new__(cls)

class sophia_process(sophia_untyped): # Proxy object pretending to be a process

	def __new__(cls, value): # Special __new__ for internal type
		
		if isinstance(value, (cls, process, dict)): # Because of __getnewargs__()
			return object.__new__(cls)

	def __init__(self, value):
		
		if isinstance(value, dict):
			self.__dict__.update(value)
		else:
			self.name = value.name
			self.type = value.type
			self.pid = value.pid
			self.messages = None # Pipe to send messages
			self.end = None # Pipe for return value
			self.bound = False # Determines whether process is bound

	def __getnewargs__(self): # Handles unpickling; return value is passed to __new__()

		return (self.__dict__.copy(),)

	def __repr__(self):

		return 'process ' + self.name

	def send(self, value): # Proxy method to send to process

		return self.messages.send(value)

	def get(self): # Proxy method to get return value from process

		return self.end.recv()

class sophia_type(sophia_routine): # Type type

	types = (type_statement, type)

	def __call__(self, value): # Enables function calls on value

		if isinstance(self.value, type_statement):
			pass
		else:
			return self.value(value) # Return instance of type

	def cast(self, value): # Explicit cast to type with modification of value

		try:
			return self.value.__cast__(value) # Defers to type
		except AttributeError:
			return get_process().error('Unsupported type conversion: ' + self.value.__name__)

	def supertype(self): # Gets supertype

		if isinstance(self.value, type_statement):
			return get_process().find(self.value.supertype)

class sophia_operator(sophia_routine): # Operator type

	types = (operator_statement, arche.operator)

	def __call__(self, *args): # Enables function calls on value
		
		if isinstance(self.value, operator_statement): # User-defined operator
			x = get_process().cast(args[0], self.value.value[1].type)
			if len(args) == 2:
				y = get_process().cast(args[1], self.value.value[2].type)
			routine = process(get_process().namespace, self.value, *args) # Create new routine
			routine.start() # Start process for routine
			value = routine.proxy.get() # Get value immediately
			return get_process().cast(value, self.value.value[0].type)
		else: # Built-in operator
			x = get_process().cast(args[0], self.value.types[1])
			if len(args) == 2:
				y = get_process().cast(args[1], self.value.types[2])
			if len(args) == 2:
				value = self.value.binary(x.value, y.value)
			else:
				value = self.value.unary(x.value)
			return get_process().cast(value, self.value.types[0])

class sophia_function(sophia_routine): # Function type

	types = (function_statement, sophia_untyped.__init__.__class__) # Hatred

	def __call__(self, *args): # Enables function calls on value

		if isinstance(self.value, function_statement): # If user-defined:
			routine = process(get_process().namespace, self.value, *args) # Create new routine
			routine.start() # Start process for routine
			return routine.proxy # Yields proxy object as a promise
		else: # If built-in:
			if args: # Python doesn't like unpacking empty tuples
				return self.value(*args) # Since value is a Python function in this case
			else:
				return self.value()

class sophia_value(sophia_untyped): # Abstract singular value type

	types = (bool, int, float, real)

class sophia_boolean(sophia_value): # Boolean type

	types = bool

	@classmethod
	def __cast__(cls, value):

		return cls(bool(value.value))

	def __repr__(self):

		return str(self.value).lower()

	def __str__(self):

		return str(self.value).lower()

class sophia_number(sophia_value): # Abstract number type

	types = (int, float, real)

	def __new__(cls, value): # Number types have specific conversion requirements
		
		if isinstance(value, sophia_untyped):
			value = value.value
		if isinstance(value, cls.types) and type(value)(value) == value:
			return object.__new__(cls)

	def __init__(self, value):

		if isinstance(value, sophia_untyped):
			value = value.value
		if isinstance(value, __class__.types) and type(value)(value) == value:
			value = type(value)(value)
		self.value = value

class sophia_integer(sophia_number): # Integer type
	
	types = int

	@classmethod
	def __cast__(cls, value):

		return cls(int(value.value))

class sophia_float(sophia_number): # Float type

	types = float

	@classmethod
	def __cast__(cls, value):

		return cls(float(value.value))

class sophia_real(sophia_number): # Real type

	types = real

	@classmethod
	def __cast__(cls, value):

		return cls(real(str(value.value)))

class sophia_sequence(sophia_untyped): # Abstract sequence type

	types = (str, tuple, dict)

	def length(self):

		return len(self)

class sophia_string(sophia_sequence): # String type

	types = str

	@classmethod
	def __cast__(cls, value):

		return cls(str(value.value))

class sophia_list(sophia_sequence): # List type

	types = tuple

	def __new__(cls, value):

		if isinstance(value, list):
			value = tuple(value)
		if isinstance(value, cls.types):
			return object.__new__(cls)

	def __init__(self, value):

		if isinstance(value, sophia_untyped):
			value = value.value
		if isinstance(value, list):
			value = tuple(value)
		self.value = value

	@classmethod
	def __cast__(cls, value):

		return cls(tuple(value.value))

class sophia_record(sophia_sequence): # Record type

	types = dict

	@classmethod
	def __cast__(cls, value):

		return cls(dict(value.value))

if __name__ == '__main__': # Hatred

	with mp.Manager() as runtime: # The stupidest global state you've ever seen in your life
		
		get_process().name = 'runtime'
		types = {k.split('_')[1]: sophia_type(v) for k, v in globals().items() if k.split('_')[0] == 'sophia'}
		operators = {v.symbol: sophia_operator(v) for k, v in arche.__dict__.items() if k.split('_')[0] == 'op'}
		functions = {k.split('_')[1]: sophia_function(v) for k, v in arche.__dict__.items() if k.split('_')[0] == 'sophia'}
		namespace = runtime.dict({0: runtime.Lock()}) # Unfortunate namespace hierarchy, but at least processes never write to the same memory
		namespace[1] = kleio.namespace((types | operators | functions).keys(), (types | operators | functions).values()) # Built-ins
		main = process(namespace, module('test.sophia')) # Spawn initial process
		main.start() # Start initial process
		main.join() # Prevent exit until initial process ends