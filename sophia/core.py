def init_types(): # Yeah, there's some name mangling going on here

    def _untyped(value):

        return value

    def _integer(value):

        if isinstance(value, int) or isinstance(value, float) and int(value) == value:
            return int(value)
        else:
            raise TypeError('Could not cast to integer')

    def _float(value):

        if isinstance(value, float) or isinstance(value, int) and float(value) == value:
            return float(value)
        else:
            raise TypeError('Could not cast to float')

    def _bool(value):

        if value is True or value is False:
            return value
        else:
            raise TypeError('Could not cast to boolean')

    def _string(value):

        if isinstance(value, str):
            return value
        else:
            raise TypeError('Could not cast to string')

    def _list(value):

        if isinstance(value, list):
            return value
        else:
            raise TypeError('Could not cast to list')

    def _record(value):

        if isinstance(value, dict):
            return value
        else:
            raise TypeError('Could not cast to record')

    return [[name[1:], value, 'type'] for name, value in locals().items()]

def init_functions():

    def _input(value):

        return input(value)

    def _print(value):

        return print(value)

    def _error(value):
        
        raise Exception(value)

    def _range(*args):

        return range(*args) # Currently exclusive of args[1]

    def _floor(value):

        if value >= 0:
            return int(value) # int() truncates floats
        else:
            return int(value) - 1

    def _ceiling(value):

        if value >= 0:
            return int(value) + 1 # int() truncates floats
        else:
            return int(value)
        
    return [[name[1:], value, 'untyped', True] for name, value in locals().items()]

def init_operators():
    
    def unary_add(x):

        return x

    def unary_sub(x):

        return -x

    def add(x, y):

        return x + y

    def sub(x, y):

        return x - y

    def mul(x, y):

        return x * y

    def div(x, y):

        return x / y

    def exp(x, y):

        return x ** y

    def mod(x, y):

        return x % y

    def intersection(x, y):

        return list(filter(lambda i: i in x, y))

    def union(x, y):

        return x + y

    def unary_bit_not(x):

        return ~x

    def bit_and(x, y):

        return x & y

    def bit_or(x, y):

        return x | y

    def bit_xor(x, y):

        return x ^ y

    def eq(x, y):

        if x == y:
            return True
        else:
            return False

    def lt(x, y):

        if x < y:
            return True
        else:
            return False

    def gt(x, y):

        if x > y:
            return True
        else:
            return False

    def lt_eq(x, y):

        if x <= y:
            return True
        else:
            return False

    def gt_eq(x, y):

        if x >= y:
            return True
        else:
            return False

    def not_eq(x, y):

        if x != y:
            return True
        else:
            return False

    def in_op(x, y):

        if x in y:
            return True
        else:
            return False

    def unary_not_op(x):

        return not x

    def and_op(x, y):

        return x and y

    def or_op(x, y):

        return x or y

    def xor_op(x, y):

        if x is not y:
            return True
        else:
            return False

    return locals()