a = {'a': 1, 'b': 2, 'c': 3}

items = list(a.items())
i = range(0, 2, 1)
value = dict([items[n] for n in i])
print(value)