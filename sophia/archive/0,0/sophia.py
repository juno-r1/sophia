# ☉
# 08/05/2022: Parser implemented (first working version)
# 15/07/2022: Hello world program
# 04/08/2022: Fibonacci program
# 09/08/2022: Basic feature set implemented

import core, operators, hemera

symbols = ['\t', '\n', # Symbols are space-unseparated
           ':', ',', '.',
           '(', '[', '{',
           ')', ']', '}'] # Characters that need to be interpreted as distinct tokens

operator_list = ['+', '-', '*', '/', '^', '%', '~', '&&', '||', '^^', '&', '|',
                 '<=', '>=', '!=', '<', '>', '=', 'in', 'not', 'and', 'or', 'xor']
operator_names = ['add', 'sub', 'mul', 'div', 'exp', 'mod', 'bit_not', 'bit_and', 'bit_or', 'bit_xor', 'intersection', 'union',
                  'lt_eq', 'gt_eq', 'not_eq', 'lt', 'gt', 'eq', 'in_op', 'not_op', 'and_op', 'or_op', 'xor_op']
operator_dict = dict(zip(operator_list, operator_names)) # Dictionary with operator names as keys and operator symbols as values

keywords = {'structure': ['if', 'else', 'while', 'for', 'assert', 'type', 'constraint', 'return', 'import'],
            'keyword': ['is', 'pass', 'continue', 'break']}

