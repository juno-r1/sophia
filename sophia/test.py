#from random import randint

#for i in range(20):
#	print((randint(1, 5), randint(1, 5), randint(1, 5)))

from mathos import real

a, b = real(1), real(2)
c = real.__add__(a, b)
print(c)