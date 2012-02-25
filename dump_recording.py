#!/usr/bin/python3

import sys
import gzip
import heating

f = gzip.open(sys.argv[1], 'rb')

while True:
    state = heating.State.load(f)

    if state is None:
        break

    print(state)
    print()

