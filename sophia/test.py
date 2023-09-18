from time import perf_counter

x = perf_counter()
a, b = 0, 1
for i in range(10000):
	a, b = b, a + b
y = perf_counter()
print(a)
print(y - x)