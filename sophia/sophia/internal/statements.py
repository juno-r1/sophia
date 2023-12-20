from .nodes import node, lexer
from .instructions import instruction as ins

class statement(node):
	"""Base statement node."""
	def __str__(self) -> str: return ('else ' if self.branch else '') + type(self).__name__

class coroutine(statement):
	"""Base coroutine node."""
	def __init__(
		self,
		value: list[node] | None
		) -> None:

		super().__init__(value)
		self.active = 0
		self.type = None

	def __str__(self) -> str: return str(['{0} {1}'.format(item.type, item.value) for item in self.value])

class module(coroutine):
	"""Base module node. This is always the top node of an AST."""
	def __init__(
		self,
		name: str
		) -> None:

		super().__init__(None) # Sets initial node to self
		self.active = -1
		self.name = name

	def __str__(self) -> str: return 'module ' + self.name

	def execute(self) -> tuple[ins, ...]:
		
		return ins('.return', '0'), # Default end of module

class type_statement(coroutine):
	"""Defines a type definition."""
	def __init__(
		self, 
		tokens: list[node]
		) -> None:
		
		super().__init__([tokens[0]]) # Sets name as value
		self.name, self.type = tokens[0].value, tokens[0].value
		values = [token.value for token in tokens]
		i, supertype, prototype = 1, None, False
		if i < len(tokens) and values[i] == 'extends':
			supertype = values[i + 1]
			supertype, i = node.sub_types[supertype] if supertype in node.sub_types else supertype, i + 2
		if i < len(tokens) and values[i] == 'with':
			j = values.index('=>') if '=>' in values else len(tokens)
			self.nodes, i = [lexer(tokens[i + 1:j]).parse()], j
			prototype = True
		if i < len(tokens) and values[i] == '=>':
			self.nodes, i = self.nodes + [lexer(tokens[i + 1:]).parse()], len(tokens)
		self.supertype, self.active = supertype if supertype else 'untyped', int(prototype)

	def start(
		self
		) -> tuple[ins, ...]:

		if self.active: # Necessary to check type of prototype
			return (ins(self.supertype, self.register, (self.nodes[0].register,)),
					ins('.type', self.name, (self.supertype, self.register)),
					ins('START', label = [self.name]))
		else:
			return (ins('.type', self.name, (self.supertype,)),
					ins('START', label = [self.name]))

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return (ins('.return', '0', (self.name,)),
				ins('END', label = [self.name]))

class event_statement(coroutine):
	"""Defines an event definition."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		super().__init__([tokens[0]]) # Sets name and message parameter as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.message = tokens[2]

	def start(
		self
		) -> tuple[ins, ...]:

		names = [item.value for item in self.value]
		types = [item.type if item.type else 'untyped' for item in self.value]
		return (ins('.event', self.name, label = [i for pair in zip(types, names) for i in pair] + [self.message.type, self.message.value]),
				ins('START', label = [self.name]))

	def execute(
		self
		) -> tuple[ins, ...]:

		if self.type:
			return (ins(self.type, self.register, ('&0',)),
					ins('.return', '0'),
					ins('END'))
		else:
			return (ins('.return', '0'),
					ins('END', label = [self.name]))

class function_statement(coroutine):
	"""Defines a function definition."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		try: # Single-line function definition
			i = [token.value for token in tokens].index('=>')
			super().__init__([token for token in tokens[0:i:2] if token.value != ')'])
			self.nodes = [return_statement(tokens[i::])]
		except ValueError:
			super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type

	def start(
		self
		) -> tuple[ins, ...]:
		
		names = [item.value for item in self.value]
		types = [item.type if item.type else 'untyped' for item in self.value]
		return (ins('.function', self.name, label = [i for pair in zip(types, names) for i in pair]),
				ins('START', label = [self.name]))

	def execute(
		self
		) -> tuple[ins, ...]: 
		
		if self.type:
			return (ins(self.type, self.register, ('&0',)),
					ins('.return', '0'),
					ins('END'))
		else:
			return (ins('.return', '0'),
					ins('END', label = [self.name]))

class assignment(statement):
	"""Defines an assignment."""
	def __init__( # Supports multiple assignment
		self,
		tokens: list[node]
		) -> None:
		
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

	def __str__(self) -> str: return 'assignment ' + str([item.value for item in self.value])

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return [ins('BIND')] + \
			   [ins(item.type if item.type else 'null',
				str(int(self.register) + i),
				(self.nodes[i].register,),
				label = [item.value])
				for i, item in enumerate(self.value)] + \
			   [ins('BIND', label = [item.value for item in self.value])]

