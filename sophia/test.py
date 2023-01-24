import cProfile

pr = cProfile.Profile()
pr.enable()

def fib(n):

	a, b = 0, 1
	for _ in range(n):
		a, b = b, a + b	
	return a

fib(1000000)
pr.disable()
pr.print_stats(sort='tottime') # sort as you wish