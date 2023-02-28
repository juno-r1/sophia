import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sophia', 'instructions', 'task')
	print(runtime.run())