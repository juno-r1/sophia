import re

from .datatypes import mathos
from .internal import expressions, presets, statements
from .internal.instructions import instruction
from .internal.nodes import node, lexer

class parser:
	"""
	Module parser for Sophia.
	Generates an AST, then a list of instructions from a .sph file.
	"""
	def __init__(
		self,
		name: str,
		offset: int = 0
		) -> None:
		
		self.node = statements.module(name)
		self.path = [0]
		self.constant = offset # Constant register counter
		self.instructions = [instruction('START', label = [name])]
		self.values = {'0': None, '&0': None} # Register namespace

	def parse(
		self,
		source: str
		) -> tuple[statements.module, list[instruction], dict]:

		if not (source and parser.balanced(source)):
			raise SystemExit # End immediately
		tokens = self.tokenise(source)
		ast = self.link(tokens)
		instructions, namespace = self.generate()
		return ast, instructions, namespace

	def tokenise(
		self,
		source: str
		) -> list[list[node]] | None:
		"""
		Regex tokenises the source, returning logical lines of tokens.
		Functions as an LL(1) parser, since the current and last symbols
		provide sufficient context to deterministically tokenise any valid
		Sophia program.
		"""
		line, column, scope = 1, 1, 1
		tokens = [[]]
		last = None
		comment, trail = False, False
		for symbol in re.finditer(presets.TOKENS_PATTERN, source):
			value = symbol.group()
			column = column + len(value)
			if trail: # Skip whitespace after trailing line
				if re.match(r'\s', value):
					continue
				else:
					trail = False
			match symbol.lastgroup:
				case 'space':
					continue
				case 'comment':
					comment = True
					continue
				case 'indent':
					scope = scope + 1
					continue
				case 'newline' if last and re.match(presets.TRAILING, str(last.value)):
					trail = True
					column = 1
					continue
				case 'newline': # Logical line end
					last = None
					comment = False
					line, column, scope = line + 1, 1, 1
					if tokens[-1]:
						tokens.append([])
					continue
				case 'number':
					token = expressions.literal(mathos.real.read(value))
				case 'string':
					token = expressions.literal(bytes(value[1:-1], 'utf-8').decode('unicode_escape'))
				case 'literal' if value in presets.KEYWORDS_INFIX:
					token = expressions.infix(value)
				case 'literal' if value in presets.KEYWORDS_PREFIX:
					token = expressions.prefix(value)
				case 'literal' if value in presets.CONSTANTS:
					token = expressions.literal(value)
				case 'literal' if value in ('if', 'else') and last and last.value != 'else':
					token = expressions.left_conditional(value) if value == 'if' else expressions.right_conditional(value)
				case 'literal' if value in presets.KEYWORDS_STRUCTURE or value in presets.KEYWORDS_CONTROL:
					token = expressions.keyword(value)
					if last and last.value == 'else':
						tokens[-1].pop()
						token.branch = True
				case 'literal':
					if last and isinstance(last, expressions.name): # Checks for type
						typename = tokens[-1].pop().value # Sets type of identifier
						typename = presets.ALIASES[typename] if typename in presets.ALIASES else typename # Expands name of type
					else:
						typename = None
					token = expressions.name(value, typename)
				case 'l_parens' if value == '(':
					token = expressions.function_call(value) if last and isinstance(last, expressions.name) else expressions.parenthesis(value)
				case 'l_parens' if value == '[':
					token = expressions.sequence_index(value) if last and isinstance(last, expressions.name) else expressions.sequence_literal(value)
				case 'l_parens' if value == '{':
					token = expressions.meta_statement(value)
				case 'r_parens':
					token = expressions.right_bracket(value)
				case 'operator' if value in '\'\"': # Unclosed quote
					return hemera.error('sophia', line, 'UQTE', ())
				case 'operator' if value in (':', ','): # Same regardless of context
					token = expressions.concatenator(value)
				case 'operator' if not last or \
								   re.fullmatch(presets.TOKENS['operator'], str(last.value)) and \
								   not re.fullmatch(presets.TOKENS['r_parens'], str(last.value)): # Prefixes
					if value == '>':
						token = expressions.receive(value)
					elif value == '*':
						token = expressions.resolve(value)
					else:
						token = expressions.prefix(value) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
				case 'operator' if value in ('^', '->', '=>'): # Infixes
					token = expressions.infix_r(value)
				case 'operator' if value == '<-':
					bind_name = tokens.pop()
					token = expressions.bind(bind_name.value)
					token.type = bind_name.type
				case 'operator':
					token = expressions.infix(value)
				case _:
					raise SystemExit('Oh no!') # Unserious default case
				#case 'operator' if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and ('=>' in line or line[-1] == ':'): # Special case for operator definition
				#	pass
				#	token = nodes.name(value)
				#if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and ('=>' in line or line[-1] == ':'): # Special case for operator definition
				#	token = name(symbol)
				#	token_type = tokens[-1].pop().value # Sets return type of operator
				#	token.type = sub_types[token_type] if token_type in sub_types else token_type
			if not comment:
				token.line, token.column = line, column
				token.scope = scope
				tokens[-1].append(token)
				last = token
		return tokens

	def link(
		self,
		tokens: list[list[node]]
		) -> statements.module:
		"""
		Recursively descends into madness and links logical lines to
		create an AST from tokens.
		"""
		lines = []
		for line in tokens: # Tokenises whole lines
			if line[0].value in presets.KEYWORDS_STRUCTURE:
				token = statements.__dict__[line[0].value + '_statement'](line) # Cheeky little hack that makes a node for whatever structure keyword is specified
			elif line[0].value in presets.KEYWORDS_CONTROL:
				token = line[0] # Keywords will get special handling later
			elif line[-1].value == ':' or '=>' in [token.value for token in line]:
				if line[0].type == 'type' and '(' not in [token.value for token in line[:line.index('=>') if '=>' in line else -1]]:
					token = statements.type_statement(line)
				elif line[1].value == 'awaits':
					token = statements.event_statement(line)
				else:
					token = statements.function_statement(line)
			elif len(line) > 1 and line[1].value == ':':
				token = statements.assignment(line)
			elif len(line) > 1 and line[1].value == 'is':
				token = statements.alias(line)
			else: # Tokenises expressions
				token = lexer(line).parse() # Passes control to a lexer object that returns an expression tree when parse() is called
			token.line = line[0].line
			token.scope = line[0].scope
			lines.append(token)
		head, last = self.node, self.node # Head token and last line
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
					head = self.node # Resets head to main node
			head.nodes.append(line) # Link nodes
			last = line
		return self.node

	def generate(
		self,
		offset: int = 0
		) -> tuple[list[instruction], dict]:
		
		self.node.length = len(self.node.nodes)
		if not self.node.nodes:
			self.instructions.extend(self.node.execute())
		while self.node: # Pre-runtime generation of instructions
			if self.path[-1] == self.node.length: # Walk up
				if isinstance(self.node.head, statements.assert_statement) and self.path[-2] < self.node.head.active: # Insert assertion
					self.instructions.append(
						instruction(
							'.assert',
							'0',
							(self.node.register,),
							line = self.node.line
						)
					)
				elif isinstance(self.node.head, statements.type_statement) and self.path[-2] >= self.node.head.active: # Insert constraint
					self.instructions.append(
						instruction(
							'.constraint',
							'0',
							(self.node.register,),
							line = self.node.line,
							label = [self.node.head.value[0].value] if self.path[-2] == self.node.head.length - 1 else []
						)
					)
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
				if not isinstance(self.node, statements.for_statement):
					if self.node.branch:
						self.instructions.append(instruction('ELSE', line = self.node.line))
					elif self.node.block:
						self.instructions.append(instruction('START', line = self.node.line))
				if isinstance(self.node, statements.event_statement):
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
				self.instructions.append(instruction('END', line = self.node.line))
		self.instructions.append(instruction('END'))
		return self.instructions, self.values

	def register(
		self,
		offset: int
		) -> str:
		
		if self.node.nodes: # Temporary register
			if isinstance(self.node.head, statements.assert_statement):
				return '0' # 0 is the return register and is assumed to be nullable
			elif isinstance(self.node.head, expressions.bind):
				return self.node.head.value # Sure, I guess
			else:
				index = str(sum(self.path) + offset + 1) # Sum of path is a pretty good way to minimise registers
				self.values[index] = None
				return index
		else:
			if isinstance(self.node, expressions.name): # Variable register
				return self.node.value
			elif isinstance(self.node, expressions.receive):
				return self.node.value.value
			elif self.node.value is None: # Null value is interned so that instructions can reliably take null as an operand
				return '&0'
			else: # Constant register
				self.constant = self.constant + 1
				index = '&' + str(self.constant)
				self.values[index] = () if isinstance(self.node, expressions.sequence_literal) else self.node.value
				return index

	@classmethod
	def balanced(
		cls,
		tokens: str
		) -> bool:
		"""
		Takes a string and checks if its parentheses are balanced.
		https://stackoverflow.com/questions/6701853/parentheses-pairing-issue
		"""
		opening, closing = presets.PARENS.keys(), presets.PARENS.values() # Gets all opening parentheses from string
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
				if not stack or token != presets.PARENS[stack.pop()]: # If the stack is empty or c doesn't match the item popped off the stack:
					hemera.error('sophia', 0, 'UPRN', ())
					return False # Parentheses are unbalanced
		else:
			if stack:
				hemera.error('sophia', 0, 'UPRN', ())
			return not stack # Interprets stack as a boolean, where an empty stack is falsy