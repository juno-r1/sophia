from time import perf_counter_ns as count
from fractions import Fraction as real

x = count()

def fib(n):
	a, b = 0, 1
	for _ in range(n):
		a, b = b, a + b
	return a

a = fib(100)
y = count()
print(y - x, 'ns (Python)')