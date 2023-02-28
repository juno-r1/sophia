'''
The Sophia module is the core of the language.
The module defines the runtime environment and core language constructs.
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
		self.root = root
		self.stream = mp.Queue() # Supervisor message stream
		self.pool = mp.Pool(initializer = self.initialise)
		self.main = task(initial.generate(), [], flags) # Initial task
		self.tasks = {self.main.pid: kleio.proxy(self.main)} # Proxies of tasks
		self.events = {} # Persistent event tasks
		self.flags = flags
		if 'tree' in self.flags:
			hemera.debug_tree(initial) # Here's tree

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

	def __init__(self, instructions, args, flags): # God objects? What is she objecting to?
		
		self.name, self.type, params, types = instructions[0]
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		self.flags = flags
		self.built_in_values = aletheia.types | mathos.operators | arche.functions
		self.built_in_types = {i: 'type' for i in aletheia.types} | {i: 'operator' for i in mathos.operators} | {i: 'function' for i in arche.functions}
		self.values = dict(zip(params, args)) # Dict of values for faster access
		self.types = dict(zip(params, types)) # Dict of types for correct typing
		self.supertypes = aletheia.supertypes
		self.reserved = params.copy() # List of reserved names in the current namespace
		self.data = [] # Unfortunately, a stack
		self.type_data = [] # Unfortunately, another stack
		self.instructions = instructions
		self.path = 1 if self.instructions else 0 # Ends early if no instructions
		self.sentinel = None # Return value of task

	def execute(self): # Target of run()
		
		if 'instructions' in self.flags:
			hemera.debug_instructions(self)
		debug_task = 'task' in self.flags
		while self.path:
			if debug_task:
				hemera.debug_task(self)
			instruction, index = self.instructions[self.path]
			self.path = self.path + 1
			if index == -1: # Push to stacks
				self.data.append(instruction)
				self.type_data.append(self.infer(instruction)) # Infer type
			else: # Dispatch and execute instruction
				if index == 0:
					args, signature = [], ()
				else:
					self.data, args = self.data[0:-index], self.data[-index:]
					self.type_data, signature = self.type_data[0:-index], tuple(self.type_data[-index:])
				method = self.find(instruction)
				instance, match = self.dispatch(method, signature)
				if not instance:
					continue
				if method.name[0] == '!': # Mutator methods
					instance(self, *args) if args else instance(self)
				elif method.name[0] == '.': # Internal methods
					value = instance(self, *args) if args else instance(self)
					self.data.append(value) # Inlining this straight up does not work for no reason at all
					self.type_data.append(self.infer(value) if method.finals[match] == '*' else method.finals[match]) # Infer type from value if needed
				else: # User-accessible methods
					value = instance(*args) if args else instance()
					self.data.append(value)
					self.type_data.append(self.infer(value) if method.finals[match] == '*' else method.finals[match])
		if 'namespace' in self.flags:
			hemera.debug_namespace(self)
		#self.calls.send((self.values,
		#				 self.types,
		#				 self.supertypes,
		#				 self.reserved)) # Send mutable namespace to supervisor
		self.message('terminate')
		return self.sentinel

	def prepare(self, namespace, message): # Sets up task for event execution

		self.node = self.start.nodes[1]
		self.path = [1, 0]
		self.values, self.types, self.supertypes, self.reserved = namespace # Update version of task in this process
		self.bind(self.start.message.value, message)

	def message(self, instruction = None, *args):
		
		mp.current_process().stream.put([instruction, self.pid] + list(args) if instruction else None)

	def bind(self, name, value, type_name = None): # Creates or updates a name binding in main
		
		if name in self.reserved or name in self.built_in_values: # Quicker and easier to do it here
			return self.error('BIND', name)
		self.values[name] = value # Mutate namespace
		if type_name:
			self.types[name] = type_name
		elif name not in self.types:
			self.types[name] = 'untyped'
		return value

	def unbind(self, name): # Destroys a name binding in the current namespace

		del self.values[name], self.types[name] # Delete binding if it exists in the namespace

	def find(self, name): # Retrieves a binding's value in the current namespace
		
		if name in self.built_in_values:
			return self.built_in_values[name]
		elif name in self.values:
			return self.values[name]
		else:
			return self.error('FIND', name)

	def check(self, name, default = None): # Internal function to check if a name has a type bound to it

		if name in self.built_in_types:
			return self.built_in_types[name]
		elif name in self.types:
			return self.types[name]
		else:
			return default

	def cast(self, value, type_name, known = None): # Checks type of value and returns boolean
		
		if not type_name:
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

	def infer(self, value): # Infers type of value

		name = type(value).__name__
		if name in arche.names:
			return arche.names[name]
		else:
			return 'untyped'

	def dispatch(self, method, args): # Performs multiple dispatch on a function
		
		signatures = []
		candidates = [x for x in method.methods.keys() if len(x) == len(args)] # Remove candidates with mismatching arity
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
			if len(candidates) == 1:
				return (method.methods[candidates[0]], candidates[0])
			else:
				self.error('DISP', method.name, str(args))
				return (None, None)

	# https://github.com/JeffBezanson/phdthesis

	def branch(self, increment, decrement, initial = 1):

		branch = initial
		while branch:
			name = self.instructions[self.path][0]
			if name == increment:
				branch = branch + 1
			elif name == decrement:
				branch = branch - 1
			self.path = self.path + 1

	def error(self, status, *args): # Error handler
		
		if not False: # Suppresses error for assertion
			if 'suppress' not in self.flags:
				hemera.debug_error(self.name, self.path - 1, status, args)
			self.path = 0 # Immediately end routine