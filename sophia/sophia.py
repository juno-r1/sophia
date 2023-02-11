'''
The Sophia module is the core of the language.
The module defines the runtime environment and core language constructs.
This is the root module and the only module that the user should need to access.
'''

# ☉ 0.3.1 07-02-2023

import aletheia, arche, hemera, kadmos, kleio, mathos
import multiprocessing as mp
from fractions import Fraction as real
from os import name as os_name
from queue import Empty

class runtime: # Base runtime object

	def __init__(self, address, *flags, root = 'sophia'):
		
		mp.freeze_support()
		try:
			mp.set_start_method('spawn' if os_name == 'nt' else 'fork')
		except RuntimeError:
			pass
		self.directory = root
		self.stream = mp.Queue() # Supervisor message stream
		self.pool = mp.Pool(initializer = self.initialise)
		self.main = task(module(address, root = self.directory), [], flags) # Initial task
		self.tasks = {self.main.pid: kleio.proxy(self.main)} # Proxies of tasks
		self.events = {} # Persistent event tasks
		self.flags = flags

	def initialise(self): # Cheeky way to sneak a queue into a task
	
		mp.current_process().stream = self.stream

	def call(self, pid, routine, args):

		routine = task(routine, args, self.flags)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].requests.append(pid) # Submit request for return value

	def bind(self, pid, routine, args):
		
		event = aletheia.sophia_event(routine)
		routine = task(routine, args, self.flags)
		self.tasks[routine.pid] = kleio.proxy(routine)
		if event:
			routine.node = routine.start.nodes[0]
			routine.path = [0, 0]
			self.events[routine.pid] = routine # Persistent reference to event
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.reference(routine)) # Return reference to process

	def link(self, pid, name, args):
		
		routine = task(module(name, root = self.directory), args, self.flags)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.reference(routine)) # Return reference to process

	def send(self, pid, reference, message):
		
		if reference.event:
			self.tasks[reference.pid].result.get() # Wait until routine is done with previous message
			namespace = self.tasks[reference.pid].calls.recv() # Get namespace from task
			routine = self.events[reference.pid]
			routine.prepare(namespace, message) # Mutate this version of the task
			self.tasks[reference.pid].result = self.pool.apply_async(routine.execute)
		else:
			self.tasks[reference.pid].messages.send(message)

	def resolve(self, pid, reference):

		if self.tasks[reference.pid].result.ready():
			self.tasks[pid].calls.send(self.tasks[reference.pid].result.get())
		else:
			self.tasks[reference.pid].requests.append(pid) # Submit request for return value

	def terminate(self, pid):

		value = self.tasks[pid].result.get()
		for process in self.tasks[pid].requests:
			self.tasks[process].calls.send(value)
		self.tasks[pid].requests = []
		for process in self.tasks[pid].references:
			self.tasks[process].count = self.tasks[process].count - 1
			if self.tasks[process].count == 0:
				del self.tasks[process] # Free referenced tasks
				if process in self.events: # Free events
					del self.events[process]
		if pid == self.main.pid:
			self.stream.put(None) # End supervisor
		elif self.tasks[pid].count == 0: # Free own task
			del self.tasks[pid]

	def run(self): # Supervisor process and pool management

		if 'profile' in self.flags:
			from cProfile import Profile
			pr = Profile()
			pr.enable()
		message = True
		interval = 10 if 'timeout' in self.flags or self.directory == 'harmonia' else None # Timeout interval
		self.tasks[self.main.pid].result = self.pool.apply_async(self.main.execute) # Start execution of initial module
		while message: # Event listener pattern; runs until null sentinel value sent from initial module
			try:
				message = self.stream.get(timeout = interval)
				if not message:
					break
				if 'debug_supervisor' in self.flags:
					print(*message)
				getattr(self, message[0])(*message[1:]) # Executes event
			except Empty:
				message = True
				hemera.debug_error('sophia', 0, 'TIME', ()) # Prints timeout warning but continues
		self.pool.close()
		self.pool.join()
		if 'profile' in self.flags:
			pr.disable()
			pr.print_stats(sort = 'tottime')
		return self.tasks[self.main.pid].result.get()

