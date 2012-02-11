import itertools
import binascii

#from hexdump import hexdump_p

UINT8_MAX = 0xff

class DBNetPacketException(Exception):
    pass

class Packet:
    PAYLOAD_SIZE_LIMIT = 240

    def __init__(self):
        self.sa = None
        self.da = None
        self.msg_id = None
        self.payload = None

    @classmethod
    def from_bytes(cls, data):
        #hexdump_p(data, "dbnet_packet")
        self = cls()

        if data[0] == 0x10:
            self.payload = None
            self.da = data[1]
            self.sa = data[2]
            self.msg_id = data[3]
        elif data[0] == 0x68:
            if data[3] != 0x68: 
                raise DBNetPacketException("Invalid packet preamble (start byte not matched)")
            length = data[1]
            if data[2] != length:
                raise DBNetPacketException("Invalid packet preamble (size not matched)")
            self.payload = data[7:-2]
            if len(self.payload) + 3 != length:
                raise DBNetPacketException("Payload size mismatch")
            self.da = data[4]
            self.sa = data[5]
            self.msg_id = data[6]
        else:
            raise DBNetPacketException("Invalid packet preamble")
        
        if data[-2] != self._checksum():
            raise DBNetPacketException("Invalid checksum")

        if data[-1] != 0x16:
            raise DBNetPacketException("Invalid end byte")

        return self

    def __bytes__(self):
        out = []

        if self.payload is None:
            payload = bytes()
            out.append(0x10)
        else:
            payload = bytes(self.payload)
            out.append(0x68)
            out.append(len(payload) + 3)
            out.append(len(payload) + 3)
            out.append(0x68)

        out.append(self.da)
        out.append(self.sa)
        out.append(self.msg_id)

        out.extend(payload)

        out.append(self._checksum())

        out.append(0x16)

        return bytes(out)
        
    def _checksum(self):
        checksum = 0

        data = [self.da, self.sa, self.msg_id]
        if self.payload is not None:
            data = itertools.chain(bytes(self.payload), data)

        for x in data:
            checksum += x

            if checksum > UINT8_MAX:
                checksum = (checksum & UINT8_MAX) + 1

        return checksum & UINT8_MAX
