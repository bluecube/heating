import numpy
import re
import itertools
import struct
import db_net

def group(lst, n):
    """group([0,3,4,10,2,3], 2) => iterator

    Group an iterable into an n-tuples iterable. Incomplete tuples
    are discarded e.g.

    >>> list(group(range(10), 3))
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]

    from http://code.activestate.com/recipes/303060-group-a-list-into-sequential-n-tuples/#c5
    """
    return zip(*[itertools.islice(lst, i, None, n) for i in range(n)])

class Type:
    TYPES = {
        'I': (0x00, struct.Struct('<H'), numpy.int16),
        'L': (0x01, struct.Struct('<I'), numpy.int32),
        'F': (0x02, struct.Struct('<f'), numpy.float32)
        }
    MATRIX_MASK = 0x20
    TYPE_MASK = 0x03

    @classmethod
    def _tuple_by_code(cls, code):
        for letter, (c, unpacker, dtype) in cls.TYPES.items():
            if code & cls.TYPE_MASK == c & cls.TYPE_MASK:
                return letter, unpacker, dtype

        raise Exception('Invalid type')

    def __init__(self, type_code, matrix = False):
        if isinstance(type_code, str):
            self.code, self.unpacker, self.dtype = self.TYPES[type_code]
        else:
            letter, self.unpacker, self.dtype = self._tuple_by_code(type_code)
            self.code = type_code

        self.matrix = matrix

        if matrix:
            self.code |= self.MATRIX_MASK

        if matrix:
            self.size = matrix[0] * matrix[1] * self.unpacker.size
        else:
            self.size = self.unpacker.size
    
    @classmethod
    def from_string(cls, string):
        matched = re.match(r'^(M?)([A-Z])(?:\[(\d+),(\d+)\])?$', string)

        if not matched:
            raise Exception("Invalid DBNet type string")

        matrix, type_code, rows, columns = matched.groups()

        if matrix == 'M':
            try:
                rows = int(rows)
                columns = int(columns)
            except (TypeError, ValueError):
                raise Exception("Invalid or missing matrix dimensions")

            matrix = (rows, columns)
        else:
            matrix = False

        return cls(type_code, matrix)

    def __str__(self):
        letter, unpacker, dtype = self._tuple_by_code(self.code)
        if self.matrix:
            return 'M{}[{},{}]'.format(letter, self.matrix[0], self.matrix[1])
        else:
            return letter

class ReadRequest:
    PACKER = struct.Struct('<BBBBHHHH')
    def __init__(self):
        self.wid = None
        self.type = None
        self.i0 = None
        self.j0 = None
        self.rows = None
        self.cols = None
        self.msg_id = 0x4D

    @classmethod
    def from_bytes(cls, data):
        if data[0] != 0x01:
            raise Exception('Read request has invalid start byte')

        if (data[1] & Type.MATRIX_MASK) != Type.MATRIX_MASK:
            raise Exception('Only matrix reads are supported now')

        self = cls()
        unused, code, wid_lo, wid_hi, self.i0, self.j0, self.rows, self.cols = \
            cls.PACKER.unpack(data)
        self.wid = wid_hi << 8 | wid_lo
        self.type = Type(code, (self.rows, self.cols))

        return self

    def __bytes__(self):
        return self.PACKER.pack(
            0x1,
            self.type.code,
            (self.wid >> 8) & 0xff,
            self.wid & 0xff,
            self.i0, self.j0, self.rows, self.cols)
     
    def details_to_string(self):
        return 'WID = {} ({}), {}x{} items from {}, {}'.format(
            self.wid, self.type, self.rows, self.cols, self.i0, self.j0)

    def __str__(self):
        return 'Read request: ' + self.details_to_string()

class ReadResponse:
    def __init__(self):
        self.value = None

    @classmethod
    def from_bytes(cls, data, request):
        if data is None:
            raise Exception('Error processing the request (data is None).')

        if data[0] != 0x81:
            raise Exception('Read response has invalid start byte')

        self = cls()
        self.request = request

        if len(data) != request.type.unpacker.size * request.rows * request.cols + 1:
            raise Exception('Invalid length of reply')

        flat_values = [request.type.unpacker.unpack(bytes(x))[0]
            for x in group(data[1:], request.type.unpacker.size)]

        self.value = list(group(flat_values, request.cols))

        return self
        
    def __str__(self):
        return 'Read response: {}\n{}'.format(
            self.request.details_to_string(), str(self.value))

class Register:
    def __init__(self, connection, wid, data_type, auto_update = False):
        self._connection = connection
        self._wid = wid
        self._type = Type.from_string(data_type)
        self._auto_update = auto_update

        if not self._type.matrix:
            raise Exception('Only matrix registers are supported now.')

        shorter_dim = min(*self._type.matrix)
        longer_dim = max(*self._type.matrix)

        # Maximal number of matrix items per transfer
        max_items = (db_net.Packet.PAYLOAD_SIZE_LIMIT - 1) // self._type.unpacker.size
        rows_per_batch = max_items // shorter_dim
        
        if rows_per_batch == 0:
            raise Exception('The matrix is too big, sorry')

        batches = ((x, min(rows_per_batch, longer_dim - x))
            for x in range(0, longer_dim, rows_per_batch))

        self._batches = []

        if self._type.matrix[0] > self._type.matrix[1]:
            for start, length in batches:
                self._batches.append((start, 0, length, self._type.matrix[1]))
        else:
            for start, length in batches:
                self._batches.append((0, start, self._type.matrix[0], length))

    def auto_update(self, val):
        self._auto_update = val

    def update(self):
        self._value = numpy.empty(self._type.matrix)

        for i0, j0, rows, cols in self._batches:
            rq = ReadRequest()
            rq.wid = self._wid
            rq.type = self._type
            rq.i0 = i0
            rq.j0 = j0
            rq.rows = rows
            rq.cols = cols

            resp_msg_id, resp_bytes = self._connection.transfer(rq.msg_id, bytes(rq))

            if resp_bytes is None:
                raise Exception("Reply: error!")

            resp = ReadResponse.from_bytes(resp_bytes, rq)

            for i, row in zip(range(i0, i0 + rows), resp.value):
                for j, x in zip(range(j0, j0 + rows), row):
                    self._value[i, j] = x
    
    @property
    def value(self):
        if self._auto_update:
            self.update()
        
        return self._value