class task:

	def __init__(self, routine, args, flags): # God objects? What is she objecting to?
		
		params = [item.value for item in routine.value[1:]] # Gets coroutine name, return type, and parameters
		types = [item.type for item in routine.value[1:]] # Get types of params
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		self.name = routine.name
		self.type = routine.type
		self.start = routine # Start node
		self.node = routine # Current node; sets initial module or start node as entry point
		self.flags = flags
		self.built_in_values = aletheia.types | mathos.operators | arche.functions
		self.built_in_types = {i: 'type' for i in aletheia.types} | {i: 'operator' for i in mathos.operators} | {i: 'function' for i in arche.functions}
		self.values = dict(zip(params, args)) # Dict of values for faster access
		self.types = dict(zip(params, types)) # Dict of types for correct typing
		self.reserved = [item.value for item in routine.value] # List of reserved names in the current namespace
		self.supertypes = aletheia.supertypes # Dict of type hierarchy
		self.path = [0]
		self.data = [] # Unfortunately, a stack
		self.type_data = [] # Unfortunately, another stack
		self.sentinel = None # Return value of task

	def execute(self): # Target of run()
		
		debug_task = True if 'debug_task' in self.flags else False
		if 'debug_tree' in self.flags:
			hemera.debug_tree(self.node)
		if not self.node.nodes: # Empty routine
			self.node = None
		while self.node: # Runtime loop
			if debug_task:
				hemera.debug_task(self)
			if self.path[-1] == -1: # Branch
				self.node = self.node.head # Walk upward
				self.path.pop()
				self.path[-1] = self.path[-1] + 1
				continue # Skip start function
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
		if 'debug_namespace' in self.flags:
			hemera.debug_namespace(self)
		self.calls.send((self.values,
						 self.types,
						 self.reserved,
						 self.supertypes)) # Send mutable namespace to supervisor
		self.message('terminate')
		return self.sentinel

	def prepare(self, namespace, message): # Sets up task for event execution

		self.node = self.start.nodes[1]
		self.path = [1, 0]
		self.values, self.types, self.reserved, self.supertypes = namespace # Update version of task in this process
		self.bind(self.start.message.value, message)

	def get(self, type_name = 'untyped'): # Data retrieval checks for type

		value, known = self.data.pop(), self.type_data.pop()
		return value if known and type_name in self.supertypes[known] else self.cast(value, type_name, known) # Instantly succeeds if checked type is supertype of known type

	def send(self, value, type_name = None):
		
		self.data.append(value)
		self.type_data.append(type_name)

	def message(self, instruction = None, *args):
		
		mp.current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def bind(self, name, value, type_name = None): # Creates or updates a name binding in main
		
		if name in self.reserved or name in self.built_in_values: # Quicker and easier to do it here
			return self.error('BIND', name)
		self.values[name] = value # Mutate namespace
		if isinstance(value, type_statement) and value.name not in self.supertypes: # Deals with types being sent between routines
			self.find(value.supertype) # Result isn't used; only called to verify existence in routine
			self.supertypes[value.name] = [value.name] + self.supertypes[value.supertype]
		if type_name:
			self.types[name] = type_name
		elif name not in self.types:
			self.types[name] = 'untyped'
		return value

	def unbind(self, name): # Destroys a name binding in the current namespace

		del self.values[name], self.types[name] # Delete binding if it exists in the namespace

	def find(self, name): # Retrieves a binding's value in the current namespace
		
		if name in self.built_in_values:
			return self.built_in_values[name]
		elif name in self.values:
			return self.values[name]
		else:
			return self.error('FIND', name)

	def check(self, name, default = None): # Internal function to check if a name has a type bound to it

		if name in self.built_in_types:
			return self.built_in_types[name]
		elif name in self.types:
			return self.types[name]
		else:
			return default

	def cast(self, value, type_name, known = None): # Checks type of value and returns boolean
		
		type_routine = self.find(type_name)
		stack = [] # Stack of user-defined types, with the requested type at the bottom
		while type_routine.supertype and type_routine.name != known: # Known type optimises by truncating stack
			stack.append(type_routine)
			type_routine = self.find(type_routine.supertype) # Type routine is guaranteed to be a built-in when loop ends, so it checks that before any of the types on the stack
		if type_routine(value) is None: # Check built-in type
			return self.error('CAST', type_routine.name, str(value))
		while stack:
			type_routine = stack.pop()
			if type_routine(self, value) is None:
				return self.error('CAST', type_routine.name, str(value))
		else:
			return value # Return indicates success; cast() raises an exception on failure

	def branch(self, path = -1):

		self.path[-1] = path # Skip nodes

	def error(self, status, *args): # Error handler
		
		if not self.node.asserted: # Suppresses error for assert statement
			if 'suppress' not in self.flags:
				hemera.debug_error(self.name, self.node.line, status, args)
			self.node = None # Immediately end routine

