from dataclasses import dataclass, field

@dataclass(slots = True, repr = False)
class instruction:
	"""
	Instructions used in Sophia's virtual machine.
	Internal instructions use the prefix '.'.
	Labels have no return address.
	"""
	name: str											# Name of the command to be called.
	address: str = ''									# Return address.
	args: tuple[str, ...] = ()							# Argument addresses.
	label: list[str] = field(default_factory = list)	# Additional information.
	arity: int = field(init = False)					# Number of arguments.

	def __post_init__(self) -> None:

		self.arity = len(self.args)

	def __str__(self) -> str:
		
		if self.args:
			return '{0} {1} {2}; {3}'.format(self.name, self.address, ' '.join(self.args), ' '.join(self.label))
		elif self.address:
			return '{0} {1}; {2}'.format(self.name, self.address, ' '.join(self.label))
		else:
			return '{0}; {1}'.format(self.name, ' '.join(self.label))

	__repr__ = __str__