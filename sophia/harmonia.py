'''
The Harmonia test suite is a tool intended for developers of Sophia implementations.
The test suite is used to validate the implementation of the language specification.
Users can use this tool to verify the integrity of their installation.
'''

import sophia, os
from fractions import Fraction as real

if __name__ == '__main__':

	target = { # Target return value of each test
		0: None,
		1: None,
		2: True,
		3: (1, (real('1.1'),), ('1.1', True), (), {'e': (False,)}, {'f': 'f', 'g': 'g'}),
		4: (1, 0),
		5: (1, -1, 3, -1, 6, real('2/3'), real('8'), real('1')),
		6: (True, True, True, True, True, True),
		7: (True, True, True, True),
		8: ((1, 2, 3, 3, 4, 5), (3,), True),
		9: (4, True),
	   10: True,
	   11: True,
	   12: True,
	   13: True,
	   14: True,
	   15: True,
	   16: True,
	   17: True,
	   18: True,
	   19: True,
	   20: True,
	   21: True,
	   22: True
	}
	
	print('', 'Pass', 'Fail', sep = '\t')
	successes, failures = 0, 0
	for i, path in enumerate(os.listdir('harmonia')):
		runtime = sophia.runtime(path, root = 'harmonia')
		result = runtime.run()
		result = True if result == target[i] else False
		if result:
			successes = successes + 1
		else:
			failures = failures + 1
		print(i, 'x' if result else '', '' if result else 'x', sep = '\t')
	else:
		print('',
			  '{0} / {1} successes'.format(successes, successes + failures),
			  'Implementation verified!\n' if not failures else '',
			  sep = '\n')