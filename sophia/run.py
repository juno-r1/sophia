import sophia

if __name__ == '__main__':
	
	runtime = sophia.runtime('main.sph', 'profile')
	print(runtime.run())