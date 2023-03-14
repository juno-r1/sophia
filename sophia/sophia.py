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

class runtime: # Base runtime object

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

	def call(self, pid, routine, args):

		routine = task(routine, args, self.flags)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].requests.append(pid) # Submit request for return value

	def future(self, pid, routine, args):
		
		routine = task(routine, args, self.flags)
		self.tasks[routine.pid] = kleio.proxy(routine)
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.future(routine)) # Return reference to process

	def stream(self, pid, routine, args):
		
		routine = task(routine, args, self.flags)
		self.tasks[routine.pid] = kleio.proxy(routine)
		routine.node = routine.start.nodes[0]
		routine.path = [0, 0]
		self.events[routine.pid] = routine # Persistent reference to event
		self.tasks[routine.pid].result = self.pool.apply_async(routine.execute)
		self.tasks[routine.pid].count = self.tasks[routine.pid].count + 1
		self.tasks[pid].references.append(routine.pid) # Mark reference to process
		self.tasks[pid].calls.send(kleio.stream(routine)) # Return reference to process

	def link(self, pid, name, args):
		
		self.future(pid, kadmos.module(name, root = self.root), args)

	def send(self, pid, reference, message):
		
		if isinstance(reference, kleio.stream):
			self.tasks[reference.pid].result.get() # Wait until routine is done with previous message
			namespace = self.tasks[reference.pid].calls.recv() # Get namespace from task
			routine = self.events[reference.pid]
			routine.prepare(namespace, message) # Mutate this version of the task
			self.tasks[reference.pid].result = self.pool.apply_async(routine.execute)
		else:
			self.tasks[reference.pid].messages.send(message)

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

		#if 'profile' in self.flags:
		#	from cProfile import Profile
		#	pr = Profile()
		#	pr.enable()
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
		#if 'profile' in self.flags:
		#	pr.disable()
		#	pr.print_stats(sort = 'tottime')
		return self.tasks[self.main.pid].result.get()

