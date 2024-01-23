class a:

	def __init__(self):

		self.x = [1, 2, 3]

	def __iter__(self):

		yield from self.x

x = a().__iter__()
print(x.send(None))