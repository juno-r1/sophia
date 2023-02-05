import sophia

if __name__ == '__main__':

	runtime = sophia.runtime('test.sophia', 'debug_task')
	print(runtime.run())