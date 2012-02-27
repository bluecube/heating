#!/usr/bin/python3

import time
import gzip
import sys
import collections

import state_factory
import heating

INTERVAL = 60
AVERAGE_COUNT = 10

sf = state_factory.StateFactory()

display = collections.deque(maxlen = (24 * 3600) // INTERVAL)
average = []

print('running')

state = sf.get_state()
print(state)
time.sleep(INTERVAL)

try:
    with gzip.open(sys.argv[1], 'ab') as f:
        while True:
            state = sf.get_state()
            print(state)

            display.append(state)
            average.append(state)

            if len(average) == AVERAGE_COUNT:
                averaged = heating.State.average(average)

                print("\nsaving:")
                print(averaged)

                averaged.save(f)
                average = []

            time.sleep(INTERVAL)
except KeyboardInterrupt:
    print('interrupted')