# Parse tree definitions

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
		self.asserted = False # Controls assertion handling

	def __str__(self): return str(self.value)

class coroutine(node): # Base coroutine object

	def __init__(self, value):

		super().__init__(value)
		self.active = 0

	def __str__(self): return str(['{0} {1}'.format(item.type, item.value) for item in self.value])

class module(coroutine): # Module object is always the top level of a syntax tree

	def __init__(self, file_name, source = None, name = None, root = 'sophia'):

		super().__init__(value = [self]) # Sets initial node to self
		if source: # Meta-statement
			self.file_data = file_name
			self.name, self.type = name, 'untyped'
		else: # Default module creation
			with open('{0}\\{1}'.format(root, file_name), 'r') as f: # Binds file data to runtime object
				self.file_data = f.read() # node.parse() takes a string containing newlines
			self.name, self.type = file_name.split('.')[0], 'untyped'
		self.active = -1
		self.source = source
		self.parse(self.file_data) # Here's tree

	def __str__(self): return 'module ' + self.name

	def parse(self, data): # Recursively descends into madness and creates a tree of nodes with self as head
		
		lines = [kadmos.split(line) for line in kadmos.group(data.splitlines())] # Splits lines into symbols
		tokens, scopes, i = [], [], 0
		for line in lines: # Tokenises each item in lines
			i = i + 1
			if isinstance(line, str): # Error messages
				return hemera.debug_error(self.name, self.source.line if self.source else i, line, ()) # Executes with empty parse tree
			scope = line.count('\t') # Gets scope level from number of tabs
			if not line[scope:]:
				continue # Skips empty lines
			scopes.append(scope)
			tokens.append([])
			for symbol in line[scope:]: # Skips tabs
				if symbol == '\r': # Increments line count for trailing lines
					i = i + 1
					continue
				elif (symbol[0] in kadmos.characters or symbol[0] in '\'\"') and (symbol not in kadmos.keyword_operators): # Quick test for literal
					if symbol in kadmos.structure_tokens or symbol in kadmos.keyword_tokens:
						if tokens[-1] and symbol in ('if', 'else'):
							token = left_conditional(symbol) if symbol == 'if' else right_conditional(symbol)
						else:
							token = keyword(symbol)
							if tokens[-1] and tokens[-1][-1].value == 'else':
								tokens[-1].pop()
								token.branch = True
					else:
						if symbol[0] in '.0123456789': # Terrible way to check for a number without using a try/except block
							token, token.type = (literal(real(symbol)), 'real') if '.' in symbol else (literal(int(symbol)), 'integer') # Type of literals is known at parse time
						elif symbol in kadmos.sub_values:
							token = literal(kadmos.sub_values[symbol]) # Interpret booleans and null
							token.type = 'boolean' if isinstance(token.value, bool) else None # Null is caught by untyped
						elif symbol[0] in '\'\"': # Strings have to be resolved at run time because they're indistinguishable from names otherwise
							token = literal(symbol[1:-1])
							token.type = 'string'
						else:
							token = name(symbol)
							if tokens[-1] and isinstance(tokens[-1][-1], name): # Checks for type
								token.type = tokens[-1].pop().value # Sets type of identifier
				else:
					if symbol in kadmos.parens[0::2]:
						if symbol == '(':
							token = function_call(symbol) if tokens[-1] and isinstance(tokens[-1][-1], name) else parenthesis(symbol)
						elif symbol == '[':
							token = sequence_index(symbol) if tokens[-1] and isinstance(tokens[-1][-1], name) else sequence_literal(symbol)
						elif symbol == '{':
							token = meta_statement(symbol)
					elif symbol in kadmos.parens[1::2]:
						token = right_bracket(symbol)
					elif tokens[-1] and isinstance(tokens[-1][-1], (literal, name, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
						if symbol in ('^', ':', ','):
							token = infix_r(symbol)
						elif symbol == '<-':
							token = bind(tokens[-1].pop().value)
						elif symbol == '->':
							token = send(symbol)
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
						elif symbol == '?':
							token = safe(symbol)
						elif symbol == '!':
							token = unsafe(symbol)
						else:
							token = prefix(symbol) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
				token.line = self.source.line if self.source else i
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
				elif line[0].type == 'interface' and '(' not in [token.value for token in line]:
					token = interface_statement(line)
				elif line[0].value[0] in kadmos.characters: # Functions have names and operators have symbols
					if line[1].value == 'awaits':
						token = event_statement(line)
					else:
						token = function_statement(line)
				else:
					token = operator_statement(line)
			elif len(line) > 1 and line[1].value == ':':
				token = assignment(line)
			else: # Tokenises expressions
				token = kadmos.lexer(line).parse() # Passes control to a lexer object that returns an expression tree when parse() is called
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

		node, node.length, path = self, len(self.nodes), [0]
		while node: # Pre-runtime parse completes node linking, sets length, defines type operations and assertion
			if path[-1] == node.length: # Walk up
				if isinstance(node, assert_statement):
					node.asserted = True
					for i in range(node.active):
						node.nodes[i].asserted = True
				elif isinstance(node, event_statement):
					if not isinstance(node.nodes[0], start_statement):
						self.nodes = []
						return hemera.debug_error(self.name, node.line, 'EVNT', ())
					node.value = node.value + node.nodes[0].value
					node.types = [item.type for item in node.value]
				elif isinstance(node, type_statement):
					for item in node.nodes:
						if aletheia.sophia_function(item) and item.value[1].value == node.name: # Detect type operation
							item.value[1].type = node.supertype
							node.namespace[item.name] = item
					node.nodes = [item for item in node.nodes if not (aletheia.sophia_function(item) and item.value[1].value == node.name)] # Strip type operations from parse tree
					node.length = len(node.nodes) # Above operation changes length
				node = node.head # Walk upward
				if node:
					path.pop()
					path[-1] = path[-1] + 1
			else: # Walk down
				node.nodes[path[-1]].head = node # Set head
				node = node.nodes[path[-1]] # Set value to child node
				node.length = len(node.nodes) # Set length
				path.append(0)

		return self

	def execute(self, routine):
		
		routine.node = self.source
		if routine.node:
			routine.path.pop() # Handles meta-statement

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

	def __call__(self, routine, value): # Initialises type routine
		
		routine.message('call', self, [value])
		return routine.calls.recv()

	def start(self, routine): # Initialises type
		
		for name in self.interfaces:
			interface = routine.find(name)
			if not interface:
				return
			if not aletheia.sophia_interface(interface):
				return routine.error('CAST', 'interface', str(interface))
			if interface.supertype not in routine.supertypes[self.supertype]: # Check for compability of interface
				return routine.error('INTR', interface.name, self.name)
			self.namespace = self.namespace | {item.name: item for item in interface.nodes} # Interface operations override type operations
		routine.supertypes[self.name] = [self.name] + routine.supertypes[self.supertype]
		routine.bind(self.name, self, 'type')
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.sentinel = routine.find(self.name) # Returns cast value upon success
		routine.node = None

class interface_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__([tokens[0]]) # Type and type parameter
		self.name, self.type = tokens[0].value, tokens[0].value
		self.supertype = tokens[2].value if len(tokens) > 2 else 'untyped'
		param = name(tokens[0].value)
		param.type = self.supertype
		self.value.append(param)

	def start(self, routine): # Initialises type
		
		routine.bind(self.name, self, 'interface')
		routine.branch() # Skips body of routine

	def execute(self, routine): return

class operator_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets operator symbol and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.types = [item.type for item in self.value]

	def start(self, routine):
		
		routine.bind(self.name, self, 'operator')
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.node = None

	def unary(self, routine, x):
		
		routine.message('call', self, [x])
		return routine.cast(routine.calls.recv(), self.types[0])

	def binary(self, routine, x, y):
		
		routine.message('call', self, [x, y])
		return routine.cast(routine.calls.recv(), self.types[0])

class event_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([tokens[0]]) # Sets name and message parameter as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.message = tokens[2]
		self.types = [item.type for item in self.value]

	def start(self, routine):

		routine.bind(self.name, self, 'event')
		routine.branch()

class function_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.types = [item.type for item in self.value]

	def start(self, routine):
		
		routine.bind(self.name, self, 'function')
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.node = None

class assignment(node):

	def __init__(self, tokens): # Supports multiple assignment
		
		tokens = tokens.copy()
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

	def __str__(self): return 'assignment ' + str([item.value for item in self.value])

	def execute(self, routine):

		values, types = [], []
		for i in range(self.length - 1, -1, -1):
			type_name = self.value[i].type
			if not type_name:
				if self.value[i].value in routine.built_in_types:
					type_name = routine.built_in_types[self.value[i].value]
				elif self.value[i].value in routine.types:
					type_name = routine.types[self.value[i].value]
				else:
					type_name = 'untyped'
			values.append(routine.get(type_name))
			types.append(type_name)
		for i, name in enumerate(self.value):
			routine.bind(name.value, values[-1 - i], types[-1 - i])

class statement(node):

	def __str__(self): return ('else ' if self.branch else '') + type(self).__name__

class if_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self, routine):

		condition = routine.get('boolean')
		if not condition:
			routine.branch()

	def execute(self, routine): return

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
		
		sequence = arche.iterable(routine.get('iterable')) # Enables fast slice
		try:
			value = next(sequence)
			type_name = self.value.type if self.value.type else routine.check(self.value.value, default = 'untyped')
			routine.cast(value, type_name)
			routine.bind(self.value.value, value, type_name)
			routine.send(sequence, '.index') # Stack trickery with invalid type name
		except StopIteration:
			routine.branch(self.node.length)

	def execute(self, routine):
		
		sequence, type_name = routine.data.pop(), routine.type_data.pop() # Don't check for type
		while type_name != '.index':
			sequence, type_name = routine.data.pop(), routine.type_data.pop()
		try:
			value = next(sequence)
			routine.cast(value, routine.types[self.value.value])
			routine.bind(self.value.value, value)
			routine.send(sequence, '.index') # .index isn't even a type
			routine.branch(1) # Skip start
		except StopIteration:
			routine.unbind(self.value.value)

class assert_statement(statement):

	def __init__(self, tokens):
		
		nodes, sequence, parens = [], [], 0
		for token in tokens[1:-1]: # Collects all expressions in head statement
			if isinstance(token, left_bracket):
				parens = parens + 1
			elif isinstance(token, right_bracket):
				parens = parens - 1
			if token.value == ',' and parens == 0:
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
			if routine.get(self.nodes[i].type if self.nodes[i].type else 'untyped') is None:
				return routine.branch()

	def execute(self, routine): return
	
class constraint_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self, routine):
		
		for constraint in self.nodes:
			constraint = routine.get('boolean')
			if not constraint:
				routine.node = None
				return

