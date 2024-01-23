import re

from .hemera import handler
from .internal import expressions, presets, statements
from .internal.instructions import instruction
from .internal.nodes import node

class parser:
	"""
	Module parser for Sophia.
	Generates an AST, then a list of instructions from a .sph file.
	"""
	def __init__(
		self,
		handler: handler,
		name: str,
		offset: int = 0
		) -> None:
		
		self.head = statements.module(name)
		self.node = self.head
		self.path = [0]
		self.constant = offset # Constant register counter
		self.instructions = [instruction('START', label = [name])]
		self.values = {'0': None, '&0': None} # Register namespace
		self.handler = handler # Error handler

	def parse(
		self,
		source: str
		) -> tuple[list[instruction], dict]:
		
		if re.fullmatch(presets.REGEX_EMPTY, source):
			raise SystemExit # End immediately without error
		if not self.matched(source):
			self.handler.error('SNTX', 'unmatched parentheses')
		if not self.balanced(source):
			self.handler.error('SNTX', 'unmatched quotes')
		lines = self.split(source)
		tokens = self.tokenise(lines)
		ast = self.link(tokens)
		instructions, namespace = self.generate()
		if 'tree' in self.handler.flags:
			ast.debug() # Here's tree
		return instructions, namespace

	def split(
		self,
		source: str
		) -> list[str]:
		"""
		Uncomments and splits the source into logical lines.
		"""
		source = re.sub(presets.REGEX_COMMENT, '\n', source)
		source = re.sub(presets.REGEX_ALIAS, self.alias, source)
		line = ''
		lines = []
		for symbol in re.finditer(presets.REGEX_SPLIT, source):
			value = symbol.group()
			match symbol.lastgroup:
				case 'trailing': # Lookbehind seems to work just fine with re.finditer
					continue
				case 'final':
					lines.append(line)
					line = ''
				case 'line':
					line = line + value
				case _:
					self.handler.error('SNTX', value)
		return lines

	def tokenise(
		self,
		lines: list[str]
		) -> list[node] | None:
		"""
		Regex tokenises the source, returning logical lines of tokens.
		Functions as an LL(1) parser, since the current and last symbols
		provide sufficient context to deterministically tokenise any valid
		Sophia program.
		"""
		tokens = []
		scope, branch = 1, False
		for line in lines:
			for symbol in re.finditer(presets.REGEX_STATEMENT, line):
				value = symbol.group()
				match symbol.lastgroup:
					case 'sentinel':
						scope, branch = 1, False
						continue
					case 'space':
						continue
					case 'indent':
						scope = value.count('\t') + 1
						continue
					case 'else':
						branch = True
						token = statements.else_statement()
					case 'branch':
						branch = True
						continue
					case 'continue':
						token = expressions.keyword_continue(value)
					case 'break':
						token = expressions.keyword_break(value)
					case 'if':
						token = statements.if_statement(value)
					case 'while':
						token = statements.while_statement(value)
					case 'for':
						token = statements.for_statement(value)
					case 'return':
						token = statements.return_statement(value)
					case 'link':
						token = statements.link_statement(value)
					case 'start':
						token = statements.start_statement()
					case 'type':
						token = statements.type_statement(value)
					case 'event':
						token = statements.event_statement(value)
					case 'function':
						token = statements.function_statement(value)
					case 'assign':
						token = statements.assignment(value)
					case 'expression':
						token = expressions.lexer(value).parse()
					case _:
						self.handler.error('SNTX', value)
				token.scope = scope
				token.branch = branch
				tokens.append(token)
		return tokens

	def link(
		self,
		lines: list[node]
		) -> statements.module:
		"""
		Links logical lines to create an AST.
		"""
		head, last = self.head, self.head # Head token and last line
		for i, line in enumerate(lines): # Group lines based on scope
			if line.scope > head.scope + 1: # If entering scope
				head = last # Last line becomes the head node
			elif line.scope < head.scope + 1: # If exiting scope
				if line.scope > 1: # If statement is in local scope:
					for n in lines[i::-1]: # Find the last line containing the current line in its direct scope, searching backwards from the current line
						if n.scope == line.scope - 1: # If such a line is found:
							head = n # Make it the head node
							break
				else: # If statement is in global scope:
					head = self.head # Resets head to main node
			head.nodes.append(line) # Link nodes
			last = line
		return self.head

	def generate(
		self,
		offset: int = 0
		) -> tuple[list[instruction], dict]:
		
		self.head.length = len(self.head.nodes)
		while self.node: # Pre-runtime generation of instructions
			if self.path[-1] == self.node.length: # Walk up
				if isinstance(self.node.head, statements.type_statement) and self.path[-2] >= self.node.head.active: # Insert constraints
					self.instructions.append(instruction('.constraint', '0', (self.node.register,)))
				self.node = self.node.head # Walk upward
				if self.node:
					self.path.pop()
					self.path[-1] = self.path[-1] + 1
				else:
					continue
			else: # Walk down
				child = self.node.nodes[self.path[-1]]
				child.head = self.node # Set head
				self.node = child # Set value to child node
				self.node.register = self.register(offset)
				self.node.length = len(self.node.nodes)
				self.path.append(0)
				if not isinstance(self.node, statements.for_statement):
					if self.node.branch:
						self.instructions.append(instruction('ELSE'))
					elif self.node.block:
						self.instructions.append(instruction('START'))
			if self.path[-1] == self.node.active:
				instructions = self.node.start()
			elif self.path[-1] == self.node.length:
				instructions = self.node.execute()
			else:
				instructions = ()
			#for x in instructions:
			#	x.line = self.node.line
			self.instructions.extend(instructions)
			if self.path[-1] == self.node.length and self.node.block:
				self.instructions.append(instruction('END'))
		self.instructions.append(instruction('END'))
		return self.instructions, self.values

	def register(
		self,
		offset: int
		) -> str:
		
		if isinstance(self.node, expressions.name): # Variable register
			return self.node.value
		elif isinstance(self.node, expressions.receive):
			return self.node.value.value
		elif isinstance(self.node, expressions.constant) and self.node.value is None: # Null value is interned so that instructions can reliably take null as an operand
			return '&0'
		elif isinstance(self.node, expressions.sequence_literal) and not self.node.nodes: # Empty list
			self.constant = self.constant + 1
			index = '&' + str(self.constant)
			self.values[index] = ()
			return index
		elif isinstance(self.node, expressions.literal): # Constant register
			self.constant = self.constant + 1
			index = '&' + str(self.constant)
			self.values[index] = self.node.value
			return index
		else: # Temporary register
			index = str(sum(self.path) + offset + 1) # Sum of path is a pretty good way to minimise registers
			self.values[index] = None
			return index
			
	def balanced(
		self,
		string: str
		) -> bool:
		"""
		Takes a string and checks if its parentheses are balanced.
		This check permits parentheses over newlines.
		https://stackoverflow.com/questions/6701853/parentheses-pairing-issue
		"""
		stack = []
		for symbol in re.finditer(presets.REGEX_BALANCED, string):
			value = symbol.group()
			match symbol.lastgroup:
				case 'string':
					continue
				case 'l_parens': # If character is an opening parenthesis:
					stack.append(value) # Add to stack
				case 'r_parens': # If character is a closing parenthesis:
					if not stack or value != presets.PARENS[stack.pop()]: # If the stack is empty or c doesn't match the item popped off the stack:
						return False # Parentheses are unbalanced
		return not stack # Interprets stack as a boolean, where an empty stack is falsy
		
	def matched(
		self,
		string: str
		) -> bool:
		"""
		Takes a string and checks if its quotes are matched.
		This check does not permit quotes over newlines.
		"""
		for symbol in re.finditer(presets.REGEX_MATCHED, string, flags = re.MULTILINE):
			match symbol.lastgroup:
				case 'string':
					continue
				case 'unmatched':
					return False
		return True

	def alias(
		self,
		symbol: re.Match
		) -> str:
		"""
		Replaces aliases with their canonical forms.
		"""
		value = symbol.group()
		match symbol.lastgroup:
			case 'string':
				return value
			case 'literal':
				return presets.ALIASES[value] if value in presets.ALIASES else value