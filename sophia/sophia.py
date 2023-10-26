'''
The Sophia module is the core of the language.
The module defines the runtime environment and task operations.
This is the root module and the only module the user should need to access.
'''

# ☉ 0.6.1 30-09-2023

import aletheia, hemera, iris, kadmos, metis
import multiprocessing as mp
import os
from queue import Empty
import hemera

class runtime:
	"""
	Base runtime environment for Sophia.
	The runtime environment is the supervisor for the tasks created by a
	running program. It implements a pool for task scheduling and handles
	message passing by acting as an intermediary between running tasks.
	"""
	def __init__(self, address, *flags, root = 'sophia'):
		
		mp.freeze_support()
		try:
			mp.set_start_method('spawn' if os.name == 'nt' else 'fork')
		except RuntimeError:
			pass
		initial = kadmos.module(address, root = root)
		if 'tree' in flags:
			hemera.debug_tree(initial) # Here's tree
		processor = metis.processor(*kadmos.translator(initial).generate()).analyse()
		self.root = root
		self.stream = mp.Queue() # Supervisor message stream
		self.pool = mp.Pool(initializer = self.initialise)
		self.main = task(processor, flags) # Initial task
		self.tasks = {self.main.pid: iris.proxy(self.main)} # Proxies of tasks
		self.events = {} # Persistent event tasks
		self.flags = flags

	def initialise(self): # Cheeky way to sneak a queue into a task
	
		mp.current_process().stream = self.stream

	def future(self, pid, routine, args, method):

		args = self.values | {routine.name: method} | dict(zip(routine.params, args))
		types = self.types | {routine.name: aletheia.infer(method)} | dict(zip(routine.params, routine.signature))
		new = task(routine.instructions, args, types, self.flags)
		self.tasks[new.pid] = iris.proxy(new)
		if types[routine.name].type == 'event':
			self.events[new.pid] = new # Persistent reference to event
		self.tasks[new.pid].result = self.pool.apply_async(new.execute)
		self.tasks[new.pid].count = self.tasks[new.pid].count + 1
		self.tasks[pid].references.append(new.pid) # Mark reference to process
		self.tasks[pid].calls.send(iris.reference(new, routine.final)) # Return reference to process

	def send(self, pid, reference, message):
		
		if reference.name == 'stdin':
			hemera.debug_error('sophia', 0, 'WRIT', ())
		elif reference.name == 'stdout':
			hemera.stream_out(message)
		elif reference.name == 'stderr':
			hemera.stream_err(message)
		elif reference.pid in self.events: # Update event
			self.tasks[reference.pid].result.get() # Wait until routine is done with previous message
			routine = self.events[reference.pid]
			routine.prepare(self.tasks[reference.pid].state, message) # Mutate this version of the task
			self.tasks[reference.pid].result = self.pool.apply_async(routine.execute)
		else:
			self.tasks[reference.pid].messages.send(message)

	def resolve(self, pid, reference):

		if reference.name == 'stdin':
			self.tasks[pid].calls.send(hemera.stream_in())
		elif reference.name == 'stdout' or reference.name == 'stderr':
			self.tasks[pid].calls.send(hemera.debug_error('sophia', 0, 'READ', ()))
		elif self.tasks[reference.pid].result.ready():
			self.tasks[pid].calls.send(self.tasks[reference.pid].result.get())
		else:
			self.tasks[reference.pid].requests.append(pid) # Submit request for return value

	def read(self, pid, message):
		"""
		Multiprocessing disables input for all child processes,
		so it has to be handled by the supervisor.
		"""
		self.tasks[pid].calls.send(hemera.stream_in(message))

	def link(self, pid, name):
		
		linked = kadmos.module(name, root = self.root)
		instructions, values, types = kadmos.translator(linked).generate()
		routine = task(instructions, values, types, self.flags)
		self.tasks[routine.pid] = iris.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(iris.reference(routine, aletheia.descriptor('untyped', prepare = True))) # Return reference to process

	def terminate(self, pid):
		
		if pid not in self.tasks:
			raise RuntimeError
		state = self.tasks[pid].result.get() # Get return state of task
		self.tasks[pid].state = state # Store persistent state in supervisor
		value = state['values']['0'] # Get return value from state
		for process in self.tasks[pid].requests:
			self.tasks[process].calls.send(value)
		self.tasks[pid].requests = []
		for process in self.tasks[pid].references:
			self.tasks[process].count = self.tasks[process].count - 1
			if self.tasks[process].count == 0:
				del self.tasks[process] # Free referenced tasks
				if process in self.events: # Free events
					del self.events[process]
		if pid == self.main.pid:
			self.stream.put(None) # End supervisor
		elif self.tasks[pid].count == 0: # Free own task
			del self.tasks[pid]

	def debug(self): # Function for testing tasks with error handling and without multiprocessing

		self.main.flags = tuple(list(self.main.flags) + ['debug']) # Suppresses terminate message
		return self.main.execute()

	def run(self): # Supervisor process and pool management

		if 'profile' in self.flags:
			from cProfile import Profile
			pr = Profile()
			pr.enable()
		message = True
		interval = 10 if 'timeout' in self.flags or self.root == 'harmonia' else None # Timeout interval
		self.tasks[self.main.pid].result = self.pool.apply_async(self.main.execute) # Start execution of initial module
		while message: # Event listener pattern; runs until null sentinel value sent from initial module
			try:
				message = self.stream.get(timeout = interval)
				if not message:
					break
				if 'supervisor' in self.flags:
					hemera.debug_supervisor(message)
				try:
					getattr(self, message[0])(*message[1:]) # Executes event
				except RuntimeError:
					hemera.debug_error('sophia', 0, 'TASK', ())
			except Empty:
				hemera.debug_error('sophia', 0, 'TIME', ()) # Prints timeout warning but continues
				message = True
		self.pool.close()
		self.pool.join()
		if 'profile' in self.flags:
			pr.disable()
			pr.print_stats(sort = 'cumtime')
		return self.tasks[self.main.pid].result.get()['values']['0']

