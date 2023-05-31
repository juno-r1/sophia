'''
The Sophia module is the core of the language.
The module defines the runtime environment and task operations.
This is the root module and the only module that the user should need to access.
'''

# ☉ 0.5 20-03-2023

import aletheia, arche, hemera, kadmos, kleio, mathos
import multiprocessing as mp
from os import name as os_name
from queue import Empty

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
			mp.set_start_method('spawn' if os_name == 'nt' else 'fork')
		except RuntimeError:
			pass
		initial = kadmos.module(address, root = root)
		if 'tree' in flags:
			hemera.debug_tree(initial) # Here's tree
		self.instructions, self.values, self.types = kadmos.translator(initial).generate()
		self.root = root
		self.stream = mp.Queue() # Supervisor message stream
		self.pool = mp.Pool(initializer = self.initialise)
		self.main = task(self.instructions, self.values, self.types, flags) # Initial task
		self.tasks = {self.main.pid: kleio.proxy(self.main)} # Proxies of tasks
		self.events = {} # Persistent event tasks
		self.flags = flags

	def initialise(self): # Cheeky way to sneak a queue into a task
	
		mp.current_process().stream = self.stream

	def future(self, pid, routine, args, method, check):
		
		args = self.values | {routine.name: method} | dict(zip(routine.params, args))
		types = self.types | {routine.name: aletheia.infer(routine)} | dict(zip(routine.params, routine.types))
		new = task(routine.instructions, args, types, self.flags)
		self.tasks[new.pid] = kleio.proxy(new)
		if check:
			self.events[new.pid] = new # Persistent reference to event
		self.tasks[new.pid].result = self.pool.apply_async(new.execute)
		self.tasks[new.pid].count = self.tasks[new.pid].count + 1
		self.tasks[pid].references.append(new.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.reference(new, check = check)) # Return reference to process

	def send(self, pid, reference, message):
		
		self.tasks[reference.pid].messages.send(message)

	def update(self, pid, reference, message):
		
		self.tasks[reference.pid].result.get() # Wait until routine is done with previous message
		routine = self.events[reference.pid]
		routine.prepare(self.tasks[reference.pid].state, message, reference.check) # Mutate this version of the task
		self.tasks[reference.pid].result = self.pool.apply_async(routine.execute)

	def resolve(self, pid, reference):

		if self.tasks[reference.pid].result.ready():
			self.tasks[pid].calls.send(self.tasks[reference.pid].result.get())
		else:
			self.tasks[reference.pid].requests.append(pid) # Submit request for return value

	def link(self, pid, name):
		
		linked = kadmos.module(name, root = self.root)
		instructions, values, types = kadmos.translator(linked).generate()
		routine = task(instructions, values, types, self.flags)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.reference(routine)) # Return reference to process

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
			pr.print_stats(sort = 'tottime')
		return self.tasks[self.main.pid].result.get()['values']['0']

class task:
	"""
	Base task object for Sophia.
	A task handles synchronous program execution and passes messages to and
	from the supervisor.
	"""
	def __init__(self, instructions, values, types, flags): # God objects? What is she objecting to?
		
		self.name = instructions[0].label[0] if instructions else ''
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		self.flags = flags
		self.values = aletheia.types | mathos.operators | arche.functions | values
		self.types = {i: 'type' for i in aletheia.types} | {i: 'function' for i in mathos.operators | arche.functions} | {k: (v if v else aletheia.infer(values[k])) for k, v in types.items()}
		self.reserved = tuple(i for i in self.values)
		self.instructions = instructions
		self.path = int(bool(instructions)) # Does not execute if the parser encountered an error
		self.op = instructions[0] # Current instruction
		self.caller = None # Stores the state of the calling routine
		self.override = None # Override flag, for when a method has a different return type to the one declared

	def execute(self): # Target of task.pool.apply_async()
		
		debug_task = 'task' in self.flags
		if 'instructions' in self.flags:
			hemera.debug_instructions(self)
		if 'profile' in self.flags:
			from cProfile import Profile
			pr = Profile()
			pr.enable()
		while self.path:
			"""
			Prepare instruction, get arguments and type signature.
			"""
			self.op = self.instructions[self.path]
			if debug_task:
				hemera.debug_task(self)
			self.path = self.path + 1
			if not self.op.register: # Labels
				continue
			arity = self.op.arity
			args = [self] + [self.find(arg) for arg in self.op.args]
			signature = tuple([self.check(arg) for arg in self.op.args])
			"""
			Multiple dispatch algorithm, with help from Julia:
			https://github.com/JeffBezanson/phdthesis
			Now distilled into 3 extremely stupid list comprehensions!
			"""
			if not (method := self.find(self.op.name)):
				continue
			if not (candidates := [x for x in method.methods if method.arity[x] == arity]): # Remove candidates with mismatching arity
				self.error('DISP', method.name, str(signature))
				continue
			for i, name in enumerate(signature):
				supertypes = self.values[name].supertypes
				candidates = [item for item in candidates if item[i] in supertypes] # Filter for candidates with a matching supertype
				depth = max([self.values[item[i]].specificity for item in candidates], default = 0) # Get the depth of the most specific candidate
				candidates = [item for item in candidates if self.values[item[i]].specificity == depth] # Keep only the most specific signatures
			if candidates:
				match = candidates[0] # Just take the first match it finds, I don't know
				instance = method.methods[match]
			else:
				self.error('DISP', method.name, str(signature))
				continue
			"""
			Execute instruction and update or unbind registers.
			"""
			value = instance(*args)
			if self.override:
				self.values[self.op.register] = value
				self.types[self.op.register], self.override = self.override, None
			elif (final := method.finals[match]) != '.':
				self.values[self.op.register] = value
				self.types[self.op.register] = aletheia.infer(value) if final == '*' else final
		if 'profile' in self.flags:
			pr.disable()
			pr.print_stats(sort = 'tottime')
		if 'namespace' in self.flags:
			hemera.debug_namespace(self)
		self.message('terminate')
		return self.state() # Return mutable state to supervisor

	def find(self, name): # Retrieves a binding's value in the current namespace
		
		return self.values[name] if name in self.values else self.error('FIND', name)

	def check(self, name, default = None): # Internal function to check if a name has a type bound to it
		
		return self.types[name] if name in self.types else aletheia.infer(default)

	def state(self): # Get current state of task as subset of __dict__

		return {'name': self.name,
				'values': self.values.copy(),
				'types': self.types.copy(),
				'reserved': self.reserved,
				'instructions': self.instructions,
				'path': self.path,
				'op': self.op,
				'caller': self.caller}

	def restore(self, state): # Restore previous state of task

		self.__dict__.update(state)

	def prepare(self, namespace, message, check): # Sets up task for event execution
		
		self.restore(namespace)
		self.path = 0
		scope = 0
		while True:
			op, self.path = self.instructions[self.path], self.path + 1
			if not op.register:
				scope = scope - 1 if op.name == 'END' else scope + 1
				if scope == 1 and op.name == 'EVENT':
					name = op.label[0]
					break
		self.values[name], self.types[name] = message, check

	def message(self, instruction = None, *args):
		
		mp.current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def error(self, status, *args): # Error handler
		
		if self.op.register != '0': # Suppresses error for assertions
			if 'suppress' not in self.flags:
				hemera.debug_error(self.name, self.op.line, status, args)
			self.values['0'] = None
			self.path = 0