import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('test.sophia', 'debug_tree')
	print(runtime.run())