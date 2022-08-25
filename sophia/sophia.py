# ☉
# 08/05/2022: Parser implemented (first working version)
# 15/07/2022: Hello world program
# 04/08/2022: Fibonacci program
# 09/08/2022: Basic feature set implemented (0.0)
# 16/08/2022: Basic feature set re-implemented (0.1)
# 20/08/2022: Type system implemented (0.1)

import core, hemera

class definition: # Name binding object

    def __init__(self, name, value, type_value = 'untyped', reserved = False):

        self.name = name
        self.value = value
        self.type = type_value
        self.reserved = reserved

class node: # Base node object

    def __init__(self, value, *nodes):

        self.value = value
        self.nodes = [n for n in nodes] # Since nodes is a tuple
        self.module = None

class Continue(Exception): # Handles the continue keyword

    pass

class runtime(node): # Runtime object contains runtime information and is the top level of the syntax tree

    def __init__(self, file_name): # God objects? What is she objecting to?

        super().__init__(file_name.split('.')[0]) # Sets name of file as value

        self.symbols = ['\t', '\n', # Symbols are space-unseparated
                        ':', ',', '.', '!',
                        '(', '[', '{',
                        ')', ']', '}'] # Characters that need to be interpreted as distinct tokens

        self.operator_list = ['+', '-', '*', '/', '^', '%', '~', '&&', '||', '^^', '&', '|', # Standard operators, and also !
                              '<=', '>=', '!=', '<', '>', '=', 'in', 'not', 'and', 'or', 'xor'] # Logic operators
        self.operator_names = ['add', 'sub', 'mul', 'div', 'exp', 'mod', 'bit_not', 'bit_and', 'bit_or', 'bit_xor', 'intersection', 'union',
                               'lt_eq', 'gt_eq', 'not_eq', 'lt', 'gt', 'eq', 'in_op', 'not_op', 'and_op', 'or_op', 'xor_op']
        self.operator_dict = dict(zip(self.operator_list, self.operator_names)) # Dictionary with operator names as keys and operator symbols as values

        self.structure_tokens = ['if', 'else', 'while', 'for', 'assert', 'type', 'constraint', 'return', 'import']
        self.keyword_tokens = ['is', 'extends', 'pass', 'continue', 'break']

        self.binding_power = [['(', ')', '[', ']', '{', '}'], # The left-binding power of a binary operator is expressed by its position in this list
                              [','],
                              [':'],
                              ['or'],
                              ['and'],
                              ['=', '!='],
                              ['<', '>', '<=', '>='],
                              ['&', '|'],
                              ['+', '-'],
                              ['*', '/', '%'],
                              ['^'],
                              ['.']]

        with open(file_name, 'r') as f: # Binds file data to runtime object
            self.file_data = f.read().splitlines()

        self.namespace = [[definition(*item) for item in core.init_types()] + [definition(*item) for item in core.init_functions()]] # Initialises main with built-in types and functions
        self.builtins = len(self.namespace[0]) - 1
        self.op_record = core.init_operators()
        self.module = None
        self.branch = False
        self.return_value = None

    def run(self, do_import = False): # Runs the module

        tree = self.parse() # Here's tree
        hemera.debug_tree(tree) # Uncomment for parse tree debug information
        print('===')
        self.execute(do_import)
        for item in self.namespace[0][self.builtins::-1]: # Unbinds built-ins in reverse order to not cause problems with the loop
            self.unbind(item.name)
        if not do_import: # Uncomment for namespace debug information
            hemera.debug_namespace(self)
        return self # Returns runtime object to facilitate imports

    def parse(self, meta_node = None): # Recursively descends into madness and returns a tree of nodes

        lines = []

        if meta_node: # Handles the meta-statement
            input_string = meta_node.nodes[0].evaluate().split('\n')
        else:
            input_string = self.file_data

        for line in input_string:
            i = line.find('//') # Handles comments, except for in strings
            if i == -1: # This conditional wouldn't even be necessary if Python did list slices right
                lines.append(recurse_split(line))
            else:
                lines.append(recurse_split(line[0:i]))
    
        tokens = []
        scopes = []

        for line in lines: # Tokenises each item in lines
            scope = line.count('\t') # Gets scope level from number of tabs
            if line[-1] == '' or line[scope:] == []:
                continue # Skips empty lines
            if not balanced(line):
                raise SyntaxError('Unmatched parentheses')
            tokens.append([])
            scopes.append(scope)
            for n, token in enumerate(line[scope:]): # Skips tabs
                if token in self.symbols or token in self.operator_list:                
                    if token in ['(', '[', '{']:
                        tokens[-1].append(left_bracket(token, 1))
                        if line[scope:][n + 1] in [')', ']', '}']:
                            tokens[-1].append(keyword(None))
                    elif token in [')', ']', '}']:
                        tokens[-1].append(right_bracket(token, 1))
                    elif len(tokens[-1]) > 0 and isinstance(tokens[-1][-1], (literal, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
                        for i, level in enumerate(self.binding_power): # Gets the left-binding power of the operator
                            if token in level:
                                if token in ['^', '.', ',', ':']:
                                    tokens[-1].append(infix_r(token, i + 1))
                                else:
                                    tokens[-1].append(infix(token, i + 1))
                                break
                        else:
                            tokens[-1].append(keyword(token))
                    else:
                        tokens[-1].append(prefix(token, len(self.binding_power) + 1)) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
                else:
                    if token in self.structure_tokens or token in self.keyword_tokens: # And much more compactly than using a massive if-elif-else statement, at that 
                        tokens[-1].append(keyword(token))
                    else:
                        if len(tokens[-1]) > 0 and isinstance(tokens[-1][-1], literal): # Checks for type
                            type_value = tokens[-1].pop().value
                        else:
                            type_value = 'untyped'
                        if n < len(line[scope:]) - 1 and line[scope:][n + 1] in ['(', '[']:
                            tokens[-1].append(reference(token))
                        else:
                            tokens[-1].append(literal(token))
                        setattr(tokens[-1][-1], 'type', type_value) # Sets type

        parsed_lines = []

        for line in tokens:
            if line[0].value in self.structure_tokens:
                statement_id = line[0].value + '_statement'
                x = eval(statement_id + '(line)') # Cheeky little hack that makes a node for whatever structure keyword is specified
            elif line[0].value in self.keyword_tokens:
                x = line[0] # Keywords will get special handling later
            elif line[-1].value == ':':
                x = function_definition(line)
            elif len(line) > 1 and line[1].value == ':':
                x = assignment(line)
            elif len(line) > 1 and line[1].value == 'is':
                x = binding(line)
            else: # Only necessary because of function calls with side effects
                x = expression(line)
            parsed_lines.append(x)

        if meta_node:
            main = meta_node
        else:
            main = self
        head = main # Head token
        last = main # Last line
        setattr(main, 'scope', 0)

        for i, line in enumerate(parsed_lines):
            setattr(line, 'scope', scopes[i] + 1) # Since main has scope 0

        for i, line in enumerate(parsed_lines): # Groups lines based on scope
            if line.scope > head.scope + 1: # If entering scope
                head = last # Last line becomes the head node
                head.nodes.append(line)
            elif line.scope < head.scope + 1: # If exiting scope
                if line.scope > 1: # If statement is in local scope:
                    for n in parsed_lines[i::-1]: # Find the last line containing the current line in its direct scope, searching backwards from the current line
                        if n.scope == line.scope - 1: # If such a line is found:
                            head = n # Make it the head node
                            break
                else: # If statement is in global scope:
                    head = main # Resets head to main node
                head.nodes.append(line)
            else: # If line in direct scope of head
                head.nodes.append(line)
            last = line
        else:
            return main

    def execute(self, do_import = False): # Takes the module tree and executes it

        if do_import:
            for statement in self.nodes:
                if isinstance(statement, (type_statement, function_definition)): # Only does type definitions and function definitions
                    statement.execute()
        else:
            for statement in self.nodes:
                statement.execute()

    def bind(self, name, value, type_value = None): # Creates or updates a name binding in main

        for item in self.namespace[-1]: # Finds and updates a name binding
            if item.name == name:
                if item.reserved: # If the name is bound, or is a loop index:
                    raise NameError('Cannot bind to reserved name')
                else:
                    if isinstance(item.value, definition): # If alias:
                        item.value.value = value # Binding can have little a indirection. As a treat
                    else:
                        item.value = value
                    if type_value != 'untyped':
                        item.type = type_value
                break
        else: # Creates a new name binding
            if type_value:
                self.namespace[-1].append(definition(name, value, type_value))
            else:
                self.namespace[-1].append(definition(name, value))

    def unbind(self, name): # Destroys a name binding in main

        for i, item in enumerate(self.namespace[-1]): # Finds and destroys a name binding
            if item.name == name:
                index = i
                break
        else:
            raise NameError('Undefined name: ' + name)

        del self.namespace[-1][index] # Destroy the binding outside of the loop to prevent issues with the loop

    def find(self, name): # Retrieves a name binding from a module

        for space in self.namespace[::-1]: # Searches module in reverse order
            for item in space:
                if item.name == name: # If the name is in the module:
                    return item # Return the binding
        else:
            raise NameError('Undefined name: ' + name)

    def cast(self, value, type_value): # Checks type for value and returns boolean
                
        type_node = self.find(type_value).value
        stack = []
        while isinstance(type_node, type_statement): # Get all supertypes for type
            stack.append(type_node)
            type_node = main.find(type_node.supertype).value
        else:
            stack.append(type_node) # Guaranteed to be a built_in
        while stack: # Check type down the entire tree
            type_node = stack.pop()
            if isinstance(type_node, type_statement): # If user-defined:
                self.namespace.append([definition(type_value, value, type_value, reserved = True)]) # Bind special variable in a new scope
                for item in type_node.nodes[1:]: # Executing the node is the same as checking the value's type
                    item.execute()
                else:
                    return_value = value
                    self.namespace.pop() # Destroy scope
            else: # If built-in:
                return_value = type_node(value) # Corrects type for built-ins
        else:
            return return_value # Return indicates success; cast() raises an exception on failure

class literal(node): # Adds literal behaviours to a node

    def __init__(self, value):

        super().__init__(value)
        self.lbp = 0

    def nud(self, lex):

        return self # Gives self as node

    def evaluate(self): # Terminal nodes

        try:
            value = float(self.value) # Attempt to cast to float
            if value % 1 == 0:
                return int(value) # Attempt to cast to int
            else:
                return value
        except ValueError:
            if self.value[0] in ['"', "'"]:
                return self.value[1:-1] # Interpret as string
            elif self.value == 'true':
                return True
            elif self.value == 'false':
                return False
            elif self.value == 'null':
                return None
            else: # If reference:
                if main.module:
                    return main.module.find(self.value).value # Retrieve data from module
                else:
                    return main.find(self.value).value # Retrieve data from reference


class keyword(node): # Adds keyword behaviours to a node

    def __init__(self, value):

        super().__init__(value)
        self.lbp = 0

    def nud(self, lex):

        return self

    def execute(self):

        if self.value == 'continue':
            raise Continue
        elif self.value == 'break':
            raise StopIteration

class reference(node): # Adds function call / sequence reference behaviours to a node

    def __init__(self, value):

        super().__init__(value)
        self.lbp = 0

    def nud(self, lex): # Basically bypasses this token entirely and implements the LED of the following left bracket

        lex.use() # Gets the next token, which is guaranteed to be a left bracket
        return lex.token.led(lex, self) # This token doesn't even *have* a LED, but it's guaranteed to call the LED of the following left bracket

    def evaluate(self):

        if main.module:
            return main.module.find(self.value).value # Retrieve data from module
        else:
            return main.find(self.value).value # Retrieve data from reference

class prefix(node): # Adds prefix behaviours to a node

    def __init__(self, value, lbp):

        super().__init__(value)
        self.lbp = lbp

    def nud(self, lex):

        n, next_token = recursive_parse(lex, self.lbp)
        self.nodes = [n]
        return self, next_token

    def evaluate(self): # Unary operators

        op = 'unary_' + main.operator_dict[self.value] # Gets the name of the operator
        x = self.nodes[0].evaluate()
        return main.op_record[op](x)

class infix(node): # Adds infix behaviours to a node

    def __init__(self, value, lbp):

        super().__init__(value)
        self.lbp = lbp

    def led(self, lex, left):

        n, next_token = recursive_parse(lex, self.lbp)
        self.nodes = [left, n]
        return self, next_token

    def evaluate(self):
        
        op = main.operator_dict[self.value] # Gets the name of the operator
        x = self.nodes[0].evaluate()
        y = self.nodes[1].evaluate()
        return main.op_record[op](x, y) # Uses the operator named in op

class infix_r(node): # Adds right-binding infix behaviours to a node

    def __init__(self, value, lbp):

        super().__init__(value)
        self.lbp = lbp

    def led(self, lex, left):

        n, next_token = recursive_parse(lex, self.lbp - 1)
        self.nodes = [left, n]
        return self, next_token

    def evaluate(self):

        if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a list
            left = self
            right = []
            while left.nodes:
                try:
                    x = int(left.nodes[0].value)
                    right.append(x)
                except ValueError:
                    right.append(left.nodes[0].value)
                left = left.nodes[1]
            else:
                right.append(left.evaluate())
                return tuple(right)
        elif self.value == ',': # Sorts out comma-separated parameters by returning them as a tuple
            left = self
            right = []
            while left.nodes and left.value == ',':
                right.append(left.nodes[0].evaluate())
                left = left.nodes[1]
            else:
                right.append(left.evaluate())
                return right
        elif self.value == '.': # Sorts out the dot operator
            name = self.nodes[0].value
            left = main.find(name) # Gets binding for name
            right = self.nodes[1]
            if left.type == 'module': # If module:
                main.module = left.value
                return right.evaluate()
            else: # If type operation:
                x = infix_r(',', None)
                x.nodes = [literal(right.nodes[0].value), right.nodes[1]]
                right.nodes[1] = x # Inserts the bound value into the syntax tree as an argument of the function call
                right.nodes[1].nodes[0].value = self.nodes[0].value # Guarantees reference type for name
                if right.nodes[1].nodes[1].value is None:
                    right.nodes[1] = right.nodes[1].nodes[0]
                main.module = main.find(left.type).value
                return right.evaluate()
        else: # Binary operators
            op = main.operator_dict[self.value] # Gets the name of the operator
            x = self.nodes[0].evaluate()
            y = self.nodes[1].evaluate()
            return main.op_record[op](x, y) # Uses the operator named in op

class left_bracket(node): # Adds left-bracket behaviours to a node

    def __init__(self, value, lbp):

        super().__init__(value)
        self.lbp = lbp

    def nud(self, lex): # For normal parentheses

        n, next_token = recursive_parse(lex, self.lbp)
        self.nodes = [n]
        try:
            lex.use()
            return self, lex.peek # The bracketed sub-expression as a whole is essentially a literal
        except StopIteration:
            return self, eol()

    def led(self, lex, left): # For function calls

        n, next_token = recursive_parse(lex, self.lbp)
        self.nodes = [left, n]
        try:
            lex.use()
            return self, lex.peek # The bracketed sub-expression as a whole is essentially a literal
        except StopIteration:
            return self, eol()

    def evaluate(self):

        if self.value == '(':
            if isinstance(self.nodes[0], reference): # Function calls
                return self.call()
            else: # Arithmetic brackets
                return self.nodes[0].evaluate()
        elif self.value == '[': # Sequence expressions
            if isinstance(self.nodes[0], reference): # Sequence index
                return self.index()
            else: # Sequence constructor
                return self.sequence()
        elif self.value == '{': # Meta-statement
            return self.meta()

    def call(self): # Handles function calls; revealed to me in a dream by hbomberguy
        
        tail = True
        overwrite = False
        main.return_value = None

        while tail:
            name = self.nodes[0].value # Gets the function name
            if main.module and isinstance(main.module, (runtime, type_statement)):
                body = main.module.find(name).value # Gets the function body
                main.module = None # Reset module
            else:
                body = main.find(name).value # Gets the function body
            if isinstance(self.nodes[1], keyword): # If no arguments:
                args = None
            else:
                args = self.nodes[1].evaluate() # Gets the given arguments
                if not isinstance(args, tuple): # Type correction
                    if isinstance(args, list): # Very tiresome type correction, at that
                        args = tuple(args)
                    else:
                        args = tuple([args])
            if isinstance(body, function_definition): # If user-defined:
                type_value = body.nodes[0].type # Gets the function type
                params = body.nodes[1].execute() # Gets the function parameters
                if isinstance(params[0], keyword): # Naïve check for no parameters
                    params = None
                if params:
                    space = [definition(name, body, type_value, True)] + [definition(param.value, None, param.type, True) for param in params] # Constructs a new copy of the namespace each time the function is called
                else:
                    space = [definition(name, body, type_value, True)]
                if overwrite:
                    main.namespace[-1] = space # Overwrite the local namespace
                else:
                    main.namespace.append(space) # Add the namespace to main
                if (not params and not args) or (params and args and len(params) == len(args)):
                    for i, item in enumerate(main.namespace[-1][1:]): # Update parameters with arguments
                        item.value = main.cast(args[i], item.type) # Tests arguments for type
                else:
                    if params:
                        x = len(params)
                    else:
                        x = 0
                    if args:
                        y = len(args)
                    else:
                        y = 0
                    raise SyntaxError('Expected {0} arguments; received {1}'.format(x, y))
                for item in body.nodes[2:]:
                    item.execute() # Execute the function body
                if isinstance(main.return_value, left_bracket) and main.return_value.tail:
                    self = main.return_value
                    overwrite = True
                else:
                    main.namespace.pop() # Delete scope
                    return main.cast(main.return_value, type_value) # Test return value for declared type
            else: # If built-in:
                try:
                    tail = False
                    if args:
                        return body(*args) # Since body is a Python function in this case
                    else:
                        return body()
                except TypeError:
                    raise TypeError(name + ' is not a function')

    def index(self): # Retrieves a value from a sequence
            
        name = self.nodes[0].evaluate()
        subscript = self.nodes[1].evaluate()
        if not isinstance(subscript, list):
            subscript = [subscript]
        for i in subscript: # Iteratively accesses the sequence
            if not isinstance(i, tuple):
                i = tuple([i])
            if isinstance(i[0], str):
                if i[0] not in name:
                    raise KeyError('Key not in record: ' + i[0]) # Can't be KeyError because the try-except clause eats those
            else:
                if i[0] < -1 * len(name) or i[0] >= len(name): # If out of bounds:
                    raise IndexError('Index out of bounds')
                if len(i) > 1:
                    if i[1] < -1 * len(name) or i[1] >= len(name): # If out of bounds:
                        raise IndexError('Index out of bounds')
            if len(i) > 1:
                if len(i) == 2:
                    if i[1] == -1: # Python uses exclusive index; Sophia uses inclusive index
                        name = name[i[0]:]
                    else:
                        name = name[i[0]:i[1] + 1]
                elif len(i) == 3:
                    if i[1] == -1:
                        name = name[i[0]::i[2]]
                    else:
                        name = name[i[0]:i[1] + 1:i[2]]
                else:
                    raise SyntaxError('Too many indices in slice')
            else:
                name = name[i[0]]
        return name # Return the accessed value

    def sequence(self): # Constructs a sequence

        items = self.nodes[0].evaluate()
        if not isinstance(items, list):
            items = [items]
        if isinstance(items[0], tuple): # If items is a record
            return {item[0]: item[1] for item in items}
        else: # If items is a list
            if items and items != [None]: # Handles empty lists
                return items
            else:
                return []

    def meta(self): # Evaluates a meta-statement

        main.parse(self) # Run-time parser stage
        for item in self.nodes[1:]:
            return_value = item.execute() # Run-time execution stage
        self.nodes = [self.nodes[0]] # Erase tree
        return return_value

class right_bracket(node): # Adds right-bracket behaviours to a node

    def __init__(self, value, lbp):

        super().__init__(value)
        self.lbp = lbp

    def led(self, lex, left): # If this function is called, something has gone wrong

        raise SyntaxError("You should not be seeing this")

class eol(node): # Creates an end-of-line node

    def __init__(self):

        super().__init__(None)
        self.lbp = -1

class type_statement(node):

    def __init__(self, tokens):
        
        super().__init__(None, tokens[1]) # Type
        if len(tokens) > 3: # Naive check for subtyping
            self.supertype = tokens[3].value # Supertype
        else:
            self.supertype = None
        self.subtypes = []
        self.namespace = []

    def execute(self):

        name = self.nodes[0].value
        for item in self.nodes: # Bind type operations to type node
            if isinstance(item, function_definition):
                self.namespace.append(definition(item.nodes[0].value, item, item.nodes[0].type, reserved = True))
        if main.module:
            main.module.bind(name, self, 'type') # Creates an empty binding to manage scope
        else:
            main.bind(name, self, 'type')

    def find(self, name):

        for binding in self.namespace: # Searches namespace
            if binding.name == name: # If the name is in the namespace:
                return binding # Return the binding
        else:
            raise NameError('Undefined name: ' + name)

class function_definition(node):

    def __init__(self, tokens):

        if len(tokens) > 4: # Checks for parameters
            super().__init__(None, tokens[0], parameters(tokens[1:]))
        else:
            super().__init__(None, tokens[0], parameters(None))

    def execute(self):

        name = self.nodes[0].value
        type_value = self.nodes[0].type
        if main.module:
            main.module.bind(name, self, type_value) # Binds the function node
        else:
            main.bind(name, self, type_value)

class assignment(node):

    def __init__(self, tokens):

        super().__init__(None, tokens[0], expression(tokens[2:])) # Typed assignments are always handed by typed_statement(), so this is fine

    def execute(self):

        name = self.nodes[0].value
        value = self.nodes[1].execute()
        type_value = self.nodes[0].type
        value = main.cast(value, type_value)
        main.bind(name, value, type_value)

class binding(node):

    def __init__(self, tokens):

        super().__init__(None, tokens[0], tokens[2])

    def execute(self):
            
        name = self.nodes[0].value
        type_value = self.nodes[0].type
        for item in main.namespace[-1]: # Check scope for binding, since find() doesn't
            if item.name == self.nodes[1].value:
                if isinstance(item.value, definition):
                    raise NameError('Cannot chain aliases')
                else:
                    main.cast(item.value, type_value)
                    main.bind(name, item, type_value) # Creates a binding referencing another binding
                    break
        else:
            raise NameError('Alias out of scope')

class if_statement(node):

    def __init__(self, tokens):

        super().__init__(None, expression(tokens[1:-1]))

    def execute(self):

        condition = self.nodes[0].execute()
        if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
            raise ValueError('Condition must evaluate to boolean')
        if condition is True:
            for item in self.nodes[1:]:
                return_value = item.execute()
            else:
                main.branch = True
                return return_value

class while_statement(node):

    def __init__(self, tokens):

        super().__init__(None, expression(tokens[1:-1]))

    def execute(self):

        condition = self.nodes[0].execute()
        if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
            raise ValueError('Condition must evaluate to Boolean')
        return_value = None
        try:
            while condition:
                try:
                    for item in self.nodes[1:]:
                        return_value = item.execute()
                    condition = self.nodes[0].execute()
                except Continue: # Continue
                    continue
            else:
                return return_value
        except StopIteration: # Break
            return return_value

class for_statement(node):

    def __init__(self, tokens):

        super().__init__(None, tokens[1], expression(tokens[3:-1]))

    def execute(self):

        index = self.nodes[0]
        sequence = iter(self.nodes[1].execute())
        main.bind(index.value, None, 'untyped')
        return_value = None
        try:
            while True: # Loop until the iterator is exhausted
                main.bind(index.value, next(sequence), 'untyped') # Binds the next value of the sequence to the loop index
                try:
                    for item in self.nodes[2:]:
                        return_value = item.execute()
                except Continue: # Continue
                    continue
        except StopIteration: # Break
            main.unbind(index.value) # Unbinds the index
            return return_value

class assert_statement(node):

    def __init__(self, tokens):

        if tokens[1].type == 'untyped':
            super().__init__(None, tokens[1]) # Assert
            self.typed = False
        else:
            super().__init__(None, tokens[1]) # Assert type
            self.typed = True

    def execute(self):

        if self.typed:
            try:
                binding = main.find(self.nodes[0].value)
                value = binding.value
                binding_type = binding.type
                assert_type = self.nodes[0].type
                value = main.cast(value, assert_type)
            except TypeError:
                main.namespace.pop() # Cleans up from cast()
                main.branch = False
                return None
            for space in main.namespace[::-1]: # Searches module in reverse order
                for item in space:
                    if item.name == self.nodes[0].value: # If the name is in the module:
                        item.type = assert_type # Change the type of the binding
                        for item in self.nodes[1:]:
                            return_value = item.execute()
                        else:
                            main.branch = True
                            item.type = binding_type
                            return return_value
        else:
            pass
    
class constraint_statement(node):

    def __init__(self, tokens):

        super().__init__(None)

    def execute(self):

        for constraint in self.nodes:
            value = constraint.execute()
            if value is not True and value is not False:
                raise ValueError('Constraint must evaluate to boolean')
            if value is False:
                raise TypeError('Constraint failed')

class else_statement(node):

    def __init__(self, tokens):

        if len(tokens) > 2:
            statement_id = tokens[1].value + '_statement'
            super().__init__(None, eval(statement_id + '(tokens[1:])')) # Else statement
            self.final = False
        else:
            super().__init__(None) # Final else
            self.final = True

    def execute(self): # Else statement
        
        if not main.branch:
            if self.final:
                for item in self.nodes:
                    return_value = item.execute()
                return return_value
            else:
                inner = self.nodes[0]
                inner.nodes.extend(self.nodes[1:]) # Reassign nodes to inner statement
                return_value = inner.execute()
                return return_value
        if self.final:
            main.branch = False

class return_statement(node):

    def __init__(self, tokens):

        super().__init__(None, expression(tokens[1:]))

    def execute(self):
            
        head_node = self.nodes[0].nodes[0] # Get head node
        if head_node.value == '(' and len(head_node.nodes) > 1: # If function call:
            setattr(head_node, 'tail', True)
            main.return_value = head_node # Facilitates tail call optimisation
        else:
            setattr(head_node, 'tail', False)
            main.return_value = self.nodes[0].execute()

class import_statement(node):

    def __init__(self, tokens):

        super().__init__(None, *tokens[1::2]) # Allows multiple imports

    def execute(self):

        for item in self.nodes:
            main.module = runtime(item.value + '.sophia')
            main.module.run(do_import = True)
            main.bind(item.value, main.module, 'module')
            main.module = None

class parameters(node):

    def __init__(self, tokens):

        super().__init__(None, expression(tokens[1:-2]).nodes[0])

    def execute(self):
        
        left = self.nodes[0]
        right = []
        while left.nodes:
            right.append(left.nodes[0])
            left = left.nodes[1]
        else:
            right.append(left)
            return right

class expression(node):

    def __init__(self, tokens):
        
        lex = lex_construct(tokens)
        tree, end = recursive_parse(lex, 0)
        super().__init__(None, tree)

    def execute(self):

        return self.nodes[0].evaluate()
        
    # https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
    # https://abarker.github.io/typped/pratt_parsing_intro.html
    # https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
    # https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

class lex_construct: # Lex object to get around not being able to peek the next value of an iterator

    def __init__(self, tokens):

        self.lexes = [iter(tokens), iter(tokens)]
        self.token = None
        self.peek = next(self.lexes[1])

    def use(self): # Gets the next tokens

        self.token = next(self.lexes[0])
        self.peek = next(self.lexes[1])

def recursive_parse(lex, lbp): # Pratt parser for expressions - takes an iterator, its current token, and the left-binding power

    try:
        lex.use() # Gets next token from the iterator, if it exists
    except StopIteration: # Detects end of expression
        return lex.token, eol() # End-of-line token

    try: # NUD has variable number of return values
        left, next_token = lex.token.nud(lex) # Executes null denotation of current token
    except TypeError: # Is this a lazy substitute for an if-clause? Yes, but it works
        left, next_token = lex.token.nud(lex), None

    while lbp < lex.peek.lbp:
        try:
            lex.use()
            left, next_token = lex.token.led(lex, left) # Executes left denotation of current token
        except StopIteration: # Detects end of expression
            return left, eol() # End-of-line token

    return left, next_token # Preserves state of next_token for higher-level calls

def balanced(tokens): # Takes a string and checks if its parentheses are balanced

    iparens = iter('(){}[]') # Iterable list of parentheses
    parens = dict(zip(iparens, iparens)) # Dictionary of parentheses: key is opening parenthesis, value is closing parenthesis
    closing = parens.values() # Gets all closing parentheses from dictionary
    stack = [] # Guess

    for token in tokens:
        char = parens.get(token, None)
        if char: # If character is an opening parenthesis:
            stack.append(char) # Add to stack
        elif token in closing: # If character is a closing parenthesis:
            if not stack or token != stack.pop(): # If the stack is empty or c doesn't match the item popped off the stack:
                return False # Parentheses are unbalanced
        
    return not stack # Interprets stack as a boolean, where an empty stack is falsy

    # https://stackoverflow.com/questions/6701853/parentheses-pairing-issue

def recurse_split(line): # Takes a line from the stripped input and splits it into tokens

    for i, char in enumerate(line):
        if char in main.symbols or char in main.operator_list: # If symbol found, split the token into everything before it, itself, and everything after it
            if i < len(line) - 1 and line[i + 1] in ['=', '&', '|', '^']: # Clumsy hack to make composite operators work
                output = [line[0:i], char + line[i + 1]] + recurse_split(line[i + 2:])
            elif i > 0 and i < len(line) - 1:
                try: # Check for decimal point
                    x = int(line[i - 1])
                    y = int(line[i + 1])
                    z = float(line[i - 1:i + 2]) # Naïve check for decimal point
                    output = [line[i - 1:i + 2]] + recurse_split(line[i + 2:])
                except ValueError:
                    output = [line[0:i], char] + recurse_split(line[i + 1:])
            else:
                output = [line[0:i], char] + recurse_split(line[i + 1:])
        elif char in ["'", '"']:
            j = line[i + 1:].index(char) + 1 # Finds matching quote
            output = [line[0:i], line[i:j + 1]] + recurse_split(line[j + 1:])
        elif char == ' ':
            output = [line[0:i]] + recurse_split(line[i + 1:])
        else:
            continue # Avoids referencing output when it doesn't exist
        while '' in output:
            output.remove('') # Strip empty strings
        return output
    else:
        return [line]

main = runtime('main.sophia')
main.run()