import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sph', 'instructions', 'namespace', 'tree')
	print(runtime.run())