class return_statement(statement):

	def __init__(self, tokens):
		
		super().__init__(None, kadmos.lexer(tokens[1:]).parse()) if len(tokens) > 1 else super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self, routine):
		
		if self.nodes:
			routine.sentinel = routine.get()
		routine.node = None

class link_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1::2]) # Allows multiple links
		self.branch = tokens[0].branch

	def __str__(self): return ('else ' if self.branch else '') + 'link_statement ' + str([item.value for item in self.nodes])

	def execute(self, routine):

		for item in self.value:
			name = item.value if '.' in item.value else (item.value + '.sophia')
			routine.message('link', name, [])
			routine.bind(name.split('.')[0], routine.calls.recv(), 'process')

class start_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[2::2])
		self.active = 0

	def __str__(self): return 'start ' + str([item.value for item in self.value])

	def start(self, routine):

		routine.branch()

	def execute(self, routine):

		routine.node = None

class else_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		self.branch = True

	def execute(self, routine): return # Final else statement

class identifier(node): # Generic identifier class

	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = 0

class literal(identifier): # Adds literal behaviours to a node

	def nud(self, lex): return self # Gives self as node

	def execute(self, routine): # Literal values are evaluated at parse time
		
		routine.send(self.value, self.type)

class name(identifier): # Adds name behaviours to a node

	def __init__(self, tokens):

		names = tokens.split('.')
		if names[0] in kadmos.sub_types: # Corrects shortened type names
			names[0] = kadmos.sub_types[names[0]]
		super().__init__(names[0])
		self.operation = names[1] if len(names) > 1 else None

	def __str__(self): return '{0}.{1}'.format(self.value, self.operation) if self.operation else self.value

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self, routine): # Terminal nodes
		
		value = routine.find(self.value)
		type_name = routine.check(self.value, default = self.type)
		if self.operation:
			for supertype in routine.supertypes[type_name]:
				type_routine = routine.find(supertype)
				if self.operation in type_routine.namespace:
					operation = type_routine.namespace[self.operation]
					routine.send(operation, 'function')
					break
			else:
				return routine.error('FIND', self.value + '.' + self.operation)
		routine.send(value, type_name)

