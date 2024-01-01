from functools import reduce
from multiprocessing import current_process
from re import match
from sys import stderr
from typing import Any

from .datatypes import aletheia
from .internal.presets import ERRORS, TOKENS_NAMESPACE
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
		flags: tuple[str, ...]
		) -> None:
		
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
		self.properties = None # Final type override
		self.final = aletheia.std_any # Return type of routine

	def execute(self) -> Any:
		"""
		Target of task.pool.apply_async().
		Executes flags, then launches runtime loop.
		"""
		if 'instructions' in self.flags:
			self.debug_instructions()
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
			self.debug_namespace()
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
				self.debug_task()
			self.path = self.path + 1
			if self.op.register: # Instructions
				registers = self.op.args
				args = [self.values[arg] for arg in registers]
				self.signature = [self.types[arg] for arg in registers]
				value = (cache if cache else self.values[self.op.name])(self, *args)
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

#	#def complete(self, # Completes descriptor with properties and inferred type of value
#	#			 descriptor: descriptor,
#	#			 final: descriptor,
#	#			 value: Any):
		
#	#	descriptor.type = descriptor.type or final.type or infer_type(value)
#	#	descriptor.supertypes = self.values[descriptor.type or 'null'].supertypes
#	#	if 'sequence' in descriptor.supertypes:
#	#		descriptor.member = descriptor.member or final.member or infer_member(value)
#	#		descriptor.length = descriptor.length or final.length or len(value)
#	#	descriptor.supermember = self.values[descriptor.member or 'null'].supertypes
#	#	return descriptor

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

#	def restore(self, # Restore previous state of task
#			    state: dict) -> None:

#		self.__dict__.update(state)

#	def prepare(self, # Sets up task for event execution
#				namespace: dict,
#				message: Any) -> None:
		
#		self.restore(namespace)
#		self.path, scope = 0, 0
#		while True:
#			op, self.path = self.instructions[self.path], self.path + 1
#			if not op.register:
#				scope = scope - 1 if op.name == 'END' else scope + 1
#				if scope == 1 and op.name == 'EVENT':
#					name = op.label[0]
#					break
#		self.values[name], self.types[name] = message, descriptor('untyped').describe(self)

#	def message(self,
#				instruction: str | None = None,
#				*args: tuple) -> None:
		
#		current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def error( # Error handler
		self,
		status: str,
		*args: tuple
		) -> None:
				
		self.properties = aletheia.std_none
		if self.op.register != '0': # Suppresses error for assertions
			if 'suppress' not in self.flags:
				print('===',
					  '{0} (line {1})'.format(self.name, self.op.line),
					  ERRORS[status].format(*args) if args else ERRORS[status],
					  '===',
					  sep = '\n',
					  file = stderr)
			self.path = 0
		self.values['0'] = None
		self.types['0'] = aletheia.std_none

	"""
	Debug operations.
	"""

	def debug_instructions(self) -> None:
	
		print('===', file = stderr)
		for i, instruction in enumerate(self.instructions):
			print(i,
				  instruction,
				  sep = '\t',
				  file = stderr)
		print('===', file = stderr)

	def debug_namespace(self) -> None:
	
		print('===',
			  self.name,
			  '---',
			  '\n---\n'.join(('{0} {1} {2}'.format(name, self.types[name], value) for name, value in self.values.items() if match(TOKENS_NAMESPACE, name))),
			  '===',
			  sep = '\n',
			  file = stderr)

	def debug_task(self) -> None:
	
		print(str(self.path),
			  self.op,
			  sep = '\t',
			  file = stderr)

	"""
	Internal pseudo-instructions.
	"""

	def intern_bind(self) -> None:
	
		args = [self.values[arg] for arg in self.op.args]
		types = [self.types[arg] for arg in self.op.args]
		for i, name in enumerate(self.op.label):
			self.values[name] = args[i]
			self.types[name] = aletheia.typedef(types[i])

	def intern_type(self) -> None:
		"""
		Delegates a type check based on the known type of a bound name.
		A variable command name is not possible in the current
		task architecture.
		"""
		register = self.op.args[0]
		value = self.values[register]
		address, name = self.op.label
		if name in self.types:
			check = self.types[name]
			check(self, value)
		else:
			check = self.types[register]
		self.values[address] = value
		self.types[address] = aletheia.typedef(check)

	def intern_list(self) -> None:

		address = self.op.label[0]
		value = tuple(self.values[arg] for arg in self.op.args)
		element = reduce(aletheia.typedef.__or__, (self.types[arg] for arg in self.op.args))
		length = len(value)
		self.values[address] = value
		self.types[address] = aletheia.typedef(
			aletheia.std_list,
			aletheia.cls_element(element),
			aletheia.cls_length(length)
		)

	def intern_record(self) -> None:

		address = self.op.label[0]
		keys = tuple(self.values[arg] for arg in self.op.args[0::2])
		values = tuple(self.values[arg] for arg in self.op.args[1::2])
		value = dict(zip(keys, values))
		element = reduce(aletheia.typedef.__or__, (self.types[arg] for arg in self.op.args[0::2]))
		length = len(value)
		self.values[address] = value
		self.types[address] = aletheia.typedef(
			aletheia.std_record,
			aletheia.cls_element(element),
			aletheia.cls_length(length)
		)

	def intern_loop(self) -> None: # Continue is just an early loop
	
		scope = 1
		while True:
			self.path = self.path - 1
			if not (op := self.instructions[self.path]).register:
				if op.name == 'START':
					scope = scope - 1
				elif op.name == 'END':
					scope = scope + 1
				if scope == 0:
					return

	def intern_break(self) -> None:
		
		op = self.instructions[self.path]
		iterator, index = self.op.args # Registers for the iterator and loop index
		self.values[iterator], self.values[index] = None, None # Sanitise registers
		while not (op.name == 'LOOP' and not op.register):
			op, self.path = self.instructions[self.path], self.path + 1

	def intern_skip(self) -> None:
	
		pass
		#value, address = task.values[task.op.args[0]], task.op.label[0]
		#signature, final = task.signature[0], task.properties
		#final.type, final.member, final.length = signature.type, signature.member, signature.length
		#path = task.path
		#while True:
		#	op, path = task.instructions[path], path + 1
		#	if not op.register and op.name == 'RETURN':
		#		task.path = path
		#		task.values[address] = value
		#		#task.types[address] = None
		#		return

interns = {
	'BIND': task.intern_bind,
	'TYPE': task.intern_type,
	'LIST': task.intern_list,
	'RECORD': task.intern_record,
	'LOOP': task.intern_loop,
	'CONTINUE': task.intern_loop,
	'BREAK': task.intern_break,
	'SKIP': task.intern_skip
}