binding_power = [['(', ')', '[', ']', '{', '}'], # The left-binding power of a binary operator is expressed by its position in this list
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

def parser(input): # Recursively descends into madness and returns a tree of nodes

    def balanced(tokens): # Takes a string and checks if its parentheses are balanced
        # https://stackoverflow.com/questions/6701853/parentheses-pairing-issue
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
    
    def recurse_split(line): # Takes a line from the stripped input and splits it into tokens

        for i, char in enumerate(line):
            if char in symbols or char in operator_list: # If symbol found, split the token into everything before it, itself, and everything after it
                if i < len(line) - 1 and line[i + 1] in ['=', '&', '|', '^']: # Clumsy hack to make composite operators work
                    output = [line[0:i], char + line[i + 1]] + recurse_split(line[i + 2:])
                elif i > 0 and i < len(line) - 1:
                    try: # Check for decimal point
                        x = int(line[i - 1])
                        y = int(line[i + 1])
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

    def node(id, value, *nodes): # Takes an item from lines and returns a dictionary describing its properties as a token

        return {'id': id,
                'value': value,
                'nodes': [n for n in nodes]} # Since nodes is a tuple

    def literal(value): # Adds literal behaviours to a token

        def nud(lex, peek):

            return token # Gives self as node

        token = node('literal', value)
        token['lbp'] = 0
        token['nud'] = nud
        token['module'] = 'main'

        return token

    def keyword(value): # Adds keyword behaviours to a token

        def nud(lex, peek):

            return token # The same, but can be changed if needed

        token = node('keyword', value)
        token['lbp'] = 0
        token['nud'] = nud

        return token

    def reference(value): # Adds function call / sequence reference behaviours to a token

        def nud(lex, peek): # Basically bypasses this token entirely and implements the LED of the following left bracket

            n = next(lex) # Gets the next token, which is guaranteed to be a left bracket
            next(peek) # Wastes a token
            return n['led'](lex, peek, token) # This token doesn't even *have* a LED, but it's guaranteed to call the LED of the following left bracket

        token = node('reference', value)
        token['lbp'] = 0
        token['nud'] = nud
        token['module'] = 'main'

        return token

    def prefix(value, lbp): # Adds prefix behaviours to a token

        def nud(lex, peek):

            n, next_token = recursive_parse(lex, peek, token['lbp'])
            token['nodes'] = [n]
            return token, next_token

        token = node('prefix', value)
        token['lbp'] = lbp
        token['nud'] = nud
        
        return token

    def infix(value, lbp): # Adds infix behaviours to a token

        def led(lex, peek, left):

            n, next_token = recursive_parse(lex, peek, token['lbp'])
            token['nodes'] = [left, n]
            return token, next_token

        token = node('infix', value)
        token['lbp'] = lbp
        token['led'] = led
        
        return token

    def infix_r(value, lbp): # Adds right-binding infix behaviours to a token

        def led(lex, peek, left):

            n, next_token = recursive_parse(lex, peek, token['lbp'] - 1)
            token['nodes'] = [left, n]
            return token, next_token

        token = node('infix_r', value)
        token['lbp'] = lbp
        token['led'] = led
        
        return token

    def left_bracket(value, lbp): # Adds left-bracket behaviours to a token

        def nud(lex, peek):

            n, next_token = recursive_parse(lex, peek, token['lbp'])
            token['nodes'] = [n]
            try:
                next(lex)
                next_token = next(peek)
            except StopIteration:
                next_token = eol()
            return token, next_token # The bracketed sub-expression as a whole is essentially a literal

        def led(lex, peek, left):

            n, next_token = recursive_parse(lex, peek, token['lbp'])
            token['nodes'] = [left, n]
            next(lex)
            try:
                next_token = next(peek)
            except StopIteration:
                next_token = eol()
            return token, next_token # The name and the bracketed sub-expression as a whole are essentially a literal

        token = node('left_bracket', value)
        token['lbp'] = lbp
        token['nud'] = nud # For normal parentheses
        token['led'] = led # For function calls

        return token

    def right_bracket(value, lbp): # Adds right-bracket behaviours to a token

        def led(lex, peek, left): # If this function is called, something has gone wrong

            raise SyntaxError("I don't know how you caused this error, but you sure did")

        token = node('right_bracket', value)
        token['lbp'] = lbp
        token['led'] = led

        return token

    def eol(): # Creates an end-of-line token

        token = node('eol', None)
        token['lbp'] = -1

        return token

    lines = []

    for line in input:
        i = line.find('//') # Handles comments, except for in strings
        if i == -1: # This conditional wouldn't even be necessary if Python did list slices right
            lines.append(recurse_split(line))
        else:
            lines.append(recurse_split(line[0:i]))
    
    tokens = []
    scopes = []

    for line in lines: # Tokenises each item in lines
        scope = line.count('\t') # Gets scope level from number of tabs
        if line[-1] == '': # Currently bugged to not work when a line contains only tabs
            continue # Skips empty lines
        if not balanced(line):
            raise SyntaxError('Unmatched parentheses')
        tokens.append([])
        scopes.append(scope)
        for n, token in enumerate(line[scope:]): # Skips tabs
            if token in symbols or token in operator_list:                
                if token in ['(', '[', '{']:
                    tokens[-1].append(left_bracket(token, 1))
                elif token in [')', ']', '}']:
                    tokens[-1].append(right_bracket(token, 1))
                elif len(tokens[-1]) > 0 and (tokens[-1][-1]['id'] in ['literal', 'right_bracket']): # If the preceding token is a literal (if the current token is an infix):
                    for i, level in enumerate(binding_power): # Gets the left-binding power of the operator
                        if token in level:
                            if token == '^':
                                tokens[-1].append(infix_r(token, i + 1))
                            else:
                                tokens[-1].append(infix(token, i + 1))
                            break
                    else:
                        tokens[-1].append(keyword(token))
                else:
                    tokens[-1].append(prefix(token, len(binding_power) + 1)) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
            else:
                for key in keywords: # Checks if the current item is a reserved keyword or symbol
                    if token in keywords[key]: # And much more compactly than using a massive if-elif-else statement, at that 
                        tokens[-1].append(keyword(token))
                        break
                else:
                    if len(tokens[-1]) > 0 and tokens[-1][-1]['id'] == 'literal': # Checks for type
                        type_value = tokens[-1].pop()['value']
                    else:
                        type_value = 'untyped'
                    if n < len(line[scope:]) - 1 and line[scope:][n + 1] in ['(', '[']:
                        tokens[-1].append(reference(token))
                    else:
                        tokens[-1].append(literal(token))
                    tokens[-1][-1]['type'] = type_value

    def statement(tokens): # Recursive descent parser

        def function_definition(tokens):

            if len(tokens) > 4: # Checks for parameters
                return node('function_definition', None, tokens[0], parameters(tokens[1:]))
            else:
                return node('function_definition', None, tokens[0], parameters(None))

        def assignment(tokens):

            return node('assignment', None, tokens[0], expression(tokens[2:])) # Typed assignments are always handed by typed_statement(), so this is fine

        def binding(tokens):

            return node('binding', None, tokens[0], tokens[2]) # Typed bindings are always handed by typed_statement(), so this is fine

        def if_statement(tokens):

            return node('if_statement', None, expression(tokens[1:-1]))

        def while_statement(tokens):

            return node('while_statement', None, expression(tokens[1:-1]))

        def for_statement(tokens):

            return node('for_statement', None, tokens[1], expression(tokens[3:-1]))

        def assert_statement(tokens):

            if tokens[1]['value'] == 'type':
                return node('assert_type_statement', None, tokens[2], expression(tokens[4:-1]))
            else:
                return node('assert_statement', None, expression(tokens[1:-1]))

        def type_statement(tokens):

            if len(tokens) > 3: # Naive check for subtyping
                return node('subtype_statement', None, tokens[1], tokens[3])
            else:
                return node('type_statement', None, tokens[1])
    
        def constraint_statement(tokens):

            return node('constraint_statement', None, expression(tokens[2:]))

        def else_statement(tokens):

            if len(tokens) > 2:
                return node('else_statement', None, statement(tokens[1:]))
            else:
                return node('else_final', None)

        def return_statement(tokens):

            return node('return_statement', None, expression(tokens[1:]))

        def import_statement(tokens):

            values = [token['value'] for token in tokens]

            if 'as' in values:
                return node('import_as_statement', None, import_statement(tokens[0:-2]), tokens[-1])
            elif 'from' in values:
                return node('import_from_statement', None, import_statement(tokens[0:-2]), tokens[-1])
            else:
                return node('import_statement', None, expression(tokens[1:]))

        def parameters(tokens):

            if tokens:
                return node('parameters', None, expression(tokens[1:-2])['nodes'][0])
            else:
                return node('parameters', None, literal(None))

        if tokens[0]['value'] in keywords['structure']:
            statement_id = tokens[0]['value'] + '_statement'
            return locals()[statement_id](tokens) # Cheeky little hack that makes a node for whatever structure keyword is specified
        elif tokens[0]['value'] in keywords['keyword']:
            return tokens[0] # Keywords will get special handling later
        elif tokens[-1]['value'] == ':':
            return function_definition(tokens)
        elif len(tokens) > 1 and tokens[1]['value'] == ':':
            return assignment(tokens)
        elif len(tokens) > 1 and tokens[1]['value'] == 'is':
            return binding(tokens)
        else: # Only necessary because of function calls with side effects
            return expression(tokens)

    def expression(tokens):
        
        lex = iter(tokens)
        peek = iter(tokens)
        next(peek)
        tree, end = recursive_parse(lex, peek, 0)
        return node('expression', None, tree)
        
        # https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
        # https://abarker.github.io/typped/pratt_parsing_intro.html
        # https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
        # https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

    def recursive_parse(lex, peek, lbp): # Pratt parser for expressions - takes an iterator, its current token, and the left-binding power

        try:
            token = next(lex)
            next_token = next(peek) # Gets next token from the iterator, if it exists
        except StopIteration: # Detects end of expression
            return token, eol() # End-of-line token

        try: # NUD has variable number of return values
            left, next_token = token['nud'](lex, peek) # Executes null denotation of current token
        except ValueError: # Is this a lazy substitute for an if-clause? Yes, but it works
            left = token['nud'](lex, peek)

        while lbp < next_token['lbp']:
            try:
                token = next(lex)
                next_token = next(peek)
                left, next_token = token['led'](lex, peek, left) # Executes left denotation of current token
            except StopIteration: # Detects end of expression
                return left, eol() # End-of-line token

        return left, next_token # Preserves state of next_token for higher-level calls

    parsed_lines = [statement(line) for line in tokens]
    main = node('main', None) # Highest-level node of program
    main['scope'] = 0

    for i, line in enumerate(parsed_lines):
        line['scope'] = scopes[i] + 1 # Since main has scope 0

    def scope_parse(main, lines): # Groups lines based on scope

        head = main # Head token
        last = main # Last line

        for i, line in enumerate(lines):
            if line['scope'] > head['scope'] + 1: # If entering scope
                head = last # Last line becomes the head node
                head['nodes'].append(line)
            elif line['scope'] < head['scope'] + 1: # If exiting scope
                if line['scope'] > 1: # If statement is in local scope:
                    for n in lines[i::-1]: # Find the last line containing the current line in its direct scope, searching backwards from the current line
                        if n['scope'] == line['scope'] - 1: # If such a line is found:
                            head = n # Make it the head node
                            break
                else: # If statement is in global scope:
                    head = main # Resets head to main node
                head['nodes'].append(line)
            else: # If line in direct scope of head
                head['nodes'].append(line)
            last = line
        else:
            return main

    return scope_parse(main, parsed_lines)

def interpreter(tree): # Takes a tree of nodes from parser() and returns an intermediate representation of it

    def namespace(args): # Record containing name bindings; optionally takes tuples of name, type, and value

        return {'names': [arg[0] for arg in args], # Binding of names to references
                'types': {arg[0]: arg[1] for arg in args}, # Binding of references to types
                'values': {arg[0]: arg[2] for arg in args}, # Binding of references to values
                'private': len(args)} # Cheat way to determine if a binding is reserved

    main = [namespace(core.initialise())] # Initialises the main namespace with built-in functions
    op_record = operators.initialise()
    alias = dict()

    def bind(address, value): # Creates or updates a name binding in main

        name = address['value']
        type_value = address['type']

        try: # Checks for aliasing
            name = alias[name]
        except KeyError:
            pass

        try:
            i = main[-1]['names'].index(name) # Get the index of the name in the namespace
        except ValueError:
            i = -1 # ...or -1 if not found

        if i >= 0 and i < main[-1]['private']: # If the name is in the private range of the namespace, or is a loop index:
            raise NameError('Cannot bind to reserved name')
        else: # Otherwise, either create or update a name binding
            if name not in main[-1]['names']:
                main[-1]['names'].append(name)
            main[-1]['types'][name] = type_value
            main[-1]['values'][name] = value

    def unbind(name): # Destroys a name binding in main

        try:
            i = main[-1]['names'].index(name) # Get the index of the name in the namespace
        except ValueError:
            raise NameError('Undefined name: ' + name)

        del main[-1]['names'][i]
        del main[-1]['types'][name]
        del main[-1]['values'][name]

    def find(name, module = main): # Retrieves a name binding from a module
        
        try: # Checks for aliasing
            name = alias[name]
        except KeyError:
            pass

        for scope in module[::-1]: # Searches module in reverse order
            if name in scope['names']: # If the name is in the module:
                return scope['values'][name] # Return the bound value
        else:
            raise NameError('Undefined name: ' + name)

    def call(value): # Handles function calls
        
        tail = True
        overwrite = False

        while tail:
            name = value['nodes'][0]['value'] # Gets the function name
            module_name = value['nodes'][0]['module'] # Gets the module name
            if module_name == 'main':
                body = find(name) # Gets the function node
            else:
                module_value = find(module_name) # Gets the module
                body = find(name, module_value) # Gets the function node from the named module
            args = evaluate(value['nodes'][1]) # Gets the given arguments as a tuple
            if not isinstance(args, tuple): # Type correction
                args = tuple([args])
            if isinstance(body, tuple): # If user-defined:
                type_value = body[0]['nodes'][0]['type'] # Gets the function type
                params = parameters(body[0]['nodes'][1]) # Gets the function parameters
                if not isinstance(params, list): # Type correction
                    params = [params]
                definition = namespace([[name, type_value, body]] + [[param['value'], param['type'], None] for param in params]) # Constructs a new copy of the namespace each time the function is called
                if overwrite:
                    main[-1] = definition # Overwrite the local namespace
                else:
                    main.append(definition) # Add the namespace to main
                if len(params) == len(args):
                    for i, param in enumerate(params): # Update parameters with arguments
                        main[-1]['values'][param['value']] = args[i] # Can't use bind() because of private range
                else:
                    raise SyntaxError('Expected {0} arguments; received {1}'.format(str(len(params)), str(len(args))))
                return_value = execute(body[0]['nodes'][2:]) # Execute the function body
                if isinstance(return_value, dict) and return_value['tail']: # Replace with actual type check later
                    value = return_value
                    overwrite = True
                else:
                    main.pop() # Delete the namespace
                    return return_value
            else: # If built-in:
                try:
                    tail = False
                    return body(*args) # Since body is a Python function in this case
                except TypeError:
                    raise TypeError(name + ' is not a function')
            
    def parameters(statement):

        if statement['id'] == 'parameters': # Yeah, sure, this works
            return parameters(statement['nodes'][0])

        if statement['nodes']: # Constructs a flat list from comma-separated values without calling evaluate() and dealing with cast()
            x = parameters(statement['nodes'][0])
            y = parameters(statement['nodes'][1])
        else:
            return statement
        if isinstance(x, list):
            items = [*x, y]
        else:
            items = [x, y]
        return items

    def execute(node): # Takes the module tree and executes it

        def function_definition(statement):

            name = statement['nodes'][0]
            bind(name, tuple([statement])) # Binds a reference to the function node as a tuple, since tuples aren't an accessible type in Sophia

        def assignment(statement):

            name = statement['nodes'][0] # Not necessary to call evaluate()
            value = expression(statement['nodes'][1])
            bind(name, value)

        def binding(statement):
            
            name = statement['nodes'][0] # Not necessary to call evaluate()
            value = statement['nodes'][1]['value'] # Not necessary to call evaluate()
            if value not in main[-1]['names']:
                raise NameError('Alias out of scope')
            else:
                bind(name, None) # Creates an empty name binding
                alias[name['value']] = value # Creates an alias

        def if_statement(statement):

            condition = expression(statement['nodes'][0])
            if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
                raise ValueError('Condition must evaluate to Boolean')
            if condition is True:
                statement['branch'] = True
                return execute(statement['nodes'][1:])

        def while_statement(statement):

            condition = expression(statement['nodes'][0])
            if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
                raise ValueError('Condition must evaluate to Boolean')
            while condition:
                return_value = execute(statement['nodes'][1:])
                condition = expression(statement['nodes'][0])
            else:
                return return_value

        def for_statement(statement):

            index = statement['nodes'][0]
            index['type'] = 'reserved'
            sequence = iter(expression(statement['nodes'][1]))
            try:
                while True: # Loop until the iterator is exhausted
                    bind(index, next(sequence)) # Binds the next value of the sequence to the loop index
                    return_value = execute(statement['nodes'][2:])
            except StopIteration:
                unbind(index['value']) # Unbinds the index
                return return_value

        def else_statement(statement):

            inner = statement['nodes'][0]
            condition = expression(inner['nodes'][0])
            if condition:
                statement['branch'] = True
                return execute(statement['nodes'][1:])

        def else_final(statement):

            return execute(statement['nodes'])

        def return_statement(statement):
            
            head_node = statement['nodes'][0]['nodes'][0] # Get head node
            if head_node['value'] == '(' and len(head_node['nodes']) > 1: # If function call:
                head_node['tail'] = True
                return head_node # Facilitates tail call optimisation
            else:
                head_node['tail'] = False
                return expression(statement['nodes'][0])

        def import_statement(statement):
            
            names = parameters(statement['nodes'][0]['nodes'][0])
            if not isinstance(names, list): # Type correction
                names = [names]
            for name in names:
                with open(name['value'] + '.sophia', 'r') as f:
                    input = f.read().splitlines()
                tree = parser(input) # Here's tree
                space = interpreter(tree) # Gets namespace
                name['type'] = 'module' # Updates type for name binding
                bind(name, space) # Create a name binding for the module

        def expression(statement):

            return evaluate(statement['nodes'][0])

        branch = False # Branch register
        return_value = None # Return register

        if isinstance(node, list): # If passed a list of nodes
            statements = node
        else: # If passed a single node
            statements = [node]

        for statement in statements:
            statement['branch'] = False
            if not branch:
                return_value = locals()[statement['id']](statement)
            if return_value is not None or statement['id'] == 'return_statement':
                return return_value
            if statement['id'] != 'else_statement':
                branch = statement['branch'] # Sets up the branch for the next statement
        else:
            return None # Allows execute() to return the value from the last statement by default

    def evaluate(node): # Takes an expression, evaluates it, and returns the evaluated value

        def cast(literal):

            try:
                value = float(literal['value']) # Attempt to cast to float
                if value % 1 == 0:
                    value = int(value) # Attempt to cast to int
            except ValueError:
                if literal['value'][0] in ['"', "'"]:
                    value = literal['value'][1:-1] # Interpret as string
                elif literal['value'] == 'true':
                    value = True
                elif literal['value'] == 'false':
                    value = False
                else:
                    value = None # If literal cannot be parsed as a literal
            if value is not None:
                return value # Return literal value
            else:
                if 'module' in literal:
                    if literal['module'] == 'main':
                        return find(literal['value']) # Retrieve data from reference
                    else:
                        return find(literal['value'], find(literal['module'])) # Retrieve data from reference
                else:
                    return find(literal['value']) # Retrieve data from reference

        def index(value): # Retrieves a value from a sequence
            
            name = evaluate(value['nodes'][0])
            subscript = evaluate(value['nodes'][1])
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

        def sequence(value): # Constructs a sequence

            items = evaluate(value['nodes'][0])
            if not isinstance(items, list):
                items = [items]
            if isinstance(items[0], tuple): # If items is a record
                return {item[0]: item[1] for item in items}
            else: # If items is a list
                if items and items != [None]: # Handles empty lists
                    return items
                else:
                    return []

        def meta(value): # Evaluates a meta-statement

            string = evaluate(value['nodes'][0]).split('\n') # Evaluates string
            tree = parser(string) # Run-time parser stage
            return execute(tree['nodes'][0]) # Run-time execution stage

        if node['id'] in ['literal', 'reference']: # Terminal nodes
            return cast(node)
        elif node['id'] == 'left_bracket': # Bracketed expressions
            if node['value'] == '(':
                if node['nodes'][0]['id'] == 'reference': # Function calls
                    return call(node)
                else: # Arithmetic brackets
                    return evaluate(node['nodes'][0])
            elif node['value'] == '[': # Sequence expressions
                if node['nodes'][0]['id'] == 'reference': # Sequence index
                    return index(node)
                else: # Sequence constructor
                    return sequence(node)
            elif node['value'] == '{': # Meta-statement
                return meta(node)
        elif node['value'] == '.': # Sorts out the dot operator
            module_name = node['nodes'][0]['value']
            value = node['nodes'][1]
            if value['id'] == 'literal':
                value['module'] = module_name # Necessary to handle imports
            elif value['id'] == 'left_bracket':
                value['nodes'][0]['module'] = module_name # Necessary to handle imports
            return evaluate(value) # Continue as normal
        elif node['value'] == ',': # Sorts out comma-separated parameters by returning them as a tuple
            x = evaluate(node['nodes'][0])
            y = evaluate(node['nodes'][1])
            if isinstance(x, list) and node['nodes'][0]['value'] != '[': # Handles nested lists
                items = x + [y]
            else:
                items = [x, y]
            return items
        elif node['value'] == ':': # Sorts out list slices and key-item pairs by returning them as a list
            x = evaluate(node['nodes'][0])
            y = evaluate(node['nodes'][1])
            if isinstance(x, tuple):
                items = (*x, y)
            else:
                items = (x, y)
            return items
        elif node['id'] == 'prefix': # Unary operators
            op = 'unary_' + operator_dict[node['value']] # Gets the name of the operator
            x = evaluate(node['nodes'][0])
            return op_record[op](x)
        elif node['id'] in ['infix', 'infix_r']: # Binary operators
            op = operator_dict[node['value']] # Gets the name of the operator
            x = evaluate(node['nodes'][0])
            y = evaluate(node['nodes'][1])
            return op_record[op](x, y) # Uses the operator named in op

    execute(tree['nodes'])
    for i in range(main[0]['private'] - 1, -1, -1): # Unbinds built-ins in reverse order to avoid index issues
        unbind(main[0]['names'][i])
    return main # Returns main to facilitate imports

def run(file): # Runs the interpreter

    with open(file, 'r') as f:
        input = f.read().splitlines()

    tree = parser(input) # Here's tree
    hemera.debug_tree(tree)
    print('===')
    interpreter(tree)

run('main.sophia')