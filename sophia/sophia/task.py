from functools import reduce
from multiprocessing import current_process
from typing import Any

from .datatypes import aletheia, iris
from .datatypes.aletheia import typedef
from .datatypes.mathos import real, slice
from .metis import processor

class task:
	"""
	Base task object for Sophia.
	A task handles synchronous program execution and passes messages to and
	from the supervisor.
	"""
	def __init__( # God objects? What is she objecting to?
		self,
		processor: processor,
		) -> None:
		"""
		Task identifiers.
		"""
		self.name = processor.name
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		"""
		Namespace management.
		"""
		self.values = processor.values
		self.types = processor.types
		self.signature = [] # Current type signature
		self.properties = None # Final type override
		"""
		Instruction execution data.
		"""
		self.instructions = processor.instructions # Guaranteed to be non-empty
		self.op = self.instructions[0] # Current instruction
		self.path = 1 # Instruction index
		self.sub = 0 # Subroutine index
		"""
		Program state management.
		"""
		self.caller = None # State of the calling routine
		self.final = aletheia.std_any # Return type of routine
		self.handler = processor.handler # Error handler

	def execute(self) -> Any:
		"""
		Target of task.pool.apply_async().
		Executes flags and runtime loop.
		"""
		self.handler.debug_initial(self)
		try:
			value = self.run()
		except SystemExit:
			return
		return self.handler.debug_final(self, value)

	def run(self) -> Any:
		"""
		Task runtime loop.
		Performs dispatch and executes instructions.
		"""
		debug_task = 'task' in self.handler.flags # Debug runtime loop
		self.caller = None # Reset caller
		try:
			while self.path:
				if self.sub:
					pass
				else:
					self.op = self.instructions[self.path]
					if debug_task:
						self.handler.debug_task(self)
					self.path = self.path + 1
					if self.op.address: # Skip labels
						registers = self.op.args
						args = [self.values[arg] for arg in registers]
						self.signature = [self.types[arg] for arg in registers]
					else:
						continue
					if (name := self.op.name) in task.interns: # Internal instructions
						value = task.interns[name](self, *args)
					else:
						value = self.values[name](self, *args)
			else:
				return value
		except KeyError as e:
			self.handler.error('FIND', e.args[0])

	def branch(
		self,
		scope: int = 0,
		skip: bool = False,
		move: bool = False
		) -> int:
		"""
		Universal branch function.
		"""
		path = self.path
		while True:
			op, path = self.instructions[path], path + 1
			if not op.address:
				if op.name == 'START' or op.name == 'ELSE':
					scope = scope + 1
				elif op.name == 'END':
					scope = scope - 1
				if scope == 0 and (skip or self.instructions[path].name != 'ELSE'):
					if move:
						self.path = path
					return path

	def call(self) -> dict: # Get current state of task as subset of __dict__

		return {
			'name': self.name,
			'values': self.values.copy(),
			'types': self.types.copy(),
			'instructions': self.instructions,
			'op': self.op,
			'path': self.path,
			'sub': self.sub,
			'caller': self.caller,
			'final': self.final
		}

	def restore( # Restore previous state of task
		self,
		state: dict | None = None
		) -> None:

		self.__dict__.update(state if state else self.caller)

	def prepare( # Sets up task for event execution
		self,
		namespace: dict,
		message: Any
		) -> None:
		
		self.restore(namespace)
		self.path, scope = 0, 0
		while True:
			op, self.path = self.instructions[self.path], self.path + 1
			if not op.address:
				scope = scope - 1 if op.name == 'END' else scope + 1
				if scope == 1 and op.name == 'EVENT':
					name = op.label[0]
					break
		self.values[name], self.types[name] = message, typedef(aletheia.std_any)

	def message(
		self,
		instruction: str,
		*args: tuple
		) -> None:

		current_process().stream.put(iris.message(self.pid, instruction, args))

	"""
	Internal instructions.
	"""

	def intern_bind(
		self,
		*args: tuple
		) -> None:

		for i, name in enumerate(self.op.label):
			self.values[name] = args[i]
			self.types[name] = typedef(self.signature[i])

	def intern_break(
		self,
		iterator: Any,
		index: Any
		) -> None:
		
		op = self.instructions[self.path]
		iterator, index = self.op.args # Registers for the iterator and loop index
		self.values[iterator], self.values[index] = None, None # Sanitise registers
		while not op.name == '.loop':
			op, self.path = self.instructions[self.path], self.path + 1

	def intern_check(
		self,
		value: Any,
		check: typedef
		) -> None:
		"""
		Type check wrapper for when a failed type check requires an error condition.
		"""
		address = self.op.address
		self.values[address] = value if check(self, value, write = False) else self.handler.error('TYPE', check, value)
		self.types[address] = typedef(check)
		return value

	def intern_constraint(
		self,
		constraint: bool | None = None
		) -> None:
		"""
		Takes true, false, or null.
		True constraint does nothing.
		False constraint returns false.
		Null constraint signifies a successful check and returns true.
		"""
		if constraint is None:
			self.path = 0
			return True
		if not constraint:
			self.path = 0
			return False

	def intern_event(
		self,
		*types: tuple[typedef, ...]
		) -> None:
		
		name = self.op.address
		params = self.op.label
		start = self.path
		end = self.branch(0, True, True)
		end = self.branch(1, True, True)
		definition = aletheia.event_method(aletheia.sub_user(self.instructions[start:end], params, types))
		if name in self.values and self.types[name] < aletheia.std_event:
			self.values[name].extend(definition)
		else:
			routine = aletheia.eventdef()
			routine.extend(definition)
			self.values[name] = routine
			self.types[name] = typedef(aletheia.std_event)

	def intern_function(
		self,
		*types: tuple[typedef, ...]
		) -> None:
		
		name = self.op.address
		params = self.op.label
		start, end = self.path, self.branch(0, True, True)
		definition = aletheia.function_method(aletheia.sub_user(self.instructions[start:end], params, types))
		if name in self.values and self.types[name] < aletheia.std_function:
			self.values[name].extend(definition)
		else:
			routine = aletheia.funcdef()
			routine.extend(definition)
			self.values[name] = routine
			self.types[name] = typedef(aletheia.std_function)

	def intern_future(
		self,
		routine: aletheia.funcdef,
		*args: tuple
		) -> None:

		address, signature, arity = self.op.address, self.signature[1:], self.op.arity - 1
		instance = routine.true if signature else routine.false
		while instance: # Traverse tree; terminates upon reaching leaf node
			instance = instance.true if instance.index < arity and instance.check(signature) else instance.false
		if instance is None or instance.arity != arity:
			self.handler.error('DISP', self.op.args[0], signature)
		for i, item in enumerate(signature): # Verify type signature
			if item > instance.signature[i]:
				self.handler.error('DISP', self.op.args[0], signature)
		values = self.values.copy() | dict(zip(instance.params, args))
		types = self.types.copy() | dict(zip(instance.params, instance.signature))
		self.message('future', instance, values, types)
		self.types[address] = typedef(aletheia.std_future)
		self.values[address] = self.calls.recv()

	def intern_iterator(
		self,
		sequence: Any
		) -> None:
	
		address = self.op.address
		self.values[address] = iter(sequence)
		self.types[address] = typedef(aletheia.std_any)

	def intern_link(
		self,
		) -> None:
	
		for name in self.op.label: # We can do this bit asynchronously
			self.message('link', name + '.sph')
		for name in self.op.label:
			self.values[name] = self.calls.recv()
			self.types[name] = typedef(aletheia.std_future)
	
	def intern_list(
		self,
		*args: tuple
		) -> None:

		address = self.op.address
		element = reduce(typedef.__or__, self.signature)
		length = len(args)
		self.values[address] = args
		self.types[address] = typedef(
			aletheia.std_list,
			aletheia.cls_element(element),
			aletheia.cls_length(length)
		)

	def intern_loop( # Continue is just an early loop
		self
		) -> None:
	
		scope = 1
		while True:
			self.path = self.path - 1
			if not (op := self.instructions[self.path]).address:
				if op.name == 'START':
					scope = scope - 1
				elif op.name == 'END':
					scope = scope + 1
				if scope == 0:
					return

	def intern_meta(
		self,
		string: str
		) -> None:

		pass
		#meta = module(string, meta = task.name)
		#offset = int(task.op.address) - 1
		#constants = len([item for item in task.values if item[0] == '&']) - 1
		#instructions, values, types = translator(meta, constants = constants).generate(offset = offset)
		#start = task.path
		#end = task.branch(0, True, False)
		#task.instructions[start + 1:end] = instructions
		#task.values.update(values)
		#task.types.update({k: v.describe(task) for k, v in types.items()})

	def intern_next(
		self,
		iterator: Any,
		) -> None:
	
		address = self.op.address
		try:
			self.values[address] = (value := next(iterator))
			self.types[address] = aletheia.infer(value)
		except StopIteration:
			self.values[self.op.args[0]] = None # Sanitise register
			self.branch(1, False, True)

	def intern_range(
		self,
		x: real,
		y: real,
		z: real
		) -> None:

		address = self.op.address
		value = tuple(slice(x, y, z))
		self.values[address] = value
		self.types[address] = typedef(
			aletheia.std_list,
			aletheia.cls_element(aletheia.std_integer),
			aletheia.cls_length(len(value))
		)

	def intern_record(
		self,
		*args: tuple
		) -> None:
		
		address = self.op.address
		element = reduce(typedef.__or__, self.signature)
		length = len(args)
		self.values[address] = dict(zip((self.values[arg] for arg in self.op.label), args))
		self.types[address] = typedef(
			aletheia.std_record,
			aletheia.cls_element(element),
			aletheia.cls_length(length)
		)

	def intern_slice(
		self,
		x: real,
		y: real,
		z: real
		) -> None:

		address = self.op.address
		value = slice(x, y, z)
		self.values[address] = value
		self.types[address] = typedef(
			aletheia.std_slice,
			aletheia.cls_element(aletheia.std_integer),
			aletheia.cls_length(len(value))
		)

	def intern_type(
		self,
		supertype: typedef,
		prototype: Any = None
		) -> None:
	
		address = self.op.address
		start, end = self.path, self.branch(0, True, True)
		instructions = self.instructions[start:end]
		method = aletheia.type_property(address, instructions)
		self.values[address] = typedef(supertype, method, prototype = prototype)
		self.types[address] = typedef(aletheia.std_type)

	interns = {
		'.bind': intern_bind,
		'.break': intern_break,
		'.check': intern_check,
		'.constraint': intern_constraint,
		'.continue': intern_loop,
		'.event': intern_event,
		'.function': intern_function,
		'.future': intern_future,
		'.iterator': intern_iterator,
		'.link': intern_link,
		'.list': intern_list,
		'.loop': intern_loop,
		'.meta': intern_meta,
		'.next': intern_next,
		'.range': intern_range,
		'.record': intern_record,
		'.slice': intern_slice,
		'.type': intern_type
	}