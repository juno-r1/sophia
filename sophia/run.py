import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sophia', 'debug_task')
	print(runtime.run())