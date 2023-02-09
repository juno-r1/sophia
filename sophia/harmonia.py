import sophia, os

target = { # Target return value of each test
	0000: None
}

if __name__ == '__main__':
	
	print('', 'pass', 'fail', sep = '\t')
	successes, failures = 0, 0
	for i, path in enumerate(os.listdir('harmonia')):
		runtime = sophia.runtime('harmonia\\{0}'.format(path), 'timeout')
		result = True if runtime.run() == target[i] else False
		if result:
			successes = successes + 1
		else:
			failures = failures + 1
		print(i,
			  'x' if result else '',
			  '' if result else 'x',
			  sep = '\t')
	else:
		print('',
			  '{0} / {1} successes'.format(successes, successes + failures),
			  'implementation verified!\n' if not failures else '',
			  sep = '\n')