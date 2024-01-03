from functools import reduce
from multiprocessing import current_process
from typing import Any

from .datatypes import aletheia
from .datatypes.aletheia import typedef
from .datatypes.mathos import real, slice
from .hemera import handler
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
		self.cache = processor.cache # Instruction cache
		self.op = self.instructions[0] # Current instruction
		self.path = 1 # Instruction index
		"""
		Program state management.
		"""
		self.caller = None # State of the calling routine
		self.final = aletheia.std_any # Return type of routine
		self.handler = handler(*flags) # Error handler

	def execute(self) -> Any:
		"""
		Target of task.pool.apply_async().
		Executes flags and runtime loop.
		"""
		self.handler.initial(self)
		value = self.run()
		return self.handler.final(self, value)

	def run(self) -> Any:
		"""
		Task runtime loop.
		Performs dispatch and executes instructions.
		"""
		debug_task = 'task' in self.handler.flags # Debug runtime loop
		self.caller = None # Reset caller
		while self.path:
			self.op, cache = self.instructions[self.path], self.cache[self.path]
			if debug_task:
				self.handler.debug_task(self)
			self.path = self.path + 1
			if self.op.address: # Skip labels
				registers = self.op.args
				args = [self.values[arg] for arg in registers]
				self.signature = [self.types[arg] for arg in registers]
				if (name := self.op.name) in task.interns: # Internal instructions
					task.interns[name](self, *args)
				else:
					value = (cache if cache else self.values[name])(self, *args)
		else:
			return value

	def branch(self, # Universal branch function
			   scope: int = 0,
			   skip: bool = False,
			   move: bool = False) -> int:

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
#			if not op.address:
#				scope = scope - 1 if op.name == 'END' else scope + 1
#				if scope == 1 and op.name == 'EVENT':
#					name = op.label[0]
#					break
#		self.values[name], self.types[name] = message, descriptor('untyped').describe(self)

#	def message(self,
#				instruction: str | None = None,
#				*args: tuple) -> None:
		
#		current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

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

	def intern_constraint(
		self,
		constraint: bool
		) -> None:
		
		pass
		#name = task.instructions[0].label[0]
		#if not constraint:
		#	value = task.values[name]
		#	task.restore(task.caller)
		#	task.error('CAST', name, str(value))
		#elif task.op.label and task.op.label[0] != name: # Update type of checked value for subsequent constraints
		#	task.types[name].type = task.op.label[0]
		#	task.types[name].describe(task)

	def intern_event(
		self,
		*types: tuple[typedef, ...]
		) -> None:

		pass
		#name = task.op.address
		#types, params = [descriptor.read(i).describe(task) for i in task.op.label[0::2]], task.op.label[1::2]
		#start = task.path
		#task.branch(0, True, True)
		#end = task.branch(0, True, True)
		#definition = event_method(task.instructions[start:end], params, types)
		#routine = task.values[name] if name in task.values and task.types[name].type == 'event' else eventdef(name)
		#routine.register(definition, types[0], tuple(types[1:-1]))
		#return routine

	def intern_function(
		self,
		*types: tuple[typedef, ...]
		) -> None:
		
		pass
		#name = task.op.address
		#types, params = [descriptor.read(i).describe(task) for i in task.op.label[0::2]], task.op.label[1::2]
		#start, end = task.path, task.branch(0, True, True)
		#definition = function_method(task.instructions[start:end], params, types)
		#routine = task.values[name] if name in task.values and task.types[name].type == 'function' else funcdef(name)
		#routine.register(definition, types[0], tuple(types[1:]))
		#return routine

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
	
		address = self.op.address
		self.message('link', task.op.address + '.sph')
		self.values[address] = self.calls.recv()
		self.types[address] = typedef(aletheia.std_future)
	
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
			self.values[address] = next(iterator)
			self.types[address] = typedef(aletheia.std_any)
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
	
		pass
	#	name, supername = task.op.address, supertype.name
	#	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
	#	type_tag.supertypes = [name] + super_tag.supertypes
	#	start, end = task.path, task.branch(0, True, True)
	#	instructions = task.instructions[start:end]
	#	routine = typedef(name, supertype.supertypes, supertype.prototype)
	#	if supername in aletheia.supertypes: # Built-in supertype
	#		check = kadmos.generate_supertype(name, supername)
	#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
	#		instructions[1:1] = check
	#		routine.register(type_method(instructions, name, super_tag), final_tag, (descriptor('untyped', prepare = True),))
	#	else:
	#		tree = supertype.tree.true
	#		while tree: # Traverse down tree and copy all false leaves
	#			key, value = tree.false.signature, tree.false.routine
	#			definition = [instruction.rewrite(i, supername, name) for i in value.instructions] # Rewrite methods with own type name
	#			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
	#			routine.register(type_method(definition, name, key[0]), final_tag, key)
	#			tree = tree.true
	#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
	#	return routine

	#def type_type_any(task, supertype, prototype):
	
	#	name, supername = task.op.address, supertype.name
	#	type_tag, final_tag, super_tag = descriptor(name), descriptor(name), descriptor(supername).describe(task)
	#	type_tag.supertypes = [name] + super_tag.supertypes
	#	start, end = task.path, task.branch(0, True, True)
	#	instructions = task.instructions[start:end]
	#	routine = typedef(name, supertype.supertypes, prototype)
	#	if supername in aletheia.supertypes: # Built-in supertype
	#		check = kadmos.generate_supertype(name, supername)
	#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
	#		instructions[1:1] = check
	#		routine.register(type_method(instructions, name, super_tag), final_tag, (descriptor('untyped', prepare = True),))
	#	else:
	#		tree = supertype.tree.true
	#		while tree: # Traverse down tree and copy all false leaves
	#			key, value = tree.false.signature, tree.false.routine
	#			definition = [instruction.rewrite(i, supername, name) for i in value.instructions] # Rewrite methods with own type name
	#			definition[-2:-2] = instructions[1:-2] # Add user constraints to instructions
	#			routine.register(type_method(definition, name, key[0]), final_tag, key)
	#			tree = tree.true
	#		routine.register(type_method(instructions, name, super_tag), final_tag, (super_tag,))
	#	return routine

	interns = {
		'.bind': intern_bind,
		'.break': intern_break,
		'.continue': intern_loop,
		'.event': intern_event,
		'.function': intern_function,
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