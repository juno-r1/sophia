ALIASES = {
	'bool': 'boolean',
	'int': 'integer',
	'num': 'number',
	'str': 'string'
}
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
ERRORS = {
	#'BIND': 'Bind to reserved name: {0}',
	#'CAST': 'Failed cast to {0}: {1}',
	#'COMP': 'Failed composition: {0} does not map onto {1}',
	#'DISP': 'Failed dispatch: {0} has no signature {1}',
	#'EVNT': 'Event has no initial',
	#'FIND': 'Undefined name: {0}',
	#'FLTR': 'Failed filter: {0} does not return boolean for {1}',
	#'INDX': 'Invalid index: {0}',
	#'PROT': 'Type {0} has no prototype',
	#'RDCE': 'Failed reduce: empty list',
	#'READ': 'Stream not readable',
	#'TASK': 'Task expired',
	#'TIME': 'Timeout warning' '\n' 'Enter Ctrl+C to interrupt program',
	#'UPRN': 'Unmatched parentheses',
	#'UQTE': 'Unmatched quotes',
	#'USER': '{0}',
	#'WRIT': 'Stream not writeable'
}
KEYWORDS_CONTROL = (
	'continue',
	'break',
	'is',
	'with',
	'extends',
	'awaits'
)
KEYWORDS_INFIX = (
	'or',
	'and',
	'xor',
	'in',
)
KEYWORDS_PREFIX = (
	'not',
	'new'
)
KEYWORDS_STRUCTURE = (
	'if',
	'while',
	'for',
	'else',
	'assert',
	'return',
	'link',
	'start'
)
PARENS = {
	'(': ')',
	'[': ']',
	'{': '}'
}
STDLIB_NAMES = {
	# Interns
	'assert': '.assert',
	'branch': '.branch',
	'constraint': '.constraint',
	'event': '.event',
	'function': '.function',
	'index': '.index',
	'iterator': '.iterator',
	'link': '.link',
	'meta': '.meta',
	'next': '.next',
	'range': '.range',
	'return': '.return',
	'skip': '.skip',
	'type': '.type',
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
	'slc': ':',
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
	'input': 'input',
	'join': 'join',
	'length': 'length',
	'map': 'map',
	'namespace': 'namespace',
	'print': 'print',
	'reduce': 'reduce',
	'reverse': 'reverse',
	'round': 'round',
	'sign': 'sign',
	'signature': 'signature',
	'split': 'split',
	'sum': 'sum',
	'typeof': 'typeof'
}
STDLIB_PREFIX = 'std_'
TOKENS = {
	'space':	r'(?P<space> )',
	'comment':	r'(?P<comment>//)',
	'indent':	r'(?P<indent>\t)',
	'newline':	r'(?P<newline>\n)',
	'number':	r'(?P<number>\d+(\.\d*)?)', # Any number of the format x(.y)
	'string':	r'(?P<string>(\'.*?\')|(\".*?\"))', # Any symbols between single or double quotes
	'literal':	r'(?P<literal>\w+)', # Any word
	'l_parens':	r'(?P<l_parens>[\(\[\{])',
	'r_parens':	r'(?P<r_parens>[\)\]\}])',
	'operator':	r'(?P<operator>[^(\s\d\w\.\(\[\{)]+)' # Any other symbol
}
TOKENS_NAMESPACE = '|'.join((TOKENS['literal'], TOKENS['operator']))
TOKENS_PATTERN = '|'.join(TOKENS.values())
TRAILING = r'[;,\'\"\(\[\{]'