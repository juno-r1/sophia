# ☉ 0.6.1 30-09-2023

import multiprocessing as mp
import os
from queue import Empty
from typing import Any

from . import hemera, kadmos, metis
from .datatypes import aletheia, iris
from .task import task

class runtime:
	"""
	Base runtime environment for Sophia.
	The runtime environment is the supervisor for the tasks created by a
	running program. It implements a pool for task scheduling and handles
	message passing by acting as an intermediary between running tasks.
	"""
	def __init__(
		self,
		address: str,
		*flags: tuple[str, ...],
		root: str = 'user'
		) -> None:
		"""
		Set MP context and read the source file.
		"""
		mp.freeze_support()
		try:
			mp.set_start_method('spawn' if os.name == 'nt' else 'fork')
		except RuntimeError:
			pass
		with open('{0}/{1}'.format(root, address), 'r') as f:
			source = f.read() # Binds file data to runtime object
		try: # Yes, the handler can fault if it's given unknown flags
			self.handler = hemera.handler(source, flags)
		except SystemExit:
			self.handler = hemera.handler(source, ())
			self.handler.lock = True
			return
		try:
			"""
			Compile stage. Yields a processor object containing optimised instructions.
			"""
			parser = kadmos.parser(self.handler, address.split('.')[0])
			instructions, namespace = parser.parse(source)
			processor = metis.processor(self.handler, instructions, namespace).analyse()
			"""
			Build the supervisor. Main task is initialised and awaiting execution.
			"""
			self.root = root
			self.stream = mp.Queue() # Supervisor message stream
			self.pool = None # Don't initialise just yet
			self.main = task(processor) # Initial task
			self.tasks = {self.main.pid: iris.proxy(self.main)} # Proxies of tasks
			self.events = {} # Persistent event tasks
		except SystemExit: # Catches any compile-time error
			self.handler.lock = True # Lock runtime

	def initialise(self) -> None: # Cheeky way to sneak a queue into a task
	
		mp.current_process().stream = self.stream

	def future(
		self,
		pid: int,
		method: aletheia.method,
		values: dict,
		types: dict
		) -> None:
		
		processor = metis.processor(self.handler, method.instructions, values, types)
		new = task(processor)
		self.tasks[new.pid] = iris.proxy(new)
		if isinstance(method, aletheia.event_method):
			self.events[new.pid] = new # Persistent reference to event
		self.tasks[new.pid].result = self.pool.apply_async(new.execute)
		self.tasks[new.pid].count = self.tasks[new.pid].count + 1
		self.tasks[pid].references.append(new.pid) # Mark reference to process
		self.tasks[pid].calls.send( # Return reference to process
			iris.reference(method.name, new.pid, method.final, readable = True, writeable = True)
		)

	def send(
		self,
		pid: int,
		reference: iris.reference,
		message: Any
		) -> None:

		if reference.pid == 1 or reference.pid == 2: # Standard streams
			self.handler.write(reference, message)
		elif reference.pid in self.events: # Update event
			self.tasks[reference.pid].state = state = self.tasks[reference.pid].result.get() # Check event is finished
			routine = self.events[reference.pid]
			routine.prepare(state, message) # Mutate this version of the task
			self.tasks[reference.pid].result = self.pool.apply_async(routine.execute)
		else:
			self.tasks[reference.pid].messages.send(message)

	def resolve(
		self,
		pid: int,
		reference: iris.reference) -> None:
		
		if reference.pid == 0: # Standard streams
			self.tasks[pid].calls.send(self.handler.read(reference))
		elif self.tasks[reference.pid].result.ready():
			self.tasks[pid].calls.send(self.tasks[reference.pid].result.get())
		else:
			self.tasks[reference.pid].requests.append(pid) # Submit request for return value

	def read(
		self,
		pid: int,
		message: str) -> None:
		"""
		Multiprocessing disables input for all child processes,
		so it has to be handled by the supervisor.
		"""
		self.tasks[pid].calls.send(self.handler.read(iris.std_stdin, message))

	def link(
		self,
		pid: int,
		address: str
		) -> None:
		
		with open('{0}/{1}'.format(self.root, address), 'r') as f:
			source = f.read() # Binds file data to runtime object
		parser = kadmos.parser(self.handler, address.split('.')[0])
		instructions, namespace = parser.parse(source)
		processor = metis.processor(self.handler, instructions, namespace).analyse()
		new = task(processor)
		self.tasks[new.pid] = iris.proxy(new)
		self.tasks[new.pid].result = self.pool.apply_async(new.execute)
		self.tasks[new.pid].count = self.tasks[new.pid].count + 1
		self.tasks[pid].references.append(new.pid) # Mark reference to process
		self.tasks[pid].calls.send( # Return reference to process
			iris.reference(new.name, new.pid, aletheia.typedef(aletheia.std_any), readable = True, writeable = True)
		)

	def terminate(
		self,
		pid: int
		) -> None:
		
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

	def debug(self) -> Any:
		"""
		Test environment with error handling and without multiprocessing.
		Significantly faster than using run() with the pool open.
		"""
		if self.handler.lock:
			return
		self.main.handler.flags = tuple(list(self.main.handler.flags) + ['debug']) # Suppresses terminate message
		return self.main.execute()

	def run(self) -> Any:
		"""
		Default runtime environment. Enables multiprocessing.
		"""
		if self.handler.lock:
			return
		message = True
		interval = 10 if 'timeout' in self.handler.flags or self.root == 'harmonia' else None # Timeout interval
		self.pool = mp.Pool(initializer = self.initialise)
		try:
			self.tasks[self.main.pid].result = self.pool.apply_async(self.main.execute) # Start execution of initial module
			while message: # Event listener; runs until null sentinel value sent from the termination of main
				try:
					message = self.stream.get(timeout = interval)
					if not message:
						break
					if 'supervisor' in self.handler.flags:
						self.handler.debug_supervisor(message)
					try:
						getattr(self, message.instruction)(message.pid, *message.args)
					except RuntimeError:
						self.handler.warn() # Prints task warning
				except Empty:
					self.handler.timeout() # Prints timeout warning
					message = True
		except SystemExit:
			self.handler.lock = True
		finally:
			self.pool.close()
			self.pool.join()
		return self.tasks[self.main.pid].result.get()['values']['0']