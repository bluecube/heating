import struct
import itertools
import binascii

import db_net

UINT32_MAX = 0xffffffff

class DBNetUdpPacketException(Exception):
    pass

def _encrypt_block(key, data):
    """
    Encrypt a single 32 bit block.
    """
    if data:
        a = data
    else:
        data = 1

    b = key * a

    for i in range(4):
        a = (2 * a + 13)
        b = (key * (a + b))

    return (a + data + b) & UINT32_MAX

class DBNetUdpPacket:
    _packer = struct.Struct('<ixxiib')
    _int_packer = struct.Struct('<i')

    def __init__(self, password = None):
        self.id_trans = None
        self.station_key = None
        self.dbnet_packet = None

        self.password = password
    
    def __bytes__(self):
        packet = bytes(self.dbnet_packet)

        return _packer.pack(
            self.id_trans,
            self.station_key,
            self._calc_signature(),
            len(packet) - 6) + \
            self._encrypt_packet(bytes(self.dbnet_packet))

    @classmethod
    def from_bytes(cls, data, password = None):
        """
        Read data from bytes, sets the instance variables.
        Throws exceptions in case of errors.
        """

        self = cls(password)

        (self.id_trans, self.station_key, self._received_signature, length) = \
            self._packer.unpack(data[:15])

        encrypted_packet = data[15:]

        if len(encrypted_packet) != length + 6:
            raise DBNetUdpPacketException("Non matching length")

        self.dbnet_packet = db_net.DBNetPacket.from_bytes(
            self._encrypt_packet(encrypted_packet))
        
        if self.password is not None:
            if self._received_signature != self._signature():
                raise DBNetUdpPacketException("Non matching signature")

        return self

    def _signature(self):
        return _encrypt_block(
            self.password,
            self.id_trans + self.station_key + 256 +
            self.dbnet_packet._checksum())

    def _keystream(self):
        """
        Return iterator with keystream for the packet encryption/decryption
        """

        key1 = self._int_packer.pack(
            _encrypt_block(self.station_key, (~self.id_trans) & UINT32_MAX))
        key2 = self._int_packer.pack(
            _encrypt_block(self.station_key, self.id_trans))

        # First there are eight bytes encrypted using key1 (two repetitions),
        # then key2 until the end
        return itertools.chain(key1, key1, itertools.cycle(key2))

    def _encrypt_packet(self, packet):
        return bytes((x ^ key for x, key in zip(packet, self._keystream())))
