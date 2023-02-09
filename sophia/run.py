import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sophia', 'debug_tree')
	print(runtime.run())