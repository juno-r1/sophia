supertypes = {
	'untyped': ('untyped',),
	'number': ('number', 'untyped'),
	'positive': ('positive', 'number', 'untyped'),
	'string': ('string', 'untyped'),
}

class method:

	def __init__(self, supertypes):

		self.supertypes = supertypes # Reference to type hierarchy
		self.methods = {}

	def register(self, method, signature): # Overwrites duplicate signatures
		
		self.methods[signature] = method # Function

	def dispatch(self, args):
		
		signatures = []
		candidates = [x for x in self.methods.keys() if len(x) == len(args)] # Remove candidates with mismatching arity
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
			return self.methods[candidates[0]] if len(candidates) == 1 else None

new = method(supertypes)

new.register(lambda: print('1!'), ('integer',))
new.register(lambda: print('!!!'), ('untyped', 'number'))
new.register(lambda: print('???'), ('number', 'untyped'))
new.register(lambda: print('!?'), ('number', 'sequence'))
new.register(lambda: print('...'), ('integer', 'number'))

new.dispatch(('integer', 'number'))()