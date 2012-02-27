import numpy
import time
import sys
import itertools
import copy

class State:
    FILE_SEPARATOR = b'|'

    def __init__(self, prev_state,
        room_temp, heating_on,
        heating_temp, return_temp,
        outside_temp,
        dhw_bottom_temp, buffer_temp,
        timestamp = None):

        self.room_temp = room_temp
        self.heating_on = numpy.array(heating_on, dtype=numpy.float)
        self.heating_temp = heating_temp
        self.return_temp = return_temp
        self.outside_temp = outside_temp
        self.dhw_bottom_temp = dhw_bottom_temp
        self.buffer_temp = buffer_temp

        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

        if prev_state is None:
            self.d_temp = None
            return

        self.d_temp = (room_temp - prev_state.room_temp) / (self.timestamp - prev_state.timestamp)

    def is_complete(self):
        return self.d_temp is not None

    @classmethod
    def _rd_line(cls, f, dtype):
        line = f.readline()

        if len(line) == 0:
            raise StopIteration()

        return numpy.array(line.strip().split(cls.FILE_SEPARATOR), dtype=dtype)

    def _w_line(cls, f, line):
        f.write(cls.FILE_SEPARATOR.join((str(x).encode('ascii') for x in line)))
        f.write(b'\n')

    def save(self, f):
        self._w_line(f, self.room_temp)
        self._w_line(f, self.heating_on)
        self._w_line(f, self.d_temp)
        self._w_line(f, (self.heating_temp, self.return_temp,
            self.outside_temp, self.dhw_bottom_temp, self.buffer_temp,
            self.timestamp))

    @classmethod
    def load(cls, f):
        self = cls(None, None, None, None, None, None, None, None)

        try:
            self.room_temp = cls._rd_line(f, numpy.float)
            self.heating_on = cls._rd_line(f, numpy.float)
            self.d_temp = cls._rd_line(f, numpy.float)
            self.heating_temp, self.return_temp, \
                self.outside_temp, self.timestamp, \
                self.dhw_bottom_temp, self.buffer_temp = cls._rd_line(f, numpy.float)
        except StopIteration:
            return None

        return self

    @classmethod
    def average(cls, states_iterable):
        it = iter(states_iterable)

        self = copy.deepcopy(next(it))
        count = 1

        for state in it:
            self.room_temp += state.room_temp
            self.heating_on += state.heating_on
            self.heating_temp += state.heating_temp
            self.return_temp += state.return_temp
            self.outside_temp += state.outside_temp
            self.dhw_bottom_temp += state.dhw_bottom_temp
            self.buffer_temp += state.buffer_temp
            count += 1
            
        self.room_temp /=count
        self.heating_on /=count
        self.heating_temp /=count
        self.return_temp /=count
        self.outside_temp /=count
        self.dhw_bottom_temp /=count
        self.buffer_temp /=count

        return self

    def __str__(self):
        lines = []
        if self.d_temp is None:
            d_temp = itertools.repeat(None)
        else:
            d_temp = self.d_temp
        for i, (t, h, dt) in enumerate(zip(self.room_temp, self.heating_on, d_temp)):
            lines.append('{}: t = {:.2f}°C, heating = {}, dt/dtau = {}'.format(i, float(t), h, dt))

        lines.append('outside temp = {:.2f}°C, heating temp = {:.2f}°C -> {:.2f}°C'.format(
            float(self.outside_temp), float(self.heating_temp), float(self.return_temp)))

        lines.append('dhw temp = {:.2f}°C, buffer temp = {:.2f}°C'.format(
            float(self.dhw_bottom_temp), float(self.buffer_temp)))

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

