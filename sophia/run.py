from sophia.runtime import runtime

if __name__ == '__main__':
	
	main = runtime('main.sph', 'instructions', 'profile')
	print(main.debug())