characters = '.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz' # Sorted by position in UTF-8
parens = '()[]{}'
comment = '//'
structure_tokens = ('if', 'while', 'for', 'else', 'assert', 'constraint', 'return', 'link')
keyword_tokens = ('is', 'extends', 'continue', 'break')
keyword_operators = ('not', 'or', 'and', 'xor', 'in')
trailing = (';', ',')
sub_types = {'int': 'integer', # Lookup table for type names
			 'bool': 'boolean',
			 'str': 'string',
			 'num': 'number'}
sub_values = {'true': True, # Lookup table for special values
			  'false': False,
			  'null': None}
binding_power = (('(', ')', '[', ']', '{', '}'), # The left-binding power of a binary operator is expressed by its position in this tuple of tuples
				 (',',),
				 (':',),
				 ('->',),
				 ('if',),
				 ('else',),
				 ('or', '||',),
				 ('and', '&&',),
				 ('xor', '^^'),
				 ('=', '!=', 'in'),
				 ('<', '>', '<=', '>='),
				 ('&', '|'),
				 ('+', '-'),
				 ('*', '/', '%'),
				 ('^',))

class lexer: # Lex object to get around not being able to peek the next value of an iterator

	def __init__(self, tokens):

		self.lexes = (iter(tokens), iter(tokens))
		self.token = None
		self.peek = next(self.lexes[1])

	def use(self): # Gets the next tokens

		self.token = next(self.lexes[0])
		try:
			self.peek = next(self.lexes[1])
		except StopIteration:
			self.peek = eol()

	def parse(self, lbp = 0): # Pratt parser for expressions - takes a lex construct and the left-binding power

		self.use()
		if isinstance(self.peek, eol): # Detects end of expression
			return self.token # End-of-line token
		left = self.token.nud(self) # Executes null denotation of current token
		while lbp < self.peek.lbp:
			self.use()
			left = self.token.led(self, left) # Executes left denotation of current token
			if isinstance(self.peek, eol): # Detects end of expression
				return left # Returns expression tree
		else:
			return left # Preserves state of next_token for higher-level calls

	# https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
	# https://abarker.github.io/typped/pratt_parsing_intro.html
	# https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
	# https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

class eol: # Sentinel object

	def __init__(self): self.lbp = -1

def group(lines): # Groups lines with trailing characters

	if not lines:
		return []
	grouped = [lines[0]]
	for line in lines[1:]:
		if grouped[-1] and grouped[-1][-1] in trailing:
			i = 0
			while line[i] in ('\t', ' '):
				i = i + 1
			grouped[-1] = grouped[-1] + '\r' +  line[i:]
		else:
			grouped.append(line)
	return grouped

def split(line): # Takes a line from the file data and splits it into tokens
	
	tokens = []
	if not balanced(line):
		return 'UPRN'
	while line:
		shift = False # Push flag
		symbol = ''
		while not shift: # Constructs token
			symbol, line = symbol + line[0], line[1:]
			if symbol == comment: # Comments
				return tokens # Comment ends line
			elif symbol[-1] == ' ':
				symbol = symbol[:-1]
				if symbol:
					shift = True
				else:
					break
			elif symbol in ('\t', '\n', ':', ';', ',') or symbol in parens:
				shift = True
			elif symbol in '\'\"': # Strings
				try:
					end = line.index(symbol) + 1 # Everything before this index is inside a string
					symbol, line = symbol + line[0:end], line[end:]
					shift = True
				except ValueError:
					return 'UQTE'
			elif not line or (symbol[-1] in characters) != (line[0] in characters): # XOR for last and next character being part of an operator
				shift = True
		else:
			tokens.append(symbol)
	return tokens

def balanced(tokens): # Takes a string and checks if its parentheses are balanced
	
	opening = parens[0::2] # Gets all opening parentheses from string
	closing = parens[1::2] # Gets all closing parentheses from string
	string = ''
	stack = [] # Guess

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
			if not stack or token != closing[opening.index(stack.pop())]: # If the stack is empty or c doesn't match the item popped off the stack:
				return False # Parentheses are unbalanced
	else:	
		return not stack # Interprets stack as a boolean, where an empty stack is falsy

	# https://stackoverflow.com/questions/6701853/parentheses-pairing-issue

def bp(symbol):

	for i, level in enumerate(binding_power):
		if symbol in level:
			return i + 1
	else:
		return len(binding_power) # Default binding power; 1 less than unary operators