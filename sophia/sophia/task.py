from functools import reduce
from multiprocessing import current_process
from typing import Any

from .datatypes.aletheia import typedef
from .metis import processor
from .hemera import debug

class task:
	"""
	Base task object for Sophia.
	A task handles synchronous program execution and passes messages to and
	from the supervisor.
	"""
	def __init__(self, # God objects? What is she objecting to?
				 processor: processor,
				 flags: tuple[str, ...]) -> None:
		
		self.name = processor.name
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		self.flags = flags
		self.caller = None # Stores the state of the calling routine
		self.instructions = processor.instructions
		self.path = int(bool(self.instructions)) # Does not execute if the parser encountered an error
		self.op = self.instructions[0] # Current instruction
		self.cache = processor.cache # Instruction cache
		self.values = processor.values
		self.types = processor.types
		self.signature = [] # Current type signature
		self.properties = typedef() # Final type properties
		self.final = typedef() # Return type of routine

	def execute(self) -> Any:
		"""
		Target of task.pool.apply_async().
		Executes flags, then launches runtime loop.
		"""
		if 'instructions' in self.flags:
			debug.debug_instructions(self)
		if 'profile' in self.flags:
			from cProfile import Profile
			pr = Profile()
			pr.enable()
		value = self.run()
		"""
		Terminate runtime loop and execute flagged operations.
		"""
		if 'profile' in self.flags:
			pr.disable()
			pr.print_stats(sort = 'cumtime')
		if 'namespace' in self.flags:
			debug.debug_namespace(self)
		if 'debug' in self.flags:
			return value
		else:
			self.message('terminate')
			return self.state() # Return mutable state to supervisor

	def run(self) -> Any:
		"""
		Task runtime loop.
		Performs dispatch and executes instructions.
		"""
		debug_task = 'task' in self.flags # Debug runtime loop
		self.caller = None # Reset caller
		while self.path:
			self.op, cache = self.instructions[self.path], self.cache[self.path]
			if debug_task:
				debug.debug_task(self)
			self.path = self.path + 1
			if (address := self.op.register): # Instructions
				routine, registers = self.values[self.op.name], self.op.args
				args = [self.values[arg] for arg in registers]
				self.signature = [self.types[arg] for arg in registers]
				instance, final, signature = (cache.routine, cache.final, cache.signature) if cache else routine(self, *self.signature)
				value = instance(self, *args)
				if final.type != '!': # Suppress write
					self.values[address] = value # Hot-swap descriptors; there's always 1 spare in the system
					self.types[address], self.properties = self.complete(self.properties, final, value), self.types[address] if address in self.types else descriptor()
					self.properties.__dict__ = {}
			elif (name := self.op.name) in interns: # Pseudo-instructions
				interns[name](self)
		else:
			return value

	def branch(self, # Universal branch function
			   scope: int = 0,
			   skip: bool = False,
			   move: bool = False) -> int:

		path = self.path
		while True:
			op, path = self.instructions[path], path + 1
			if not op.register:
				if op.name == 'START' or op.name == 'ELSE':
					scope = scope + 1
				elif op.name == 'END':
					scope = scope - 1
				if scope == 0 and (skip or self.instructions[path].name != 'ELSE'):
					if move:
						self.path = path
					return path

	#def complete(self, # Completes descriptor with properties and inferred type of value
	#			 descriptor: descriptor,
	#			 final: descriptor,
	#			 value: Any):
		
	#	descriptor.type = descriptor.type or final.type or infer_type(value)
	#	descriptor.supertypes = self.values[descriptor.type or 'null'].supertypes
	#	if 'sequence' in descriptor.supertypes:
	#		descriptor.member = descriptor.member or final.member or infer_member(value)
	#		descriptor.length = descriptor.length or final.length or len(value)
	#	descriptor.supermember = self.values[descriptor.member or 'null'].supertypes
	#	return descriptor

	def state(self) -> dict: # Get current state of task as subset of __dict__

		return {'name': self.name,
				'values': self.values.copy(),
				'types': self.types.copy(),
				'instructions': self.instructions,
				'path': self.path,
				'op': self.op,
				'caller': self.caller,
				'final': self.final,
				'cache': self.cache}

	def restore(self, # Restore previous state of task
			    state: dict) -> None:

		self.__dict__.update(state)

	def prepare(self, # Sets up task for event execution
				namespace: dict,
				message: Any) -> None:
		
		self.restore(namespace)
		self.path, scope = 0, 0
		while True:
			op, self.path = self.instructions[self.path], self.path + 1
			if not op.register:
				scope = scope - 1 if op.name == 'END' else scope + 1
				if scope == 1 and op.name == 'EVENT':
					name = op.label[0]
					break
		self.values[name], self.types[name] = message, descriptor('untyped').describe(self)

	def message(self,
				instruction: str | None = None,
				*args: tuple) -> None:
		
		current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def error(self, # Error handler
			  status: str,
			  *args: tuple) -> None:
		
		self.properties.type = 'null'
		self.properties.member = None
		self.properties.length = None
		if self.op.register != '0': # Suppresses error for assertions
			if 'suppress' not in self.flags:
				debug.debug_error(self.name, self.op.line, status, args)
			self.values['0'] = None
			self.path = 0

