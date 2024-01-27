from typing import Self

from .hemera import handler
from .stdlib import arche
from .datatypes import aletheia
from .internal.instructions import instruction
from .internal.presets import STDLIB_NAMES

class processor:
	"""
	Static analysis processor for generated instructions.
	"""
	def __init__(
		self,
		handler: handler,
		instructions: list[instruction],
		namespace: dict,
		types: dict | None = None
		) -> None:

		"""
		Static attributes for the task to access.
		"""
		self.name = instructions[0].label[0] if instructions else ''
		self.handler = handler
		if types is None:
			self.values = arche.stdvalues | namespace
			self.types = arche.stdtypes | {k: aletheia.infer(v) for k, v in namespace.items()}
		else:
			self.values = arche.stdvalues | namespace
			self.types = arche.stdtypes| types
		"""
		Mutable attributes for the processor to access.
		"""
		self.instructions = instructions
		self.path = int(bool(instructions))
		self.op = None
		#self.signature = []
		#self.properties = {}
		#self.state = None
		#self.scope()

	def analyse(self) -> Self:

		self.handler.debug_processor(self)
		while 0 < self.path < len(self.instructions): # This can and does change
			self.op = self.instructions[self.path]
			self.path = self.path + 1
			if self.op.name == 'BIND':
				self.bind()
		return self

	def bind(self) -> None:
		"""
		Evaluates type checking for name binding, removing instructions
		if the type check is known to succeed.
		Currently does not bother to remove unnecessary type checks.
		"""
		i, checks, addresses = self.path, [], []
		while self.instructions[i].name != '.bind':
			i = i + 1
		for name in self.instructions[i].label:
			if name in STDLIB_NAMES:
				self.handler.error('BIND', name)
		binds = self.instructions[self.path:i]
		for item in binds:
			if item.args[1] == '?':
				addresses.append(item.args[0])
			else:
				addresses.append(item.address)
				checks.append(item)
		self.instructions[i].args = addresses
		self.instructions[self.path - 1:i] = checks
		self.path = self.path + len(checks)

def user_namespace(
	namespace: dict[str]
	) -> dict[str]:

	return {k: v for k, v in namespace.items() if not (k in STDLIB_NAMES.values())}