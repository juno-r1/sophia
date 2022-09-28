# ☉
# 08/05/2022: Parser implemented (first working version)
# 15/07/2022: Hello world program
# 04/08/2022: Fibonacci program
# 09/08/2022: Basic feature set implemented (0.0)
# 16/08/2022: Basic feature set re-implemented (0.1)
# 20/08/2022: Type system implemented (0.1)

import core, hemera, kadmos

class definition: # Name binding object

	def __init__(self, name, value, type_value = 'untyped', reserved = False):

		self.name = name
		self.value = value
		self.type = type_value
		self.reserved = reserved

class node: # Base node object

	def __init__(self, value, *nodes):

		self.value = value
		self.head = None
		self.nodes = [i for i in nodes]
		self.instance = [] # Unfortunately, a stack
		self.path = 0 # Controls which node the runtime traverses to

class coroutine(node): # Base coroutine object

	def __init__(self, value, *tokens):

		super().__init__(value)
		self.namespace = [] # Coroutine namespace
		self.entry = self # Entry node; will be either self or a yield node
		self.exit = None # Exit address; main jumps to this address after execution
		self.active = False # State of coroutine; can be active (valid target for yield) or inactive (invalid target for yield)

class runtime(coroutine): # Runtime object contains runtime information and is the top level of the syntax tree

	def __init__(self, file_name): # God objects? What is she objecting to?

		super().__init__(None)
		with open(file_name, 'r') as f: # Binds file data to runtime object
			self.file_data = f.read().splitlines()
		self.name = file_name.split('.')[0]
		self.value = self
		self.namespace = [[definition(*item) for item in core.init_types()] + [definition(*item) for item in core.init_functions()]] # Initialises main with built-in types and functions
		self.builtins = len(self.namespace[0]) - 1
		self.address = None
		self.routine = self # Currently active coroutine

	def execute(self): # Runs the module

		self.active = True
		tree = self.parse() # Here's tree
		hemera.debug_tree(tree) # Uncomment for parse tree debug information
		print('===')
		value = None # Value register
		while self.value: # Execution loop
			#hemera.debug_runtime(self)
			if self.address: # If destination specified by node:
				#print('Call!')
				if isinstance(self.value, function_definition) and self.value.path == len(self.value.nodes):
					self.value.instance.pop()
				self.value.path = 0
				self.address.exit = self.value # Store source address in destination node
				self.value = self.address # Move to addressed node
				self.address = None # Remove address from main
				if isinstance(self.value, coroutine):
					self.value.path = 0
				elif isinstance(self.value, left_bracket): # Corrects path when destination is a function call
					self.value.path = 2
				value = self.value.instance[-1].send(value)
			elif self.value.nodes and self.value.path < len(self.value.nodes): # Walk down
				self.value.nodes[self.value.path].head = self.value # Sets child head to self
				self.value = self.value.nodes[self.value.path] # Set value to child node
				if isinstance(self.value, coroutine):
					self.value.path = len(self.value.nodes) # Adds new counter to stack, skipping all nodes
				self.value.instance.append(self.value.execute()) # Initialises generator
				value = self.value.instance[-1].send(value)
			else: # Walk up
				while self.value.path == len(self.value.nodes) and not self.address: # While last node of branch:
					if not isinstance(self.value, coroutine):
						self.value.instance.pop() # Removes generator
					self.value.path = 0
					self.value = self.value.head # Walk upward
					self.value.path = self.value.path + 1 # Increment path counter
					if self.value is self: # Check if finished
						if self.value.path == len(self.nodes):
							self.value = None
						break
					if isinstance(self.value, coroutine):
						value = self.value.instance[-2].send(value)
					else:
						value = self.value.instance[-1].send(value)
		else:
			self.active = False
			for item in self.namespace[0][self.builtins::-1]: # Unbinds built-ins in reverse order to not cause problems with the loop
				self.unbind(item.name)
			hemera.debug_namespace(self)
			yield self # Returns runtime object to facilitate imports

	def parse(self, meta_node = None): # Recursively descends into madness and returns a tree of nodes

		lines = []

		if meta_node: # Handles the meta-statement
			input_string = meta_node.nodes[0].evaluate().split('\n')
		else:
			input_string = self.file_data

		for line in input_string:
			i = line.find('//') # Handles comments, except for in strings
			if i == -1: # This conditional wouldn't even be necessary if Python did list slices right
				lines.append(kadmos.recurse_split(line))
			else:
				lines.append(kadmos.recurse_split(line[0:i]))
	
		tokens = []
		scopes = []

		for line in lines: # Tokenises each item in lines
			scope = line.count('\t') # Gets scope level from number of tabs
			if line[-1] == '' or line[scope:] == []:
				continue # Skips empty lines
			if not kadmos.balanced(line):
				raise SyntaxError('Unmatched parentheses')
			tokens.append([])
			scopes.append(scope)
			for n, token in enumerate(line[scope:]): # Skips tabs
				if token in kadmos.symbols or token in kadmos.operator_list:
					if token in ['(', '[', '{']:
						tokens[-1].append(left_bracket(token, 1))
						if line[scope:][n + 1] in [')', ']', '}']:
							tokens[-1].append(keyword(None))
					elif token in [')', ']', '}']:
						tokens[-1].append(right_bracket(token, 1))
					elif len(tokens[-1]) > 0 and isinstance(tokens[-1][-1], (literal, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
						for i, level in enumerate(kadmos.binding_power): # Gets the left-binding power of the operator
							if token in level:
								if token in ['^', '.', ',', ':']:
									tokens[-1].append(infix_r(token, i + 1))
								else:
									tokens[-1].append(infix(token, i + 1))
								break
						else:
							tokens[-1].append(keyword(token))
					else:
						tokens[-1].append(prefix(token, len(kadmos.binding_power) + 1)) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
				else:
					if token in kadmos.structure_tokens or token in kadmos.keyword_tokens:
						tokens[-1].append(keyword(token))
					else:
						if len(tokens[-1]) > 0 and isinstance(tokens[-1][-1], literal): # Checks for type
							type_value = tokens[-1].pop().value
						else:
							type_value = 'untyped'
						if n < len(line[scope:]) - 1 and line[scope:][n + 1] in ['(', '[']:
							tokens[-1].append(reference(token))
						else:
							tokens[-1].append(literal(token))
						setattr(tokens[-1][-1], 'type', type_value) # Sets type

		parsed_lines = []

		for line in tokens:
			if line[0].value in kadmos.structure_tokens:
				statement_id = line[0].value + '_statement'
				x = eval(statement_id + '(line)') # Cheeky little hack that makes a node for whatever structure keyword is specified
			elif line[0].value in kadmos.keyword_tokens:
				x = line[0] # Keywords will get special handling later
			elif line[-1].value == ':':
				x = function_definition(line)
			elif len(line) > 1 and line[1].value == ':':
				x = assignment(line)
			elif len(line) > 1 and line[1].value == 'is':
				x = binding(line)
			else: # Only necessary because of function calls with side effects
				x = expression(line)
			parsed_lines.append(x)

		if meta_node:
			main = meta_node
		else:
			main = self
		head = main # Head token
		last = main # Last line
		setattr(main, 'scope', 0)

		for i, line in enumerate(parsed_lines):
			setattr(line, 'scope', scopes[i] + 1) # Since main has scope 0

		for i, line in enumerate(parsed_lines): # Groups lines based on scope
			if line.scope > head.scope + 1: # If entering scope
				head = last # Last line becomes the head node
			elif line.scope < head.scope + 1: # If exiting scope
				if line.scope > 1: # If statement is in local scope:
					for n in parsed_lines[i::-1]: # Find the last line containing the current line in its direct scope, searching backwards from the current line
						if n.scope == line.scope - 1: # If such a line is found:
							head = n # Make it the head node
							break
				else: # If statement is in global scope:
					head = main # Resets head to main node
			head.nodes.append(line) # Link nodes
			last = line
		else:
			return main

	def bind(self, name, value, type_value = None): # Creates or updates a name binding in main

		for item in self.namespace[-1]: # Finds and updates a name binding
			if item.name == name:
				if item.reserved: # If the name is bound, or is a loop index:
					raise NameError('Cannot bind to reserved name')
				else:
					if isinstance(item.value, definition): # If alias:
						item.value.value = value # Binding can have little a indirection. As a treat
					else:
						item.value = value
					if type_value != 'untyped':
						item.type = type_value
				break
		else: # Creates a new name binding
			if type_value:
				self.namespace[-1].append(definition(name, value, type_value))
			else:
				self.namespace[-1].append(definition(name, value))

	def unbind(self, name): # Destroys a name binding in main

		for i, item in enumerate(self.namespace[-1]): # Finds and destroys a name binding
			if item.name == name:
				index = i
				break
		else:
			raise NameError('Undefined name: ' + name)

		del self.namespace[-1][index] # Destroy the binding outside of the loop to prevent issues with the loop

	def find(self, name): # Retrieves a name binding from a module
		
		for space in self.namespace[::-1]: # Searches module in reverse order
			for item in space:
				if item.name == name: # If the name is in the module:
					return item # Return the binding
		else:
			raise NameError('Undefined name: ' + name)

	def cast(self, value, type_value): # Checks type for value and returns boolean
				
		type_node = self.find(type_value).value
		stack = []
		while isinstance(type_node, type_statement): # Get all supertypes for type
			stack.append(type_node)
			type_node = main.find(type_node.supertype).value
		else:
			stack.append(type_node) # Guaranteed to be a built_in
		while stack: # Check type down the entire tree
			type_node = stack.pop()
			if isinstance(type_node, type_statement): # If user-defined:
				self.namespace.append([definition(type_value, value, type_value, reserved = True)]) # Bind special variable in a new scope
				for item in type_node.nodes[1:]: # Executing the node is the same as checking the value's type
					item.execute()
				else:
					return_value = value
					self.namespace.pop() # Destroy scope
			else: # If built-in:
				return_value = type_node(value) # Corrects type for built-ins
		else:
			return return_value # Return indicates success; cast() raises an exception on failure

class literal(node): # Adds literal behaviours to a node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = 0

	def nud(self, lex):

		return self # Gives self as node

	def execute(self): # Terminal nodes

		try:
			value = float(self.value) # Attempt to cast to float
			if value % 1 == 0:
				value = int(value) # Attempt to cast to int
		except ValueError:
			if self.value[0] in ['"', "'"]:
				value = self.value[1:-1] # Interpret as string
			elif self.value == 'true':
				value = True
			elif self.value == 'false':
				value = False
			elif self.value == 'null':
				value = None
			else: # If reference:
				value = main.find(self.value).value # Returns value referenced by name
		yield value # Send value to main

class keyword(node): # Adds keyword behaviours to a node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = 0

	def nud(self, lex):

		return self

	def execute(self):

		if self.value == 'continue':
			raise Continue
		elif self.value == 'break':
			raise StopIteration
		elif self.value is None:
			yield ()

class reference(node): # Adds function call / sequence reference behaviours to a node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = 0

	def nud(self, lex): # Basically bypasses this token entirely and implements the LED of the following left bracket

		lex.use() # Gets the next token, which is guaranteed to be a left bracket
		return lex.token.led(lex, self) # This token doesn't even *have* a LED, but it's guaranteed to call the LED of the following left bracket

	def execute(self):

		yield main.find(self.value).value # Retrieve value from reference

class prefix(node): # Adds prefix behaviours to a node

	def __init__(self, value, lbp):

		super().__init__(value)
		self.lbp = lbp

	def nud(self, lex):

		n, next_token = recursive_parse(lex, self.lbp)
		self.nodes = [n]
		return self, next_token

	def execute(self): # Unary operators

		op = 'unary_' + kadmos.operator_dict[self.value] # Gets the name of the operator
		x = yield
		yield core.operators[op](x)

class infix(node): # Adds infix behaviours to a node

	def __init__(self, value, lbp):

		super().__init__(value)
		self.lbp = lbp

	def led(self, lex, left):

		n, next_token = recursive_parse(lex, self.lbp)
		self.nodes = [left, n]
		return self, next_token

	def execute(self):
		
		op = kadmos.operator_dict[self.value] # Gets the name of the operator
		x = yield
		y = yield
		yield core.operators[op](x, y) # Uses the operator named in op

class infix_r(node): # Adds right-binding infix behaviours to a node

	def __init__(self, value, lbp):

		super().__init__(value)
		self.lbp = lbp

	def led(self, lex, left):

		n, next_token = recursive_parse(lex, self.lbp - 1)
		self.nodes = [left, n]
		return self, next_token

	def execute(self):

		if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a list
			left = self
			right = []
			while left.nodes and left.value == ':':
				right.append(left.nodes[0].evaluate())
				left = left.nodes[1]
			else:
				right.append(left.evaluate())
				if isinstance(right[0], str):
					return {right[0]: right[1]}
				else:
					return slice(right)
		elif self.value == ',': # Sorts out comma-separated parameters by returning them as a tuple
			left = self
			right = []
			while left.nodes and left.value == ',':
				right.append(left.nodes[0].evaluate())
				left = left.nodes[1]
			else:
				right.append(left.evaluate())
				return tuple(right)
		elif self.value == '.': # Sorts out the dot operator
			name = self.nodes[0].value
			left = main.find(name) # Gets binding for name
			right = self.nodes[1]
			if left.type == 'module': # If module:
				main.module = left.value
				return right.evaluate()
			else: # If type operation:
				x = infix_r(',', None)
				x.nodes = [literal(right.nodes[0].value), right.nodes[1]]
				right.nodes[1] = x # Inserts the bound value into the syntax tree as an argument of the function call
				right.nodes[1].nodes[0].value = self.nodes[0].value # Guarantees reference type for name
				if right.nodes[1].nodes[1].value is None:
					right.nodes[1] = right.nodes[1].nodes[0]
				main.module = main.find(left.type).value
				return right.evaluate()
		else: # Binary operators
			op = main.operator_dict[self.value] # Gets the name of the operator
			x = self.nodes[0].evaluate()
			y = self.nodes[1].evaluate()
			return core.operators[op](x, y) # Uses the operator named in op

class left_bracket(node): # Adds left-bracket behaviours to a node

	def __init__(self, value, lbp):

		super().__init__(value)
		self.lbp = lbp

	def nud(self, lex): # For normal parentheses

		n, next_token = recursive_parse(lex, self.lbp)
		self.nodes = [n]
		try:
			lex.use()
			return self, lex.peek # The bracketed sub-expression as a whole is essentially a literal
		except StopIteration:
			return self, eol()

	def led(self, lex, left): # For function calls

		n, next_token = recursive_parse(lex, self.lbp)
		self.nodes = [left, n]
		try:
			lex.use()
			return self, lex.peek # The bracketed sub-expression as a whole is essentially a literal
		except StopIteration:
			return self, eol()

	def execute(self):

		if self.value == '(':
			if isinstance(self.nodes[0], reference): # Function calls
				body = yield
				args = yield
				if not isinstance(args, tuple): # Type correction
					args = tuple([args]) # Very tiresome type correction, at that
				if isinstance(body, function_definition): # If user-defined:
					#if isinstance(self.head.head, return_statement): # Tail call optimisation
					#	print(body.exit, main.routine.exit)
					#	body.exit = main.routine.exit
					#	main.namespace.pop() # Destroy namespace
					#	main.routine.instance.pop() # Destroy spare instance
					routine = main.routine # Save calling environment
					main.routine = body
					main.address = body
					value = yield args # Function yields back into call to store return value
					main.routine = routine # Reset calling environment
					yield value
				else: # If built-in:
					try:
						if args: # Python doesn't like unpacking empty tuples
							yield body(*args) # Since body is a Python function in this case
						else:
							yield body()
					except TypeError:
						raise TypeError(name + ' is not a function')
			else: # Arithmetic brackets
				x = yield
				yield x
		elif self.value == '[': # Sequence expressions
			if isinstance(self.nodes[0], reference): # Sequence index
				name = yield
				subscript = yield
				for i in subscript: # Iteratively accesses the sequence
					if isinstance(i, str):
						if i not in name:
							raise KeyError('Key not in record: ' + i)
					elif isinstance(i, slice):
						try:
							if i.nodes[1] < -1 * len(name) or i.nodes[1] > len(name): # If out of bounds:
								raise IndexError('Index out of bounds')
						except TypeError:
							raise IndexError('Cannot slice element')
					else:
						if i < -1 * len(name) or i >= len(name): # If out of bounds:
							raise IndexError('Index out of bounds')
					if isinstance(i, slice):
						name = [name[n] for n in i.value] # Constructs slice using range
					else:
						name = name[i] # Python can handle this bit
				yield name # Return the accessed value
			else: # Sequence constructor
				items = yield
				if isinstance(items, slice): # If slice:
					yield items.execute() # Gives slice expansion
				else:
					if not isinstance(items, tuple):
						items = [items]
					else:
						items = list(items)
				if isinstance(items[0], dict): # If items is a record
					yield {list(item.keys())[0]: list(item.values())[0] for item in items} # Stupid way to merge a list of dictionaries
				else: # If items is a list
					if items and items != [None]: # Handles empty lists
						yield items
					else:
						yield []
		elif self.value == '{': # Meta-statement
			main.parse(self) # Run-time parser stage
			for item in self.nodes[1:]:
				return_value = item.execute() # Run-time execution stage
			self.nodes = [self.nodes[0]] # Erase tree
			return return_value

class right_bracket(node): # Adds right-bracket behaviours to a node

	def __init__(self, value, lbp):

		super().__init__(value)
		self.lbp = lbp

class slice(node): # Initialised during execution

	def __init__(self, slice_list):

		if len(slice_list) == 2: # Normalises list slice
			slice_list.append(1)
		if slice_list[1] >= 0: # Correction for inclusive range
			slice_list[1] = slice_list[1] + 1
		else:
			slice_list[1] = slice_list[1] - 1
		super().__init__(range(*slice_list), *slice_list) # Stores slice and iterator

	def __iter__(self): # Overrides __iter__() method

		return iter(self.value) # Enables iteration over range without expanding slice

	def execute(self): # Returns expansion of slice

		return [i for i in self.value]

class eol(node): # Creates an end-of-line node

	def __init__(self):

		super().__init__(None)
		self.lbp = -1

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__(tokens[1]) # Type
		if len(tokens) > 3: # Naive check for subtyping
			self.supertype = tokens[3].value # Supertype
		else:
			self.supertype = None

	def execute(self):

		name = self.value.value
		for item in self.nodes: # Bind type operations to type node
			if isinstance(item, function_definition):
				self.namespace.append(definition(item.value[0].value, item, item.value[0].type, reserved = True))
		main.bind(name, self, 'type') # Creates an empty binding to manage scope

	def find(self, name):

		for binding in self.namespace: # Searches namespace
			if binding.name == name: # If the name is in the namespace:
				return binding # Return the binding
		else:
			raise NameError('Undefined name: ' + name)

class function_definition(coroutine):

	def __init__(self, tokens):

		super().__init__(tokens[0:-1:2]) # Sets name and a list of parameters as self.value

	def execute(self):

		name = self.value[0].value # Definition
		type_value = self.value[0].type # Gets the function type
		return_value = None
		main.bind(name, self, type_value)
		while True: # Execution loop
			args = yield return_value
			params = self.value[1:] # Gets the function parameters
			main.namespace.append([]) # Add the namespace to main
			self.instance.append(self.execute()) # Initialise new instance for recursion support
			self.instance[-1].send(None) # Create function definition in new namespace
			main.namespace[-1] = main.namespace[-1] + [definition(param.value, None, param.type, True) for param in params] # Constructs a new copy of the namespace each time the function is called
			if len(params) == len(args):
				for i, item in enumerate(main.namespace[-1][1:]): # Update parameters with arguments
					item.value = main.cast(args[i], item.type) # Checks arguments for type
			else:
				raise SyntaxError('Expected {0} arguments; received {1}'.format(len(params), len(args)))
			self.active = True
			for item in self.nodes:
				try:
					yield
				except (Return, Yield) as status: # Return and yield statements pass back here
					return_value = main.cast(status.args[0], type_value)
					break
			else: # Default behaviour for no return or yield
				main.address = self.exit
				main.namespace.pop()
				self.entry = self
				self.exit = None
				self.active = False
				return_value = main.cast(None, type_value)

class assignment(node):

	def __init__(self, tokens):

		super().__init__(tokens[0], expression(tokens[2:])) # Typed assignments are always handed by typed_statement(), so this is fine

	def execute(self):

		name = self.value.value
		type_value = self.value.type
		value = yield # Yields to main
		value = main.cast(value, type_value)
		main.bind(name, value, type_value)
		yield # Yields to go up

class binding(node):

	def __init__(self, tokens):

		super().__init__([tokens[0], tokens[2]])

	def execute(self):
			
		name = self.value[0].value
		type_value = self.value[0].type
		value = self.value[1].value
		for item in main.namespace[-1]: # Check scope for binding, since find() doesn't
			if item.name == value:
				if isinstance(item.value, definition):
					raise NameError('Cannot chain aliases')
				else:
					main.cast(item.value, type_value)
					main.bind(name, item, type_value) # Creates a binding referencing another binding
					yield
		else:
			raise NameError('Alias out of scope')

class if_statement(node):

	def __init__(self, tokens):

		super().__init__(None, expression(tokens[1:-1]))

	def execute(self):

		condition = yield
		if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			raise ValueError('Condition must evaluate to boolean')
		if condition is True:
			for item in self.nodes[1:]:
				yield
		else:
			main.branch = True
		yield

class while_statement(node):

	def __init__(self, tokens):

		super().__init__(None, expression(tokens[1:-1]))

	def execute(self):

		condition = self.nodes[0].execute()
		if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			raise ValueError('Condition must evaluate to Boolean')
		return_value = None
		try:
			while condition:
				try:
					for item in self.nodes[1:]:
						return_value = item.execute()
					condition = self.nodes[0].execute()
				except Continue: # Continue
					continue
			else:
				return return_value
		except StopIteration: # Break
			return return_value

class for_statement(node):

	def __init__(self, tokens):

		super().__init__(None, tokens[1], expression(tokens[3:-1]))

	def execute(self):

		index = self.nodes[0]
		sequence = iter(self.nodes[1].execute())
		main.bind(index.value, None, index.type)
		return_value = None
		try:
			while True: # Loop until the iterator is exhausted
				main.bind(index.value, next(sequence), index.type) # Binds the next value of the sequence to the loop index
				try:
					for item in self.nodes[2:]:
						return_value = item.execute()
				except Continue: # Continue
					continue
		except StopIteration: # Break
			main.unbind(index.value) # Unbinds the index
			return return_value

class assert_statement(node):

	def __init__(self, tokens):

		super().__init__(None, tokens[1])

	def execute(self):
		
		main.branch = False
		try:
			try:
				binding = main.find(self.nodes[0].value)
			except NameError: # Catches unbound names
				return None
			assert_type = self.nodes[0].type
			if assert_type == 'untyped' and binding.value is None: # Handles behaviour of untyped assertion
				return None
			else:
				main.cast(binding.value, assert_type)
		except TypeError:
			main.namespace.pop() # Cleans up from cast()
			return None
		main.bind(binding.name, binding.value, assert_type)
		for item in self.nodes[1:]:
			return_value = item.execute()
		else:
			main.branch = True
			main.bind(binding.name, binding.value, binding.type)
			return return_value
	
class constraint_statement(node):

	def __init__(self, tokens):

		super().__init__(None)

	def execute(self):

		for constraint in self.nodes:
			value = constraint.execute()
			if value is not True and value is not False:
				raise ValueError('Constraint must evaluate to boolean')
			if value is False:
				raise TypeError('Constraint failed')

class else_statement(node):

	def __init__(self, tokens):

		if len(tokens) > 2:
			statement_id = tokens[1].value + '_statement'
			super().__init__(None, eval(statement_id + '(tokens[1:])')) # Else statement
			self.final = False
		else:
			super().__init__(None) # Final else
			self.final = True

	def execute(self): # Else statement
		
		if not main.branch:
			if self.final:
				for item in self.nodes:
					return_value = item.execute()
				return return_value
			else:
				inner = self.nodes[0]
				inner.nodes.extend(self.nodes[1:]) # Reassign nodes to inner statement
				return_value = inner.execute()
				return return_value
		if self.final:
			main.branch = False

class return_statement(node):

	def __init__(self, tokens):

		value = tokens[1:]
		if value:
			super().__init__(None, expression(value))
		else:
			super().__init__(None)

	def execute(self):
		
		if self.nodes:
			return_value = yield # If main.tail is true, control never returns back here
		else:
			return_value = None
		main.address = main.routine.exit # Set address to exit
		main.routine.entry = main.routine # Reset entry and exit
		main.routine.exit = None
		main.namespace.pop() # Destroy namespace
		main.routine.instance.pop() # Destroy spare instance
		return_value = main.routine.instance[-1].throw(Return(return_value)) # Throws Return with return value
		yield return_value

class yield_statement(node):

	def __init__(self, tokens):

		if 'to' in [token.value for token in tokens]:
			address = tokens[-1]
			value = tokens[1:-2]
		else:
			address = None
			value = tokens[1:]
		if value:
			super().__init__(address, expression(value))
		else:
			super().__init__(address)

	def execute(self):
			
		head_node = self.nodes[0].nodes[0] # Get head node
		if head_node.value == '(' and len(head_node.nodes) > 1: # If function call:
			setattr(head_node, 'tail', True)
			main.return_value = head_node # Facilitates tail call optimisation
		else:
			setattr(head_node, 'tail', False)
			main.return_value = self.nodes[0].execute()

class import_statement(node):

	def __init__(self, tokens):

		super().__init__(None, *tokens[1::2]) # Allows multiple imports

	def execute(self):

		for item in self.nodes:
			main.module = runtime(item.value + '.sophia')
			main.module.run(do_import = True)
			main.bind(item.value, main.module, 'module')
			main.module = None

class expression(node):

	def __init__(self, tokens):
		
		lex = lex_construct(tokens)
		tree, end = recursive_parse(lex, 0)
		super().__init__(None, tree)

	def execute(self):

		x = yield # Yield to go down
		yield x # Yield to go up
		
	# https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
	# https://abarker.github.io/typped/pratt_parsing_intro.html
	# https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
	# https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

class lex_construct: # Lex object to get around not being able to peek the next value of an iterator

	def __init__(self, tokens):

		self.lexes = [iter(tokens), iter(tokens)]
		self.token = None
		self.peek = next(self.lexes[1])

	def use(self): # Gets the next tokens

		self.token = next(self.lexes[0])
		self.peek = next(self.lexes[1])

class Return(Exception): pass # Handles return
class Yield(Exception): pass # Handles yield
class Continue(Exception): pass # Handles continue
class Break(Exception): pass # Handles break

def recursive_parse(lex, lbp): # Pratt parser for expressions - takes an iterator, its current token, and the left-binding power

	try:
		lex.use() # Gets next token from the iterator, if it exists
	except StopIteration: # Detects end of expression
		return lex.token, eol() # End-of-line token

	try: # NUD has variable number of return values
		left, next_token = lex.token.nud(lex) # Executes null denotation of current token
	except TypeError: # Is this a lazy substitute for an if-clause? Yes, but it works
		left, next_token = lex.token.nud(lex), None

	while lbp < lex.peek.lbp:
		try:
			lex.use()
			left, next_token = lex.token.led(lex, left) # Executes left denotation of current token
		except StopIteration: # Detects end of expression
			return left, eol() # End-of-line token

	return left, next_token # Preserves state of next_token for higher-level calls

main = runtime('test.sophia') # Initialises runtime object
main.instance = main.execute() # Initialises runtime generator
main.instance.send(None) # Starts runtime