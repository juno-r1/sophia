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

		if self.address:
			return '{0} {1} {2}; {3}'.format(self.name, self.address, ' '.join(self.args), ' '.join(self.label))
		else:
			return '{0}; {1}'.format(self.name, ' '.join(self.label))

	__repr__ = __str__

	#@classmethod
	#def read(cls, value): # Convert string to instruction

	#	command, label = value.split(';')
	#	command, label = command.split(' '), label.split(' ')
	#	line, name, register, args = int(command[0]), command[1], command[2], tuple(command[3:])
	#	return cls(name, register, args, line, label)

	#@classmethod
	#def rewrite( # Rewrite instruction for subtypes
	#	cls,
	#	ins,
	#	old: str,
	#	new: str
	#	):

	#	args = tuple(new if i == old else i for i in ins.args)
	#	label = [new if i == old else i for i in ins.label]
	#	return cls(ins.name, ins.register, args, line = ins.line, label = label)

	"""
	Instruction generation functions.
	"""

	#@classmethod
	#def generate_labels(
	#	cls,
	#	name: str
	#	) -> list:

	#	return [[cls('START', '', label = [name])],
	#			[cls('.return', '0', (name,)), cls('END', '')]]

	#@classmethod
	#def generate_supertype(
	#	cls,
	#	name: str,
	#	supername: str
	#	) -> list:

	#	return [cls(supername, '0', (name,)), 
	#			cls('?', '0', ('0',)), # Convert to boolean
	#			cls('.constraint', '0', ('0',), label = [supername])]

	#@classmethod
	#def generate_union(
	#	cls,
	#	name: str,
	#	x_name: str,
	#	y_name: str
	#	) -> list:

	#	return [cls(x_name, '0', (name,)), 
	#			cls('?', '1', ('0',)),
	#			cls(y_name, '0', (name,)),
	#			cls('?', '0', ('0',)),
	#			cls('or', '0', ('0', '1')),
	#			cls('.constraint', '0', ('0',))]

	#@classmethod
	#def generate_intersection(
	#	cls,
	#	name: str,
	#	x_name: str
	#	) -> list:

	#	return [cls(x_name, '0', (name,)), 
	#			cls('?', '0', ('0',)),
	#			cls('.constraint', '0', ('0',))]

	#@classmethod
	#def generate_x_function(
	#	cls,
	#	name: str,
	#	args: tuple[str, ...]
	#	) -> list:

	#	return [cls('START', label = [name]),
	#			cls(name, '0', args = args),
	#			cls('.return', '0', ('0',)),
	#			cls('END')]

	#@classmethod
	#def generate_y_function(
	#	cls,
	#	name: str,
	#	args: tuple[str, ...],
	#	register: str
	#	) -> list:

	#	return [cls('START', label = [name]),
	#			cls(name, register, args = args),
	#			cls('END')]