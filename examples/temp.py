import itertools

batch_size = 1
retires = 3

max_conns = 20
n_calls =  10
starting_batch_size = 3 # (-(n_calls) // max_conns)
print(starting_batch_size)
print('for loop')
# don't udnerstandand the point of htis
for batch_size in itertools.chain(map(lambda i: starting_batch_size // (2 ** i), range(retires)), [1]):
    print(batch_size)
    

