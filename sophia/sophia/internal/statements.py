import re

from .expressions import lexer
from .nodes import node
from .instructions import instruction as ins

class statement(node):
	"""Base statement node."""
	def __str__(self) -> str: return ('else ' if self.branch else '') + type(self).__name__

class coroutine(statement):
	"""Base coroutine node."""
	def __init__(
		self,
		name: str,
		final: str,
		params: dict[str, str]
		) -> None:

		super().__init__()
		self.active = 0
		self.name = name
		self.final = final
		self.params = params

	def __str__(self) -> str: return str('{0} {1}()'.format(self.final, self.name))

class module(coroutine):
	"""Base module node. This is always the top node of an AST."""
	def __init__(
		self,
		name: str
		) -> None:

		super().__init__(name, 'any', {})
		self.active = -1
		self.name = name

	def __str__(self) -> str: return 'module ' + self.name

	def execute(self) -> tuple[ins, ...]:
		
		return ins('return', '0'), # Default end of module

class type_statement(coroutine):
	"""Defines a type definition."""
	def __init__(
		self, 
		string: str
		) -> None:

		# Regex
		string, expression = re.split(r'=>\s*', string, 1) if '=>' in string else (string[:-1], None)
		name = re.split(' ', re.search(r'type \w+', string).group(), 1)[1]
		supertype = re.split(' ', re.search(r'extends \w+', string).group(), 1)[1] if 'extends' in string else 'any'
		prototype = re.split(' ', re.search(r'with .+', string).group(), 1)[1] if 'with' in string else ''
		super().__init__(name, name, {name: supertype})
		if prototype:
			self.nodes.append(lexer(prototype).parse())
		if expression:
			self.nodes.append(lexer(expression).parse())
		self.active = int(bool(prototype))

	def start(
		self
		) -> tuple[ins, ...]:

		if self.active: # Necessary to check type of prototype
			return (ins(self.params[self.name], self.register, (self.nodes[0].register,)),
					ins('.type', self.name, (self.params[self.name], self.register)),
					ins('START', label = [self.name]))
		else:
			return (ins('.type', self.name, (self.params[self.name],)),
					ins('START', label = [self.name]))

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return (ins('return', '0', (self.name,)),
				ins('END', label = [self.name]))

class event_statement(coroutine):
	"""Defines an event definition."""
	def __init__(
		self,
		string: str
		) -> None:

		string, expression = re.split(r'=>\s*', string, 1) if '=>' in string else (string, None)
		name, string = re.split(r' awaits ', string, 1)
		final, name = re.split(r' ', name, 1) if ' ' in name else ('any', name)
		message, string = re.split(r'\s*\(', string, 1)
		check, message = re.split(r' ', message, 1) if ' ' in message else ('any', message)
		params = {name: final}
		for value in re.finditer(r'\w+( \w+)?', string):
			param = value.group()
			typename, param = re.split(r' ', param, 1) if ' ' in param else ('any', param)
			params[param] = typename
		params = params | {message: check}
		super().__init__(name, final, params)
		if expression:
			self.nodes = [return_statement('return ' + expression)]

	def start(
		self
		) -> tuple[ins, ...]:
		
		return (ins('.event', self.name, tuple(self.params.values()), label = list(self.params.keys())),
				ins('START', label = [self.name]))

	def execute(
		self
		) -> tuple[ins, ...]: 
		
		return (ins('return', '0'),
				ins('END'))

class function_statement(coroutine):
	"""Defines a function definition."""
	def __init__(
		self,
		string: str
		) -> None:
		
		string, expression = re.split(r'=>\s*', string, 1) if '=>' in string else (string, None)
		name, string = re.split(r'\s*\(', string, 1)
		final, name = re.split(r' ', name, 1) if ' ' in name else ('any', name)
		params = {name: final}
		for value in re.finditer(r'\w+( \w+)?', string):
			param = value.group()
			typename, param = re.split(r' ', param, 1) if ' ' in param else ('any', param)
			params[param] = typename
		super().__init__(name, final, params)
		if expression:
			self.nodes = [return_statement('return ' + expression)]

	def start(
		self
		) -> tuple[ins, ...]:
		
		return (ins('.function', self.name, tuple(self.params.values()), label = list(self.params.keys())),
				ins('START', label = [self.name]))

	def execute(
		self
		) -> tuple[ins, ...]: 
		
		return (ins('return', '0'),
				ins('END'))

