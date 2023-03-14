from fractions import Fraction
from rationals import Rational as real
from cProfile import Profile

def integer_fib(n):

	a, b = 0, 1
	for i in range(0, n, 1):
		a, b = a, a + b
	return a

def real_fib(n):

	a, b = real(0), real(1)
	for i in range(0, n, 1):
		a, b = a, a + b
	return a

def fraction_fib(n):

	a, b = Fraction(0), Fraction(1)
	for i in range(0, n, 1):
		a, b = a, a + b
	return a

n = 1000000

pr = Profile()
pr.enable()
integer_fib(n)
pr.disable()
pr.print_stats(sort = 'tottime')

pr = Profile()
pr.enable()
real_fib(n)
pr.disable()
pr.print_stats(sort = 'tottime')

pr = Profile()
pr.enable()
fraction_fib(n)
pr.disable()
pr.print_stats(sort = 'tottime')