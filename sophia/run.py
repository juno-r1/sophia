from sophia.runtime import runtime

if __name__ == '__main__':
	
	main = runtime('main.sph', 'task', 'instructions', 'supervisor')
	print(main.run())