def debug_tree(tree, level = 0): # Takes a parse tree

    if tree.nodes: # True for non-terminals, false for terminals
        level += 1 # This actually works, because parameters are just local variables, for some reason
        if tree.value:
            print(('  ' * level), tree.value)
        else:
            print(('  ' * level), type(tree).__name__)
        for item in tree.nodes:
            debug_tree(item, level)
    else:
        level += 1
        print(('  ' * level), tree.value)

def debug_namespace(module): # Takes a list formatted like a module

    print('===')
    for i, scope in enumerate(module.namespace):
        debug_scope(scope)
        if i != len(module.namespace) - 1:
            print('---')
    print('===')

def debug_scope(scope): # Takes a list of bindings

    for binding in scope:
        if binding.type == 'module':
            print(binding.name, binding.type, [item.name for item in binding.value.namespace[0]])
        elif binding.type == 'type' and hasattr(binding.value, 'namespace'):
            print(binding.name, binding.type, [item.name for item in binding.value.namespace])
        else:
            print(binding.name, binding.type, binding.value)