class keyword(identifier): # Adds keyword behaviours to a node

	def __init__(self, tokens):

		super().__init__(tokens)
		self.active = 0

	def nud(self, lex): return self

	def start(self, routine):

		loop = routine.node
		while not isinstance(loop, (while_statement, for_statement)): # Traverses up to closest enclosing loop
			loop = loop.head
			routine.path.pop()
		routine.node = loop
		if self.value == 'continue':
			if loop.value: # For loop
				loop.execute(routine) if '.index' in routine.type_data else routine.branch(loop.length) # Tests if loop is unbound
			else:
				routine.branch(0)
		elif self.value == 'break':
			routine.branch()
			if loop.value: # End for loop correctly
				routine.data.pop() # Don't check for type
				type_name = routine.type_data.pop()
				while type_name != '.index':
					routine.data.pop()
					type_name = routine.type_data.pop()
				routine.unbind(loop.value.value)

	def execute(self, routine): return # Shouldn't ever be called anyway

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
		routine.send(op.unary(routine, x), op.types[0]) # Equivalent for all operators

class bind(prefix): # Defines the bind operator

	def __str__(self): return 'bind ' + self.value

	def execute(self, routine):
		
		address = routine.get('process')
		routine.bind(self.value, address, 'process') # Binds routine
		routine.send(address, 'process')

