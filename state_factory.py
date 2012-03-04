import heating

import db_net.udp
import db_net.registers

import numpy

class StateFactory:
    """
    Create states from dbnet registers.
    This is specific to our house.
    """
    PASSWORD = 48414
    ADDRESS = ('10.0.0.202', 59)
    MY_STATION = 25
    REMOTE_STATION = 4

    ROOM_COUNT = 19

    def __init__(self):
        self.conn = db_net.udp.Client(
            self.ADDRESS,
            self.REMOTE_STATION,
            self.PASSWORD,
            dbnet_source_addr = self.MY_STATION)

        self.temp_reg = db_net.registers.Register(self.conn, 4112, 'MF[25,1]', auto_update = True)
        self.status_reg = db_net.registers.Register(self.conn, 4113, 'MI[1,5]', auto_update = True)
            # There's no need to read the whole matrix when only part of it will be used.

        self.heating_count = self.get_heating_count()

        self.prevState = None

    def get_heating_count(self):
        ordering_reg = db_net.registers.Register(self.conn, 4082, 'MI[1,32]', auto_update = True)

        for i, value in enumerate(ordering_reg.value[0,:]):
            if value == 255:
                return i

        return 32

    def get_state(self):
        temps = self.temp_reg.value
        status = self.status_reg.value

        room_temp = temps[:self.ROOM_COUNT,0]
        all_temps = temps[:,0]

        bits = status[0, 3] | (status[0, 4] << 8)

        heating_on = numpy.zeros(self.heating_count, dtype=numpy.bool)
        i = 0
        while bits > 0:
            heating_on[i] = bool(bits & 0x01)
            bits = bits >> 1
            i = i + 1

        state = heating.State(self.prevState,
            room_temp = room_temp,
            heating_on = heating_on,
            heating_temp = all_temps[24],
            return_temp = all_temps[23],
            outside_temp = all_temps[19],
            dhw_bottom_temp = all_temps[21],
            buffer_temp = all_temps[22])

        self.prevState = state

        return state

