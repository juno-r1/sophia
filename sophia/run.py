import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sph', 'tree', 'task', 'instructions')
	print(runtime.debug())