class task:

	def __init__(self, instructions, values, types, flags): # God objects? What is she objecting to?
		
		self.name, self.type = instructions[0].split(' ')[0][1:] if instructions else '', 'untyped'
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		self.flags = flags
		self.internal_values = aletheia.types | mathos.operators | arche.functions
		self.internal_types = {i: 'type' for i in aletheia.types} | {i: 'function' for i in mathos.operators | arche.functions}
		self.values, self.types = values, types
		self.reserved = tuple(i for i in values)
		self.supertypes = aletheia.supertypes
		self.specificity = {k: len(v) for k, v in aletheia.supertypes.items()} # Length of supertypes is equivalent to specificity of subtype
		self.instructions = [i.split(' ') for i in instructions]
		self.path = 1 if instructions else 0 # Does not execute if the parser encountered an error
		self.label, self.address, self.registers = None, None, None

	def execute(self): # Target of run()
		
		if 'instructions' in self.flags:
			hemera.debug_instructions(self)
		if 'profile' in self.flags:
			from cProfile import Profile
			pr = Profile()
			pr.enable()
		debug_task = 'task' in self.flags
		while self.path:
			if debug_task:
				hemera.debug_task(self)
			"""
			Prepare instruction, get arguments and type signature
			"""
			instruction = self.instructions[self.path]
			self.label, self.address, self.registers = instruction[0], instruction[1], instruction[2:]
			self.path = self.path + 1
			if self.label == ';': # Label
				continue
			args = [self] + [self.find(register) for register in self.registers]
			signature = tuple(self.check(register) for register in self.registers)
			length = len(signature)
			"""
			Multiple dispatch algorithm, with help from:
			https://github.com/JeffBezanson/phdthesis
			"""
			if not (method := self.find(self.label)):
				continue
			if not (candidates := [x for x in method.methods if method.lengths[x] == length]): # Remove candidates with mismatching arity
				self.error('DISP', method.name, str(signature))
				continue
			for i, name in enumerate(signature):
				signatures, candidates, max_depth = candidates, [], 0 # Filtering left-to-right search
				for item in signatures:
					if item[i] in self.supertypes[name]: # Check that parameter type is a supertype of x
						candidates.append(item)
						max_depth = max(max_depth, self.specificity[item[i]]) # Only ever increases
				else:
					candidates = [item for item in candidates if self.specificity[item[i]] == max_depth] # Keep only most specific signatures
			if candidates:
				instance, match = method.methods[candidates[0]], candidates[0]
			else:
				self.error('DISP', method.name, str(signature))
				continue
			"""
			Execute instruction, update return registers with return value and type
			"""
			value = instance(*args)
			self.values[self.address] = value
			if self.address[0] in '0123456789':
				self.types[self.address] = arche.infer(value) if method.finals[match] == '*' else method.finals[match]
		if 'profile' in self.flags:
			pr.disable()
			pr.print_stats(sort = 'tottime')
		if 'namespace' in self.flags:
			hemera.debug_namespace(self)
		#self.calls.send((self.values,
		#				  self.types,
		#				  self.supertypes,
		#				  self.reserved)) # Send mutable namespace to supervisor
		self.message('terminate')
		return self.values['0']

	#def prepare(self, namespace, message): # Sets up task for event execution

	#	self.node = self.start.nodes[1]
	#	self.path = [1, 0]
	#	self.values, self.types, self.supertypes, self.reserved = namespace # Update version of task in this process
	#	self.bind(self.start.message.value, message)

	def message(self, instruction = None, *args):
		
		mp.current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def bind(self, name, value, type_name = 'null'): # Creates or updates a name binding in main
		
		if name in self.reserved or name in self.internal_values:
			return self.error('BIND', name)
		self.values[name] = value
		if type_name != 'null':
			self.types[name] = type_name
		elif name not in self.types:
			self.types[name] = 'untyped'
		return value

	def unbind(self, name): # Destroys a name binding in the current namespace

		del self.values[name], self.types[name] # Delete binding if it exists in the namespace

	def find(self, name): # Retrieves a binding's value in the current namespace
		
		if name in self.internal_values:
			return self.internal_values[name]
		elif name in self.values:
			return self.values[name]
		else:
			return self.error('FIND', name)

	def check(self, name, default = 'null'): # Internal function to check if a name has a type bound to it

		if name in self.internal_types:
			return self.internal_types[name]
		elif name in self.types:
			return self.types[name]
		else:
			return default

	def cast(self, value, type_name, known = 'null'): # Checks type of value and returns boolean
		
		if type_name == 'null':
			return value
		type_routine = self.find(type_name)
		stack = [] # Stack of user-defined types, with the requested type at the bottom
		while type_routine.supertype and type_routine.name != known: # Known type optimises by truncating stack
			stack.append(type_routine)
			type_routine = self.find(type_routine.supertype) # Type routine is guaranteed to be a built-in when loop ends, so it checks that before any of the types on the stack
		if type_routine(value) is None: # Check built-in type
			return self.error('CAST', type_routine.name, str(value))
		while stack:
			type_routine = stack.pop()
			if type_routine(self, value) is None:
				return self.error('CAST', type_routine.name, str(value))
		else:
			return value # Return indicates success; cast() raises an exception on failure

	def dispatch(self, method, args): # Performs multiple dispatch on a function
		
		if not method:
			raise TypeError
		signatures = []
		candidates = [x for x in method.methods if len(x) == len(args)] # Remove candidates with mismatching arity
		if not candidates: # No candidate with matching arity
			return None
		for i, name in enumerate(args):
			signatures, candidates, max_depth = candidates, [], 0 # Filtering left-to-right search
			for signature in signatures:
				if signature[i] in self.supertypes[name]: # Check that parameter type is a supertype of x
					candidates.append(signature)
					subtype_depth = len(self.supertypes[signature[i]]) # Length of supertypes is equivalent to specificity of subtype
					max_depth = subtype_depth if subtype_depth > max_depth else max_depth # Only ever increases
			else:
				candidates = [x for x in candidates if len(self.supertypes[x[i]]) == max_depth] # Keep only most specific signature 
		else:
			if candidates:
				return (method.methods[candidates[0]], candidates[0])
			else:
				self.error('DISP', method.name, str(args))
				raise TypeError

	# https://github.com/JeffBezanson/phdthesis

	def error(self, status, *args): # Error handler
		
		if self.address != '0': # Suppresses error for assertions
			if 'suppress' not in self.flags:
				hemera.debug_error(self.name, self.path - 1, status, args)
			self.path = 0 # Immediately end routine