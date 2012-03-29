#!/usr/bin/python3

import sys
import gzip
import heating
import itertools

def states(fp):
    x = heating.State.load(fp)

    while x is not None:
        yield x
        x = heating.State.load(fp)

f = gzip.open(sys.argv[1], 'rb')

model = heating.HeatingModel()

model.learn(states(f))
model.save(sys.argv[2])