class alias(statement):
	"""Defines a type alias."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:
		
		super().__init__(tokens[0], lexer(tokens[2:]).parse())

	def __str__(self) -> str: return 'alias ' + str(self.value.value)

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('.alias', self.value.value, (self.nodes[0].register,)),

class if_statement(statement):
	"""Defines an if statement."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		super().__init__(None, lexer(tokens[1:-1]).parse())
		self.active = 1
		self.branch = tokens[0].branch
		self.block = True

	def start(
		self
		) -> tuple[ins, ...]:
		
		return ins('.branch', self.register, (self.nodes[0].register,)),

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('.branch', self.register),

class while_statement(statement):
	"""Defines a while statement."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		super().__init__(None, lexer(tokens[1:-1]).parse())
		self.active = 1
		self.branch = tokens[0].branch
		self.block = True

	def start(
		self
		) -> tuple[ins, ...]:
		
		return ins('.branch', self.register, (self.nodes[0].register,)),

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('LOOP'),

class for_statement(statement):
	"""Defines a for statement."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		super().__init__(tokens[1], lexer(tokens[3:-1]).parse())
		self.active = 1
		self.branch = tokens[0].branch
		self.block = True

	def start(
		self
		) -> tuple[ins, ...]: 
		
		adjacent = str(int(self.register) + 1) # Uses the register of the first enclosed statement
		if self.value.type:
			return (ins('.iterator', self.register, (self.nodes[0].register,)),
					ins('ELSE' if self.branch else 'START', line = self.line),
					ins('.next', adjacent, (self.register,)),
					ins('.unloop', '0', (adjacent, self.value.type)), # Equivalent to Python's StopIteration check
					ins('.bind', self.value.value, ('0', self.value.type), label = [self.value.value]),
					ins(self.value.type, self.value.value, (self.value.value,)))
		else:
			return (ins('.iterator', self.register, (self.nodes[0].register,)),
					ins('ELSE' if self.branch else 'START', line = self.line),
					ins('.next', adjacent, (self.register,)),
					ins('.unloop', self.value.value, (adjacent,)))

	def execute(self): return ins('LOOP'),

class assert_statement(statement):
	"""Defines an assertion."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:
		
		nodes, sequence, parens = [], [], 0
		for token in tokens[1:-1]: # Collects all expressions in head statement
			if token in node.parens.keys():
				parens = parens + 1
			elif token in node.parens.values():
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

	def start(
		self
		) -> tuple[ins, ...]:
		
		return ()

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('.branch', self.register),

class return_statement(statement):
	"""Defines a return statement."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:
		
		super().__init__(None, lexer(tokens[1:]).parse()) if len(tokens) > 1 else super().__init__(None)
		self.branch = tokens[0].branch

	def execute(
		self
		) -> tuple[ins, ...]: 
		
		routine = self
		while not isinstance(routine, coroutine):
			routine = routine.head
		type_name = routine.type
		if type_name and not isinstance(routine, module):
			return (ins(type_name, self.register, (self.nodes[0].register if self.nodes else self.register,)),
					ins('.return', '0', (self.nodes[0].register,) if self.nodes else ()))
		else:
			return ins('.return', '0', (self.nodes[0].register,) if self.nodes else ()),

class link_statement(statement):
	"""Defines a link."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		super().__init__(tokens[1::2]) # Allows multiple links
		self.branch = tokens[0].branch

	def __str__(self) -> str: return ('else ' if self.branch else '') + 'link_statement ' + str([item.value for item in self.nodes])

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return [ins('.link', item.value) for item in self.value]

class start_statement(statement):
	"""Defines an initial."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:
		
		super().__init__(tokens[2::2])

	def __str__(self) -> str: return 'start ' + str([item.value for item in self.value])

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return (ins('.return', '0'),
				ins('END'),
				ins('EVENT', label = [self.head.message.value]),
				ins(self.head.message.type, self.head.message.value, (self.head.message.value,)))

class else_statement(statement):
	"""Defines an else statement."""
	def __init__(
		self,
		tokens: list[node]
		) -> None:

		super().__init__(None)
		self.branch = True
		self.block = True

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ()
