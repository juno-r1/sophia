def fib(n):

	a, b = 0, 1
	for i in range(n):
		a, b = b, a + b
	return a

from cProfile import Profile
pr = Profile()
pr.enable()
fib(100000)
pr.disable()
pr.print_stats(sort = 'tottime')