class task:
	"""
	Base task object for Sophia.
	A task handles synchronous program execution and passes messages to and
	from the supervisor.
	"""
	def __init__(self, processor, flags): # God objects? What is she objecting to?
		
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
		self.properties = aletheia.descriptor() # Final type properties
		self.final = aletheia.descriptor() # Return type of routine

	def execute(self):
		"""
		Target of task.pool.apply_async().
		Executes flags, then launches runtime loop.
		"""
		if 'instructions' in self.flags:
			hemera.debug_instructions(self)
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
			hemera.debug_namespace(self)
		if 'debug' in self.flags:
			return value
		else:
			self.message('terminate')
			return self.state() # Return mutable state to supervisor

	def run(self):
		"""
		Task runtime loop.
		Performs dispatch and executes instructions.
		"""
		debug_task = 'task' in self.flags # Debug runtime loop
		self.caller = None # Reset caller
		while self.path:
			"""
			Prepare instruction, method, and arguments.
			"""
			self.op, cache = self.instructions[self.path], self.cache[self.path]
			if debug_task:
				hemera.debug_task(self)
			self.path = self.path + 1
			if (address := self.op.register): # Instructions
				method, registers = self.values[self.op.name], self.op.args
				args = [self.values[arg] for arg in registers]
			else: # Labels and pseudo-instructions
				if self.op.name == 'BIND':
					address, register = self.op.label[0], self.op.args[0]
					value, signature = self.values[register], self.types[register]
					self.properties.type = self.op.label[1]
					self.values[address] = value
					self.types[address], self.properties = self.complete(self.properties, signature, value), self.types[address] if address in self.types else aletheia.descriptor()
					self.properties.type, self.properties.member, self.properties.length = None, None, None
				continue
			"""
			Multiple dispatch algorithm, with help from Julia:
			https://github.com/JeffBezanson/phdthesis
			Binary search tree yields closest key for method, then key is verified.
			"""
			self.signature = [self.types[arg] for arg in registers]
			if cache is None:
				tree = method.tree.true if registers else method.tree.false # Here's tree
				while tree: # Traverse tree; terminates upon reaching leaf node
					tree = tree.true if (tree.index < self.op.arity) and tree.op(self.signature[tree.index]) else tree.false
				if tree is None:
					self.error('DISP', method.name, self.signature)
					continue
				instance, final, signature = tree.routine, tree.final, tree.signature
				try:
					for i, item in enumerate(self.signature): # Verify type signature
						if item > signature[i]:
							self.error('DISP', method.name, self.signature)
							continue
				except IndexError:
					self.error('DISP', method.name, self.signature)
					continue
			else:
				instance, final, signature = cache.routine, cache.final, cache.signature
			"""
			Execute instruction and update registers.
			"""
			value = instance(self, *args)
			if final.type != '!': # Suppress write
				self.values[address] = value # Hot-swap descriptors; there's always 1 spare in the system
				self.types[address], self.properties = self.complete(self.properties, final, value), self.types[address] if address in self.types else aletheia.descriptor()
				self.properties.type, self.properties.member, self.properties.length = None, None, None
		else:
			return value

	def branch(self, scope = 0, skip = False, move = False): # Universal branch function

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

	def complete(self, descriptor, final, value): # Completes descriptor with properties and inferred type of value
		
		descriptor.type = descriptor.type or final.type or aletheia.infer_type(value)
		descriptor.supertypes = self.values[descriptor.type or 'null'].supertypes
		if 'sequence' in descriptor.supertypes:
			descriptor.member = descriptor.member or final.member or aletheia.infer_member(value)
			descriptor.length = descriptor.length or final.length or len(value)
		descriptor.supermember = self.values[descriptor.member or 'null'].supertypes
		return descriptor

	def state(self): # Get current state of task as subset of __dict__

		return {'name': self.name,
				'values': self.values.copy(),
				'types': self.types.copy(),
				'instructions': self.instructions,
				'path': self.path,
				'op': self.op,
				'caller': self.caller,
				'final': self.final,
				'cache': self.cache}

	def restore(self, state): # Restore previous state of task

		self.__dict__.update(state)

	def prepare(self, namespace, message): # Sets up task for event execution
		
		self.restore(namespace)
		self.path, scope = 0, 0
		while True:
			op, self.path = self.instructions[self.path], self.path + 1
			if not op.register:
				scope = scope - 1 if op.name == 'END' else scope + 1
				if scope == 1 and op.name == 'EVENT':
					name = op.label[0]
					break
		self.values[name], self.types[name] = message, aletheia.descriptor('untyped').describe(self)

	def message(self, instruction = None, *args):
		
		mp.current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def error(self, status, *args): # Error handler
		
		self.properties.type = 'null'
		self.properties.member = None
		self.properties.length = None
		if self.op.register != '0': # Suppresses error for assertions
			if 'suppress' not in self.flags:
				hemera.debug_error(self.name, self.op.line, status, args)
			self.values['0'] = None
			self.path = 0