class assignment(statement):
	"""Defines an assignment. Supports multiple assignment."""
	def __init__(
		self,
		string: str
		) -> None:
		
		binds, expressions = {}, []
		while string:
			name, string = re.split(r':\s*', string, 1)
			typename, name = re.split(r' ', name, 1) if ' ' in name else ('?', name)
			binds[name] = typename
			if ';' in string:
				expression, string = re.split(r';\s*', string, 1)
			else:
				expression, string = string, ''
			expressions.append(lexer(expression).parse())
		super().__init__(*expressions)
		self.binds = binds

	def __str__(self) -> str: return 'assignment ' + ' '.join(('{0} {1}'.format(typename, name) for name, typename in self.binds.items()))

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return [ins('BIND')] + \
			   [ins('.check',
				str(int(self.register) + i),
				(self.nodes[i].register, typename))
				for i, typename in enumerate(self.binds.values())] + \
			   [ins('.bind', '0', label = list(self.binds.keys()))]

class if_statement(statement):
	"""Defines an if statement."""
	def __init__(
		self,
		string: str
		) -> None:

		expression = re.split(r' ', string, 1)[1][:-1] # Strip colon
		super().__init__(lexer(expression).parse())
		self.active = 1
		self.block = True

	def start(
		self
		) -> tuple[ins, ...]:
		
		return ins('if', self.register, (self.nodes[0].register,)),

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('if', self.register),

class while_statement(statement):
	"""Defines a while statement."""
	def __init__(
		self,
		string: str
		) -> None:

		expression = re.split(r' ', string, 1)[1][:-1] # Strip colon
		super().__init__(lexer(expression).parse())
		self.active = 1
		self.block = True

	def start(
		self
		) -> tuple[ins, ...]:
		
		return ins('if', self.register, (self.nodes[0].register,)),

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('.loop', '0'),

class for_statement(statement):
	"""Defines a for statement."""
	def __init__(
		self,
		string: str
		) -> None:

		string = re.split(r' ', string, 1)[1][:-1] # Strip colon
		index, iterator = re.split(r' in ', string, 1)
		typename, index = re.split(r' ', index, 1) if ' ' in index else ('?', index)
		super().__init__(lexer(iterator).parse())
		self.active = 1
		self.index = index
		self.typename = typename

	def start(
		self
		) -> tuple[ins, ...]: 
		
		return (ins('.iterator', self.register, (self.nodes[0].register,)),
				ins('ELSE' if self.branch else 'START'),
				ins('.next', '0', (self.register,)),
				ins('BIND'),
				ins('.check', '0', ('0', self.typename)),
				ins('.bind', '0', label = [self.index]))

	def execute(self): return ins('.loop', '0'), ins('END')

class return_statement(statement):
	"""Defines a return statement."""
	def __init__(
		self,
		string: str
		) -> None:
		
		if ' ' in string:
			expression = re.split(r' ', string, 1)[1]
			super().__init__(lexer(expression).parse())
		else:
			super().__init__()

	def execute(
		self
		) -> tuple[ins, ...]: 
		
		routine = self
		while not isinstance(routine, coroutine):
			routine = routine.head
		return (ins('.check', self.register, (self.nodes[0].register if self.nodes else self.register, routine.final)),
				ins('return', '0', (self.register,) if self.nodes else ()))

class link_statement(statement):
	"""Defines a link."""
	def __init__(
		self,
		string: str
		) -> None:
		
		super().__init__()
		string = re.split(r' ', string, 1)[1]
		self.links = re.split(r',\s*', string)

	def __str__(self) -> str: return ('else ' if self.branch else '') + 'link_statement ' + ' '.join(self.links)

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ins('.link', '0', tuple(self.links)),

class start_statement(statement):
	"""Defines an initial."""
	def __str__(self) -> str: return 'start'

	def execute(
		self
		) -> tuple[ins, ...]:

		message, check = list(self.head.params.items())[-1]
		return (ins('return', '0'),
				ins('END'),
				ins('EVENT', label = [message]),
				ins('BIND'),
				ins('.check', message, (message, check)),
				ins('.bind', '0', label = [message]))

class else_statement(statement):
	"""Defines an else statement."""
	def __init__(
		self
		) -> None:

		super().__init__()
		self.block = True

	def execute(
		self
		) -> tuple[ins, ...]:
		
		return ()