#!/usr/bin/python3

import heating

import time
import gzip
import sys

import db_net.udp
import db_net.registers

INTERVAL = 10 * 60
WID = 4112
#TYPE = 'MF[32,2]'
# There's no need to read the whole matrix when only part of it will be used.
TYPE = 'MF[25,2]'
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
reg = db_net.registers.Register(conn, WID, TYPE, auto_update = True)

prevState = None

print('running')

try:
    with gzip.open(sys.argv[1], 'ab') as f:
        while True:
            matrix = reg.value

            room_temps = matrix[:ROOM_COUNT,0]
            requested_temps = matrix[:ROOM_COUNT,1]
            all_temps = matrix[:,0]
            
            heating_on = room_temps < requested_temps

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
