import multiprocessing as mp
import cProfile

class worker:

	def __init__(self, x):

		self.x = x
		self.stream = None
		self.receiver = None

	def execute(self, n):

		#print('Started!')
		for i in range(self.x, self.x + n):
			self.x = i
			self.stream.send((self.execute_async, ()))
		for i in range(n):
			x = self.receiver.recv()
		#print('Done!')
		self.stream.send(None) # Sentinel value

	def execute_async(self):

		#print('Working!')
		return self.x

if __name__ == '__main__':

	pr = cProfile.Profile()
	pr.enable()

	with mp.Pool(maxtasksperchild = 50) as pool:
	
		starter = worker(0)
		receiver, starter.stream = mp.Pipe()
		stream, starter.receiver = mp.Pipe()
		result = pool.apply_async(starter.execute, (100,))
		while not result.ready():
			value = receiver.recv()
			if value:
				future = pool.apply_async(*value)
				stream.send(future.get())
			else:
				break
		pool.close()
		pool.join()

	pr.disable()
	pr.print_stats(sort = 'tottime')