"""
Internal pseudo-instructions.
"""

def intern_bind(task) -> None:
	
	types = [task.values[item].descriptor for item in task.op.label[0::2]]
	names = task.op.label[1::2]
	args = [task.values[arg] for arg in task.op.args]
	signature = [task.types[arg] for arg in task.op.args]
	for i, name in enumerate(names):
		value = args[i]
		task.properties.type = signature[0].type if types[i].type == 'null' else types[i].type
		task.values[name] = value
		task.types[name], task.properties = task.complete(task.properties, signature[i], value), task.types[name] if name in task.types else descriptor()
		task.properties.type, task.properties.member, task.properties.length = None, None, None

def intern_list(task) -> None:

	address = task.op.label[0]
	value = tuple(task.values[arg] for arg in task.op.args)
	task.properties.type = 'list'
	task.properties.member = reduce(descriptor.mutual, [task.types[arg] for arg in task.op.args]).type
	task.properties.length = len(value)
	task.properties.supertypes = task.values[task.properties.type or 'null'].supertypes
	task.properties.supermember = task.values[task.properties.member or 'null'].supertypes
	task.values[address] = value
	task.types[address], task.properties = task.properties, task.types[address] if address in task.types else descriptor()
	task.properties.type, task.properties.member, task.properties.length = None, None, None

def intern_record(task) -> None:

	address = task.op.label[0]
	keys = tuple(task.values[arg] for arg in task.op.args[0::2])
	values = tuple(task.values[arg] for arg in task.op.args[1::2])
	value = dict(zip(keys, values))
	task.properties.type = 'record'
	task.properties.member = reduce(descriptor.mutual, [task.types[arg] for arg in task.op.args[1::2]]).type
	task.properties.length = len(value)
	task.properties.supertypes = task.values[task.properties.type or 'null'].supertypes
	task.properties.supermember = task.values[task.properties.member or 'null'].supertypes
	task.values[address] = value
	task.types[address], task.properties = task.properties, task.types[address] if address in task.types else descriptor()
	task.properties.type, task.properties.member, task.properties.length = None, None, None

def intern_loop(task) -> None:
	
	scope = 1
	while True:
		task.path = task.path - 1
		if not (op := task.instructions[task.path]).register:
			if op.name == 'START':
				scope = scope - 1
			elif op.name == 'END':
				scope = scope + 1
			if scope == 0:
				return

def intern_break(task) -> None: # BUGGED: ONLY SKIPS TO NEXT CONTINUE

	task.values[task.op.register], task.values[task.op.args[0]] = None, None # Sanitise registers
	while True:
		op, task.path = task.instructions[task.path], task.path + 1
		if op.name == 'LOOP' and not op.register:
			return

def intern_skip(task) -> None:
	
	value, address = task.values[task.op.args[0]], task.op.label[0]
	signature, final = task.signature[0], task.properties
	final.type, final.member, final.length = signature.type, signature.member, signature.length
	path = task.path
	while True:
		op, path = task.instructions[path], path + 1
		if not op.register and op.name == 'RETURN':
			task.path = path
			task.values[address] = value
			#task.types[address] = None
			return

interns = {'BIND': intern_bind,
		   'LIST': intern_list,
		   'RECORD': intern_record,
		   'LOOP': intern_loop,
		   'BREAK': intern_break,
		   'SKIP': intern_skip}