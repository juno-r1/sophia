'''
The Sophia module is the core of the language.
The module defines the runtime environment and task operations.
This is the root module and the only module that the user should need to access.
'''

# ☉ 0.4 11-02-2023

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

	def call(self, pid, routine, args, method): # Pass in method for recursion support

		args = self.values | ({routine.name: method} if method else {}) | dict(zip(routine.params, args))
		types = self.types | ({routine.name: arche.infer(routine)} if method else {}) | dict(zip(routine.params, routine.types))
		routine = task(routine.instructions, args, types, self.flags, check = routine.type)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].requests.append(pid) # Submit request for return value

	def future(self, pid, routine, args, method):
		
		args = self.values | ({routine.name: method} if method else {}) | dict(zip(routine.params, args))
		types = self.types | ({routine.name: arche.infer(routine)} if method else {}) | dict(zip(routine.params, routine.types))
		routine = task(routine.instructions, args, types, self.flags, check = routine.type)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.reference(routine)) # Return reference to process

	def event(self, pid, routine, args, method):
		
		args = self.values | ({routine.name: method} if method else {}) | dict(zip(routine.params, args))
		types = self.types | ({routine.name: arche.infer(routine)} if method else {}) | dict(zip(routine.params, routine.types))
		type_name = routine.check
		routine = task(routine.instructions, args, types, self.flags, check = routine.type)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.events[routine.pid] = routine # Persistent reference to event
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.reference(routine, check = type_name)) # Return reference to process

	def link(self, pid, name, args):
		
		self.future(pid, kadmos.module(name, root = self.root), args)

	def send(self, pid, reference, message):
		
		self.tasks[reference.pid].messages.send(message)

	def update(self, pid, reference, message):

		self.tasks[reference.pid].result.get() # Wait until routine is done with previous message
		namespace = self.tasks[reference.pid].calls.recv() # Get namespace from task
		routine = self.events[reference.pid]
		routine.prepare(namespace, message, reference.check) # Mutate this version of the task
		self.tasks[reference.pid].result = self.pool.apply_async(routine.execute)

	def resolve(self, pid, reference):

		if self.tasks[reference.pid].result.ready():
			self.tasks[pid].calls.send(self.tasks[reference.pid].result.get())
		else:
			self.tasks[reference.pid].requests.append(pid) # Submit request for return value

	def terminate(self, pid):

		value = self.tasks[pid].result.get()
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
				getattr(self, message[0])(*message[1:]) # Executes event
			except Empty:
				message = True
				hemera.debug_error('sophia', 0, 'TIME', ()) # Prints timeout warning but continues
		self.pool.close()
		self.pool.join()
		if 'profile' in self.flags:
			pr.disable()
			pr.print_stats(sort = 'tottime')
		return self.tasks[self.main.pid].result.get()

