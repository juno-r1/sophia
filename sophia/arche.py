from time import perf_counter_ns
from sys import stderr

class element(tuple): pass # Stupid hack to make record construction work

class iterable: # Loop index

	def __init__(self, value):

		self.value = iter(value)

	def __next__(self):

		return next(self.value)

class slice: # Slice object

	def __init__(self, sequence):
		
		self.indices = sequence.copy() # Stores indices for reversal
		sequence[1] = sequence[1] + 1 if sequence[2] >= 0 else sequence[1] - 1 # Correction for inclusive range
		self.value = range(*sequence) # Stores slice iterator

	def __getitem__(self, index): # Enables O(1) indexing of slices
		
		if index >= 0:
			return self.indices[0] + self.indices[2] * index
		else:
			return self.indices[1] + self.indices[2] * (index + 1)

	def __iter__(self): # Enables loop syntax

		return iter(self.value) # Enables iteration over range without expanding slice

	def __len__(self):

		return len(self.value) # Python's implementation is probably as efficient as mine would be

	def __reversed__(self):
		
		return slice([self.indices[1], self.indices[0], -self.indices[2]])

class procedure: # Base function object

	def __init__(self, routine, *types):

		self.call = routine
		self.types = types

def f_input(value):

	return input(value)

def f_print(value):

	print(value)
	return True

def f_error(status):
	
	print(status, file = stderr)
	return None

def f_time():

	return perf_counter_ns()

pro_input = (f_input, 'string', 'string')

pro_print = (f_print, 'boolean', 'string')

pro_error = (f_error, 'untyped', 'string') # Fails its type check on purpose to throw an error

pro_time = (f_time, 'integer')

functions = {'_'.join(k.split('_')[1:]): procedure(*v) for k, v in globals().items() if k.split('_')[0] == 'pro'}