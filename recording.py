#!/usr/bin/python3

import heating

import time
import gzip
import sys

import db_net.udp
import db_net.registers
import numpy

INTERVAL = 10 * 60
PASSWORD = 48414
ADDRESS = ('10.0.0.202', 59)
MY_STATION = 25
REMOTE_STATION = 4

ROOM_COUNT = 19


conn = db_net.udp.Client(
    ADDRESS,
    REMOTE_STATION,
    PASSWORD,
    dbnet_source_addr = MY_STATION)
temp_reg = db_net.registers.Register(conn, 4112, 'MF[25,2]', auto_update = True)
status_reg = db_net.registers.Register(conn, 4113, 'MI[1,5]', auto_update = True)
    # There's no need to read the whole matrix when only part of it will be used.

ordering_reg = db_net.registers.Register(conn, 4082, 'MI[1,32]', auto_update = True)

heating_count = 32
for i, value in enumerate(ordering_reg.value[0,:]):
    if value == 255:
        heating_count = i
        break

prevState = None

print('running')

try:
    with gzip.open(sys.argv[1], 'ab') as f:
        while True:
            temps = temp_reg.value
            status = status_reg.value

            room_temps = temps[:ROOM_COUNT,0]
            all_temps = temps[:,0]

            bits = status[0, 3] | (status[0, 4] << 8)

            heating_on = numpy.zeros(heating_count, dtype=numpy.bool)
            i = 0
            while bits > 0:
                heating_on[i] = bool(bits & 0x01)
                bits = bits >> 1
                i = i + 1

            state = heating.State(prevState,
                room_temps, heating_on, all_temps[24], all_temps[23],
                all_temps[19])

            print(state)

            if prevState is not None:
                state.save(f)

            prevState = state

            time.sleep(INTERVAL)
except KeyboardInterrupt:
    print('interrupted')
