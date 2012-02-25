import numpy
import time
import sys
import itertools

class State:
    FILE_SEPARATOR = b'|'

    def __init__(self, prev_state,
        room_temp, heating_on, heating_temp, heating_return_temp,
        outside_temp, timestamp = None):

        self.room_temp = room_temp
        self.heating_on = heating_on
        self.heating_temp = heating_temp
        self.heating_return_temp = heating_return_temp
        self.outside_temp = outside_temp

        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

        if prev_state is None:
            self.d_temp = None
            return

        self.d_temp = (room_temp - prev_state.room_temp) / (self.timestamp - prev_state.timestamp)

    def save(self, f):
        self._w_line(f, self.room_temp)
        self._w_line(f, self.heating_on)
        self._w_line(f, self.d_temp)
        self._w_line(f, (self.heating_temp, self.heating_return_temp,
            self.outside_temp, self.timestamp))

    @classmethod
    def _rd_line(cls, f, dtype):
        line = f.readline()

        if len(line) == 0:
            raise StopIteration()

        return numpy.array(line.strip().split(cls.FILE_SEPARATOR), dtype=dtype)

    def _w_line(cls, f, line):
        f.write(cls.FILE_SEPARATOR.join((str(x).encode('ascii') for x in line)))
        f.write(b'\n')

    @classmethod
    def load(cls, f):
        self = cls(None, None, None, None, None)

        try:
            self.room_temp = cls._rd_line(f, numpy.float)
            self.heating_on = cls._rd_line(f, numpy.bool)
            self.d_temp = cls._rd_line(f, numpy.float)
            self.heating_temp, self.heating_return_temp, \
                self.outside_temp, self.timestamp = cls._rd_line(f, numpy.float)
        except StopIteration:
            return None

        return self

    def __str__(self):
        lines = []
        if self.d_temp is None:
            d_temp = itertools.repeat(None)
        else:
            d_temp = self.d_temp
        for i, (t, h, dt) in enumerate(zip(self.room_temp, self.heating_on, d_temp)):
            lines.append('{}: t = {:.2f}°C, heating = {}, dt/dtau = {}'.format(i, t, h, dt))

        lines.append('outside temp = {:.2f}°C, heating temp = {:.2f}°C -> {:.2f}°C'.format(
            self.outside_temp, self.heating_temp, self.heating_return_temp))

        return '\n'.join(lines)

class HeatingModel:
    def __init__(self):
        pass

    def predict(self, state, new_timestamp):
        pass

    def _state_to_params(self, state):
        pass

    def learn(self, state_iterator):
        pass

    def save(self, f):
        pass

    @classmethod
    def load(cls, f):
        return cls()

