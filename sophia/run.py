import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sph', 'task', 'instructions', 'namespace')
	print(runtime.run())