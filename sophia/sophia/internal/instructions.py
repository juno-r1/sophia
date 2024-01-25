from dataclasses import dataclass, field
from typing import Self

@dataclass(slots = True, repr = False)
class instruction:
	"""
	Instructions used in Sophia's virtual machine.
	Internal instructions use the prefix '.'.
	Labels have no return address.
	"""
	name: str											# Name of the command to be called.
	address: str = ''									# Return address.
	args: list[str] = field(default_factory = list)		# Argument addresses.
	label: list[str] = field(default_factory = list)	# Additional information.
	arity: int = field(init = False)					# Number of arguments.

	def __post_init__(self) -> None:

		self.arity = len(self.args)

	def __str__(self) -> str:
		
		string = self.name
		if self.address:
			string = string + ' ' + self.address
		if self.args:
			string = string + ' ' + ' '.join(self.args)
		string = string + ';'
		if self.label:
			string = string + ' ' + ' '.join(self.label)
		return string

	__repr__ = __str__

	@classmethod
	def left(
		cls,
		left,
		right
		) -> list[Self]:
		"""
		Converts a built-in method into the first half of a composed function.
		"""
		return [
			cls('START', label = [left.name]),
			cls(left.name, right.params[0], left.params),
			cls('END')
		]

	@classmethod
	def right(
		cls,
		right
		) -> list[Self]:
		"""
		Converts a built-in method into the second half of a composed function.
		"""
		return [
			cls('START', label = [right.name]),
			cls(right.name, '0', right.params),
			cls('return', '0', ('0',)),
			cls('END')
		]