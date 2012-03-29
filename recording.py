#!/usr/bin/python3

import time
import gzip
import sys
import itertools

#import matplotlib.pyplot as plt

import state_factory
import heating

INTERVAL = 60
AVERAGE_COUNT = 10

PLOT_LEN = 24 * 3600
PLOT_COUNT = PLOT_LEN // INTERVAL

sf = state_factory.StateFactory()

average = []

print('running')

f = gzip.open(sys.argv[1], 'ab')

state = sf.get_state()
print(state)

#plot_values = numpy.zeroes((2 * PLOT_COUNT, len(state.values['room_temp'])))
#plot_times = numpy.zeroes(2 * PLOT_COUNT)

try:
    while True:
#    for i in itertools.cycle(range(PLOT_COUNT)):
#        plot_values[i,:] = state.values['room_temp']
#        plot_times[i] = state.timestamp
#        plot_values[i + PLOT_COUNT,:] = state.values['room_temp']
#        plot_times[i + PLOT_COUNT] = state.timestamp
#        plt.plot_date(plot_times, plot_values)

        time.sleep(INTERVAL)

        state = sf.get_state()
        print(state)

        average.append(state)

        if len(average) == AVERAGE_COUNT:
            averaged = heating.State.average(average)

            print("\nsaving:")
            print(averaged)

            averaged.save(f)
            average = []
except KeyboardInterrupt:
    print('interrupted')
finally:
    f.close()
