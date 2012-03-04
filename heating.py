import numpy
import time
import sys
import itertools
import copy
import datetime

class State:
    FILE_SEPARATOR = b'|'
    SINGLE_ITEM = b'='
    MULTIPLE_ITEMS = b'x'

    def __init__(self, prev_state, timestamp = None, **kwargs):

        self.values = kwargs

        self._check_all_values()

        self.values['heating_on'] = numpy.array(self.values['heating_on'], dtype=numpy.float)

        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

        if prev_state is None:
            self.d_temp = None
            return

        self.values['d_temp'] = (self.values['room_temp'] - prev_state.values['room_temp']) / (self.timestamp - prev_state.timestamp)

    def _check_all_values(self):
        self._check_value('room_temp')
        self._check_value('heating_on')
        self._check_value('heating_temp')
        self._check_value('return_temp')
        self._check_value('outside_temp')

    def _check_value(self, name):
        if name not in self.values:
            raise Exception('missing required value ' + name)

    def _w_line(cls, f, value, name):
        f.write(name.encode('ascii'))
        f.write(cls.FILE_SEPARATOR)

        try:
            it = iter(value)
        except TypeError:
            f.write(cls.SINGLE_ITEM)

            f.write(cls.FILE_SEPARATOR)
            f.write(str(value).encode('ascii'))
        else:
            f.write(cls.MULTIPLE_ITEMS)

            for item in value:
                f.write(cls.FILE_SEPARATOR)
                f.write(str(item).encode('ascii'))

        f.write(b'\n')

    def save(self, f):
        for name, value in self.values.items():
            self._w_line(f, value, name)

        self._w_line(f, self.timestamp, 'timestamp')

        f.write(b'\n')

    @classmethod
    def load(cls, f):
        values = {}

        try:
            for line in f:
                items = line.strip().split(cls.FILE_SEPARATOR)
                if len(items) == 1:
                    break
                
                name = items[0].decode('ascii')
                
                if items[1] == cls.SINGLE_ITEM:
                    values[name] = items[2]
                else:
                    values[name] = numpy.array(items[2:])
        except StopIteration:
            return None

        if not len(values):
            return None

        timestamp = float(values['timestamp'])
        del values['timestamp']

        self = cls(None, timestamp, **values)

        return self

    @classmethod
    def average(cls, states_iterable):
        it = iter(states_iterable)

        self = copy.deepcopy(next(it))
        count = 1

        for state in it:
            for name in self.values:
                self.values[name] += state.values[name]
            count += 1
            
        for name in self.values:
            self.values[name] /= count

        return self

    def __str__(self):
        lines = ['*** {}'.format(datetime.datetime.fromtimestamp(self.timestamp).isoformat())]

        for name, value in self.values.items():
            lines.append('{}: {}'.format(name, str(value)))

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

