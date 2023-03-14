import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sph', 'instructions', 'profile')
	print(runtime.run())