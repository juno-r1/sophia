import sophia

def namespace(*args): # Literally just a dictionary

    return {arg: None for arg in args}

def push(x):

    stack.append(x)

def call(name): # Revealed to me in a dream by hbomberguy

    args = []
    args.append(stack.pop())
    while args[-1] != name:
        args.append(stack.pop())
    else:
        scope = main.keys()[-1]
        main[name] = main[scope][name] # Creates new local namespace from function definition
        parameters = main[name].keys() # Contains the function data last, but will never be reached 
        for i, arg in enumerate(args):
            main[name][parameters[i]]['data'] = args[i] # Assigns arguments to parameters
        else:
            [execute(line) for line in main[name][name]] # Function data stored in key of the same name as the function so as to prevent unintentional access
        del main[name] # Collect namespace when no longer needed

def bind(): # Creates a name binding for a namespace

    name = stack.pop()
    expression = stack.pop()
    scope = main.keys()[-1]
    main[scope][name] = {'data': expression, # Binds to most local scope
                         'type': 'null', # Default type is null
                         'access': True} # Default access is true (public)

def bind_type():

    return stack.pop()

# BEGINNING OF EXECUTION

def recurse_print(tree, level = 0):

    if tree['nodes']: # True for non-terminals, false for terminals
        level += 1 # This actually works, because parameters are just local variables, for some reason
        if tree['value']:
            print(('  ' * level), tree['value'])
        else:
            print(('  ' * level), tree['id'])
        for item in tree['nodes']:
            recurse_print(item, level)
    else:
        level += 1
        print(('  ' * level), tree['value'])

file = 'statements.sophia'

with open(file, 'r') as f:
    input = f.read().splitlines()

tree = sophia.parser(input) # Here's tree
recurse_print(tree)
instructions = sophia.interpreter(tree)
[print(line) for line in instructions]

stack = []
main = {'global': namespace()}