symbols = ['\t', '\n', # Symbols are space-unseparated
                ':', ',', '.', '!',
                '(', '[', '{',
                ')', ']', '}'] # Characters that need to be interpreted as distinct tokens

operator_list = ['+', '-', '*', '/', '^', '%', '~', '&&', '||', '^^', '&', '|', # Standard operators
                        '<=', '>=', '!=', '<', '>', '=', 'in', 'not', 'and', 'or', 'xor'] # Logic operators
operator_names = ['add', 'sub', 'mul', 'div', 'exp', 'mod', 'bit_not', 'bit_and', 'bit_or', 'bit_xor', 'intersection', 'union',
                        'lt_eq', 'gt_eq', 'not_eq', 'lt', 'gt', 'eq', 'in_op', 'not_op', 'and_op', 'or_op', 'xor_op']
operator_dict = dict(zip(operator_list, operator_names)) # Dictionary with operator names as keys and operator symbols as values

structure_tokens = ['if', 'else', 'while', 'for', 'assert', 'type', 'constraint', 'return', 'yield', 'import']
keyword_tokens = ['is', 'extends', 'pass', 'continue', 'break']

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
        if char in symbols or char in operator_list: # If symbol found, split the token into everything before it, itself, and everything after it
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