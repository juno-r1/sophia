from time import perf_counter_ns as count

x = count()

#def fib(n):

a, b = 0, 1
for _ in range(1000):
	a, b = b, a + b
#	return a

#a = fib(100)
y = count()
print(a)
print(y - x, 'ns (Python)')