class receive(prefix): # Defines the receive operator

	def __str__(self): return '>' + self.value.value

	def nud(self, lex):

		self.value = lex.parse(self.lbp)
		return self

	def execute(self, routine):
		
		value = routine.messages.recv()
		routine.bind(self.value.value, value, self.value.type if self.value.type else None)
		routine.send(value, self.value.type if self.value.type else None)

class resolve(prefix): # Defines the resolution operator

	def execute(self, routine):
		
		reference = routine.get('process')
		routine.message('resolve', reference)
		routine.send(routine.cast(routine.calls.recv(), reference.type), reference.type)

class safe(prefix): # Defines the safety operator

	def execute(self, routine):

		value = routine.data.pop() # Bypass type checking
		routine.type_data.pop()
		routine.send(True if value is not None else False, 'boolean')

class unsafe(prefix): # Defines the unsafety operator

	def execute(self, routine):

		value = routine.get()
		routine.send(value if value else None) # I'm sure someone has a use for this

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self, routine):
		
		op = routine.find(self.value)
		x, y = routine.get(op.types[2]), routine.get(op.types[1]) # Operands are received in reverse order
		routine.send(op.binary(routine, y, x), op.types[0])

class left_conditional(infix): # Defines the conditional operator

	def __init__(self, value):

		super().__init__(value)
		self.active = 1

	def led(self, lex, left):
		
		n = lex.parse(self.lbp)
		left, n.nodes[0] = n.nodes[0], left # Swap for initial execution of condition
		self.nodes = [left, n]
		return self

	def start(self, routine):

		condition = routine.get('boolean')
		routine.node = self.nodes[1]
		routine.path.append(0 if condition else 1)

	def execute(self, routine): return

class right_conditional(infix): # Defines the conditional operator

	def __init__(self, value):

		super().__init__(value)
		self.active = 1

	def start(self, routine):
		
		routine.node = self.head
		routine.path.pop()
		routine.path[-1] = routine.node.length

	def execute(self, routine): return

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self, routine):

		if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a slice object or a dictionary
			x, y = routine.get(), routine.get()
			value = [y] + x if self.nodes and self.nodes[1].value == ':' else [y, x]
			if self.head.value == ':':
				routine.send(value)
			elif len(value) == 2:
				if aletheia.sophia_integer(value[0]): # Equalise integer type
					value[0] = int(value[0])
				routine.send(arche.element(value))
			else:
				routine.send(arche.slice(value))
		elif self.value == ',': # Sorts out comma-separated parameters by returning them as a list
			x, y = routine.get(), routine.get()
			routine.send([y] + x if self.nodes and self.nodes[1].value == ',' else [y, x])
		else: # Binary operators
			op = routine.find(self.value) # Gets the operator definition
			x, y = routine.get(op.types[2]), routine.get(op.types[1])
			routine.send(op.binary(routine, y, x), op.types[0])