class task:
	"""
	Base task object for Sophia.
	A task handles synchronous program execution and passes messages to and
	from the supervisor.
	"""
	def __init__(self, instructions, values, types, flags, check = 'untyped'): # God objects? What is she objecting to?
		
		self.name = instructions[0].split(' ')[2] if instructions else ''
		self.type = check
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		self.flags = flags
		self.internal_values = aletheia.types | mathos.operators | arche.functions
		self.internal_types = {i: 'type' for i in aletheia.types} | {i: 'function' for i in mathos.operators | arche.functions}
		self.values, self.types = values, {k: (v if v in aletheia.supertypes else arche.infer(values[k])) for k, v in types.items()}
		self.reserved = tuple(i for i in values)
		self.supertypes = aletheia.supertypes
		self.specificity = aletheia.specificity
		self.instructions = [i.split(' ') for i in instructions]
		self.arity = [0 if i[0] == ';' else (len(i) - 2) for i in self.instructions]
		self.path = 1 if instructions else 0 # Does not execute if the parser encountered an error
		self.label, self.address, self.registers = None, None, None
		self.unbind = False # Unbind flag
		self.override = None # Override flag, for when a method has a different return type to the one declared

	def execute(self): # Target of task.pool.apply_async()
		
		debug_task = 'task' in self.flags
		if 'instructions' in self.flags:
			hemera.debug_instructions(self)
		#if 'profile' in self.flags:
		#	from cProfile import Profile
		#	pr = Profile()
		#	pr.enable()
		while self.path:
			if debug_task:
				hemera.debug_task(self)
			"""
			Prepare instruction, get arguments and type signature.
			"""
			instruction, arity = self.instructions[self.path], self.arity[self.path]
			self.label, self.address, self.registers = instruction[0], instruction[1], instruction[2:]
			self.path = self.path + 1
			if self.label == ';': # Label
				continue
			args = [self] + [self.find(register) for register in self.registers]
			signature = tuple([self.check(register) for register in self.registers])
			"""
			Multiple dispatch algorithm, with help from Julia:
			https://github.com/JeffBezanson/phdthesis
			Now distilled into 3 extremely stupid list comprehensions!
			"""
			if not (method := self.find(self.label)):
				continue
			if not (candidates := [x for x in method.methods if method.arity[x] == arity]): # Remove candidates with mismatching arity
				self.error('DISP', method.name, str(signature))
				continue
			for i, name in enumerate(signature):
				candidates = [item for item in candidates if item[i] in self.supertypes[name]] # Filter for candidates with a matching supertype
				depth = max([self.specificity[item[i]] for item in candidates], default = 0) # Get the depth of the most specific candidate
				candidates = [item for item in candidates if self.specificity[item[i]] == depth] # Keep only the most specific signatures
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
			if self.unbind:
				del self.values[self.address], self.types[self.address]
				self.unbind = False
			elif self.override:
				self.values[self.address] = value
				self.types[self.address], self.override = self.override, None
			elif (final := method.finals[match]) != '.':
				self.values[self.address] = value
				self.types[self.address] = arche.infer(value) if final == '*' else final
		#if 'profile' in self.flags:
		#	pr.disable()
		#	pr.print_stats(sort = 'tottime')
		if 'namespace' in self.flags:
			hemera.debug_namespace(self)
		self.calls.send((self.values,
						 self.types,
						 self.supertypes,
						 self.specificity,
						 self.reserved)) # Send mutable state to supervisor
		self.message('terminate')
		return self.values['0']

	def prepare(self, namespace, message, check): # Sets up task for event execution

		name = self.instructions[0][3]
		while True: # Skip initial
			label = self.instructions[self.path]
			if label[0] == ';' and int(label[1]) <= 2 and label[2] == '.end':
				break
			self.path = self.path + 1
		self.values, self.types, self.supertypes, self.specificity, self.reserved = namespace
		self.bind(name, message, check)

	def bind(self, name, value, type_name = 'null'): # Creates or updates a name binding in main
		
		if name in self.reserved or name in self.internal_values:
			return self.error('BIND', name)
		self.values[name] = value
		if type_name != 'null':
			self.types[name] = type_name
		elif name not in self.types:
			self.types[name] = 'untyped'
		return value

	def find(self, name): # Retrieves a binding's value in the current namespace
		
		if name in self.internal_values:
			return self.internal_values[name]
		elif name in self.values:
			return self.values[name]
		else:
			return self.error('FIND', name)

	def check(self, name, default = None): # Internal function to check if a name has a type bound to it

		if name in self.internal_types:
			return self.internal_types[name]
		elif name in self.types:
			return self.types[name]
		else:
			return arche.infer(default)

	def cast(self, value, type_name, known = 'null'): # Checks type of value and returns boolean
		
		if type_name == 'null':
			return value
		type_routine = self.find(type_name)
		stack = [] # Stack of user-defined types, with the requested type at the bottom
		while type_routine.supertype and type_routine.name != known: # Known type optimises by truncating stack
			stack.append(type_routine)
			type_routine = self.find(type_routine.supertype)
		if type_routine(value) is None: # Check built-in type
			return self.error('CAST', type_routine.name, str(value))
		while stack:
			type_routine = stack.pop()
			if type_routine(self, value) is None:
				return self.error('CAST', type_routine.name, str(value))
		else:
			return value # Return indicates success; cast() raises an exception on failure

	def message(self, instruction = None, *args):
		
		mp.current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def error(self, status, *args): # Error handler
		
		if self.address != '0': # Suppresses error for assertions
			if 'suppress' not in self.flags:
				hemera.debug_error(self.name, self.path - 1, status, args)
			self.path = 0