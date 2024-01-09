ALIASES = {
	'bool': 'boolean',
	'int': 'integer',
	'num': 'number',
	'str': 'string'
}
COMMENT = r'(?P<comment>\s*//.*?(\n|$))'
CONSTANTS = {
	'true': True,
	'false': False,
	'null': None
}
DATATYPES = { # Base data types
	'NoneType': 'none',
	'typedef': 'type',
	'eventdef': 'event',
	'funcdef': 'function',
	'bool': 'boolean',
	'real': 'number',
	'str': 'string',
	'tuple': 'list',
	'dict': 'record',
	'slice': 'slice',
	'reference': 'future'
}
EMPTY = r'((\s*\n?)|(\s*//.*\n?))*' # Matches any empty source file
ERRORS = {
	'BIND': 'Bind to reserved name: {0}',
	#'CAST': 'Failed cast to {0}: {1}',
	#'COMP': 'Failed composition: {0} does not map onto {1}',
	'DISP': 'Failed dispatch: {0} has no signature {1}',
	#'EVNT': 'Event has no initial',
	'FIND': 'Undefined name: {0}',
	'FLAG': 'Invalid flag: {0}',
	#'FLTR': 'Failed filter: {0} does not return boolean for {1}',
	'INDX': 'Invalid index: {0}',
	'LOCK': 'Runtime encountered an error during program execution',
	#'PROT': 'Type {0} has no prototype',
	#'RDCE': 'Failed reduce: empty list',
	#'READ': 'Stream not readable',
	'SNTX': 'Syntax error: {0}',
	#'TASK': 'Task expired',
	'TYPE': 'Invalid value for type {0}: {1}',
	'UPRN': 'Unmatched parentheses',
	'UQTE': 'Unmatched quotes',
	'USER': '{0}',
	#'WRIT': 'Stream not writeable'
}
FLAGS = (
	'debug',
	'instructions',
	'namespace',
	'processor',
	'profile',
	'supervisor',
	'suppress',
	'task',
	'tree'
)
INFIX_R = [
	'^',
	'->',
	'=>'
]
KEYWORDS_INFIX = (
	'and',
	'or',
	'xor',
	'in',
)
KEYWORDS_PREFIX = (
	'not',
	'new'
)
PARENS = {
	'(': ')',
	'[': ']',
	'{': '}'
}
PROPERTIES = (
	'element',
	'length'
)
STDLIB_NAMES = {
	# Streams
	'stdin': 'stdin',
	'stdout': 'stdout',
	'stderr': 'stderr',
	# Types
	'any': 'any',
	'none': 'none',
	'some': 'some',
	'routine': 'routine',
	'type': 'type',
	'event': 'event',
	'function': 'function',
	'boolean': 'boolean',
	'number': 'number',
	'integer': 'integer',
	'sequence': 'sequence',
	'string': 'string',
	'list': 'list',
	'record': 'record',
	'slice': 'slice',
	'future': 'future',
	# Operators
	'add': '+',
	'sub': '-',
	'mul': '*',
	'div': '/',
	'exp': '^',
	'mod': '%',
	'eql': '=',
	'neq': '!=',
	'ltn': '<',
	'gtn': '>',
	'leq': '<=',
	'geq': '>=',
	'sbs': 'in',
	'lnt': 'not',
	'lnd': 'and',
	'lor': 'or',
	'lxr': 'xor',
	'ins': '&',
	'uni': '|',
	'idx': '[',
	'sfe': '?',
	'usf': '!',
	'snd': '->',
	'new': 'new',
	'cmp': '.',
	# Built-ins
	'abs': 'abs',
	'cast': 'cast',
	'ceiling': 'ceiling',
	'dispatch': 'dispatch',
	'error': 'error',
	'floor': 'floor',
	'filter': 'filter',
	'format': 'format',
	'hash': 'hash',
	'if': 'if',
	'input': 'input',
	'join': 'join',
	'length': 'length',
	'map': 'map',
	'namespace': 'namespace',
	'print': 'print',
	'reduce': 'reduce',
	'return': 'return',
	'reverse': 'reverse',
	'round': 'round',
	'sign': 'sign',
	'signature': 'signature',
	'split': 'split',
	'sum': 'sum',
	'typeof': 'typeof'
}
STDLIB_PREFIX = 'std_'
"""
Regex line patterns.
"""
REGEX_UNMATCHED = r'(?P<unmatched>(\'[^\']*?)|(\"[^\"]*?))' # Detects unmatched quotes
REGEX_TRAILING = r'(?P<trailing>(?<=[,;\(\[\{])\n\s*)'
REGEX_FINAL = r'(?P<final>\n|$)'
REGEX_LINE = r'(?P<line>.+(?=\n|$))'
REGEX_SENTINEL = r'(?P<sentinel>$)'
"""
Regex statement patterns.
"""
REGEX_SPACE = r'(?P<space> +)'
REGEX_INDENT = r'(?P<indent>\t+)'
REGEX_ELSE = r'(?P<else>else:$)'
REGEX_BRANCH = r'(?P<branch>else )'
REGEX_CONTINUE = r'(?P<continue>continue$)'
REGEX_BREAK = r'(?P<break>break$)'
REGEX_IF = r'(?P<if>if .+:$)'
REGEX_WHILE = r'(?P<while>while .+:$)'
REGEX_FOR = r'(?P<for>for \w+( \w+)? in .+:$)'
REGEX_RETURN = r'(?P<return>return( .+)?$)'
REGEX_LINK = r'(?P<link>link (\w+(,\s*|$))+)'
REGEX_START = r'(?P<start>start:$)'
REGEX_TYPE = r'(?P<type>type \w+( extends \w+)?( with .*)?((:$)|(\s*=>\s*.+)))'
REGEX_EVENT = r'(?P<event>.+( .+)? awaits \w+( \w+)?\s*\((\w+( \w+)?(,\s*)?)*\)((:$)|(\s*=>\s*.+)))'
REGEX_FUNCTION = r'(?P<function>.+( .+)?\s*\((\w+( \w+)?(,\s*)?)*\)((:$)|(\s*=>\s*.+)))'
REGEX_ASSIGN = r'(?P<assign>(\w+( \w+)?:\s*.+((;\s*)|$))+$)'
REGEX_EXPRESSION = r'(?P<expression>.+)'
"""
Regex expression patterns.
"""
REGEX_NUMBER = r'(?P<number>\d+(\.\d*)?)' # Any number of the format x(.y)
REGEX_STRING = r'(?P<string>(\'.*?\')|(\".*?\"))' # Any symbols between single or double quotes
REGEX_LITERAL = r'(?P<literal>\w+)' # Any word
REGEX_L_PARENS = r'(?P<l_parens>[\(\[\{])'
REGEX_R_PARENS = r'(?P<r_parens>[\)\]\}])'
REGEX_OPERATOR = r'(?P<operator>[^(\s\d\w\(\[\{)]+)' # Any other symbol
"""
Regex combinations.
"""
REGEX_MATCHED = '|'.join((REGEX_STRING, REGEX_UNMATCHED))
REGEX_BALANCED = '|'.join((REGEX_STRING, REGEX_L_PARENS, REGEX_R_PARENS))
REGEX_SPLIT = '|'.join((REGEX_TRAILING, REGEX_FINAL, REGEX_LINE))
REGEX_STATEMENT = '|'.join((
	REGEX_SENTINEL,
	REGEX_SPACE,
	REGEX_INDENT,
	REGEX_ELSE,
	REGEX_BRANCH,
	REGEX_CONTINUE,
	REGEX_BREAK,
	REGEX_IF,
	REGEX_WHILE,
	REGEX_FOR,
	REGEX_RETURN,
	REGEX_LINK,
	REGEX_START,
	REGEX_TYPE,
	REGEX_EVENT,
	REGEX_FUNCTION,
	REGEX_ASSIGN,
	REGEX_EXPRESSION
))
REGEX_LEXER = '|'.join((
	REGEX_SENTINEL,
	REGEX_NUMBER,
	REGEX_STRING,
	REGEX_LITERAL,
	REGEX_L_PARENS,
	REGEX_R_PARENS,
	REGEX_OPERATOR
))
REGEX_NAMESPACE = '|'.join((REGEX_LITERAL, REGEX_OPERATOR)) # Valid namespace symbols