class send(infix_r): # Defines the send operator

	def __str__(self): return 'send'

	def execute(self, routine):
		
		address = routine.get('process')
		routine.message('send', address, routine.get(address.event if address.event else 'untyped'))
		routine.send(address, 'process')

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

	def execute(self, routine):

		args = routine.get() if self.length > 1 else []
		if not isinstance(args, list): # Type correction
			args = [args] # Very tiresome type correction, at that
		if self.nodes[0].operation: # Type operation
			args = [routine.get()] + args # Shuffle arguments
		function = routine.get('callable') # Get actual function
		if len(function.types) - 1 != len(args):
			return routine.send(routine.error('ARGS', len(function.types) - 1, len(args))) # Requires data to be sent to the stack
		for i, arg in enumerate(args):
			type_name = function.types[i + 1] if function.types[i + 1] else 'untyped'
			if routine.cast(arg, type_name) is None:
				return routine.send(None)
		if isinstance(function, (function_statement, event_statement)):
			routine.message('bind' if isinstance(self.head, bind) else 'call', function, args)
			value = routine.calls.recv()
		else:
			value = function.call(*args) if args else function.call() # Sure wish apply() still existed in Python
		type_name = 'process' if aletheia.sophia_process(value) else (function.types[0] if function.types[0] else 'untyped')
		value = routine.cast(value, type_name)
		routine.send(value, type_name)

class parenthesis(left_bracket):

	def execute(self, routine): return

class sequence_index(left_bracket):

	def execute(self, routine):
		
		subscript, value = routine.get(), routine.get('sequence')
		if not isinstance(subscript, list):
			subscript = [subscript]
		for i in subscript: # Iteratively accesses the sequence
			routine.cast(value, 'sequence')
			length = len(value) # Only bother doing this when you need to
			if aletheia.sophia_integer(i): # Sophia's integer type is abstract, Python's isn't
				i = int(i)
			if aletheia.sophia_slice(i):
				if (not (-length <= i.indices[0] < length)) or (not (-length <= i.indices[1] < length)): # If out of bounds:
					return routine.send(routine.error('INDX', str(i.indices)))
			elif aletheia.sophia_record(value):
				if i not in value:
					return routine.send(routine.error('INDX', str(i)))
			else:
				if not (aletheia.sophia_integer(i) and -length <= i < length):
					return routine.send(routine.error('INDX', str(i)))
			if aletheia.sophia_slice(i):
				if aletheia.sophia_string(value):
					value = ''.join([value[n] for n in i]) # Constructs slice of string using range
				elif aletheia.sophia_record(value):
					items = list(value.items())
					value = dict([items[n] for n in i]) # Constructs slice of record using range
				else:
					value = tuple([value[n] for n in i]) # Constructs list of list or slice using range
			else:
				value = value[i] # Python can handle this bit
		routine.send(value) # Return the accessed value

class sequence_literal(left_bracket):

	def execute(self, routine):
		
		items = routine.get() if self.nodes else []
		if not isinstance(items, (list, arche.slice)):
			items = [items]
		if items and isinstance(items[0], arche.element): # If items is a key-item pair in a record
			routine.send(dict(iter(items))) # Better way to merge a list of key-value pairs into a record
		else: # If list or slice:
			routine.send(tuple(items)) # Tuple expands slice

class meta_statement(left_bracket):

	def __init__(self, value):

		super().__init__(value)
		self.active = 1

	def start(self, routine):
		
		tree = module(routine.get('string'), source = self, name = routine.name) # Here's tree
		routine.node = tree # Redirect control flow to new tree
		routine.path.append(0)

	def execute(self, routine): return

class right_bracket(operator): # Adds right-bracket behaviours to a node

	def nud(self, lex): return self