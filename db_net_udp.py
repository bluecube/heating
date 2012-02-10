import struct
import itertools
import binascii

import socket
import select

import db_net

#from hexdump import hexdump_p

UINT32_MAX = 0xffffffff

class DBNetUdpException(Exception):
    pass

class DBNetUdpPacketException(DBNetUdpException):
    pass

class DBNetUdpTimeoutException(DBNetUdpException):
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

class Packet:
    _packer = struct.Struct('<IHII')
    _int_packer = struct.Struct('<I')

    NORMAL_MODE = 0
    INVALID_STATION_KEY = 0x1111

    def __init__(self):
        self.id_trans = None
        self.station_key = None
        self.dbnet_packet = None
        self.password = None

        self.mode = self.NORMAL_MODE
    
    def __bytes__(self):
        header = self._packer.pack(
            self.id_trans,
            self.mode,
            self.station_key,
            self._signature())

        if self.mode == self.INVALID_STATION_KEY:
            if self.dbnet_packet != None:
                raise DBNetUdpPacketException("No payload is allowed if mode is INVALID_STATION_KEY.")

            return header

        packet = self._encrypt_packet(bytes(self.dbnet_packet))
        return header + bytes([len(packet) - 6]) + packet

    @classmethod
    def from_bytes(cls, data, password = None):
        """
        Read data from bytes, sets the instance variables.
        Throws exceptions in case of errors.
        """

        self = cls()

        self.password = password

        (self.id_trans, self.mode, self.station_key, self._received_signature) = \
            self._packer.unpack(data[:14])

        if len(data) <= 14:
            return self
        
        length = data[14]

        encrypted_packet = data[15:]

        if len(encrypted_packet) != length + 6:
            raise DBNetUdpPacketException("Non matching length")

        self.dbnet_packet = db_net.Packet.from_bytes(
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

    def bruteforce(self):
        """
        Try to find the password for a received packet by enumerating all possibilities.
        Prints stuff, takes a whole day on my computer.
        """

        results = []

        try:
            for password_high in range(0, 2**32, 2**16):
                print("{:.4%}".format(password_high / 2**32))
                for password in range(password_high, password_high + 2**16):
                    self.password = password
                    if self._received_signature == self._signature():
                        print("!!! Found: {} !!!".format(password))
                        results.append(password)
        except KeyboardInterrupt:
            pass
        finally:
            print("results: " + ', '.join((str(p) for p in results)))

class _Connection:
    BUFFSIZE = 1024
    TRY_COUNT = 3

    def __init__(self, password, timeout = 3):
        self._timeout = timeout
        self._password = password

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _receive(self):
        (ready_rd, x, x) = select.select([self._socket], [], [], self._timeout)

        if not ready_rd:
            raise DBNetUdpTimeoutException("Receive timed out")

        received, addr = self._socket.recvfrom(self.BUFFSIZE)

        return Packet.from_bytes(received), addr


class Client(_Connection):
    TRY_COUNT = 3

    def __init__(self, addr, dbnet_addr, password, timeout = 3, dbnet_source_addr = 0x1f):
        super().__init__(password, timeout)
        self._addr = addr
        self._sa = dbnet_source_addr
        self._da = dbnet_addr

        self._station_key = {}
        self._id_trans = 0

    def _send(self, msg_id, payload, addr):
        self._id_trans += 1

        packet = Packet()
        packet.id_trans = self._id_trans
        packet.station_key = self._station_key.get(self._da, 0)
        packet.password = self._password

        packet.dbnet_packet = db_net.Packet()
        packet.dbnet_packet.sa = self._sa
        packet.dbnet_packet.da = self._da
        packet.dbnet_packet.msg_id = msg_id
        packet.dbnet_packet.payload = payload

        b = bytes(packet)

        self._socket.sendto(bytes(packet), addr)

    def transfer(self, msg_id, payload = None):
        """
        Perform a single transfer in client mode.
        Repeatedly sends a message and reads answers, until
        one of them is valid or a number of tries fails.
        Returns tuple with reply message id and payload.
        """
        i = 1
        last_exc = []
        while i < self.TRY_COUNT:
            self._send(msg_id, payload, self._addr)

            #hexdump_p(payload, "Sent:")

            try:
                packet, address = self._receive()
            except DBNetUdpException as e:
                i += 1
                last_exc.append(str(e))
                continue

            if packet.id_trans != self._id_trans:
                i += 1
                last_exc.append("Non matching transaction identifier")
                continue

            self._station_key[self._da] = packet.station_key

            if packet.mode == Packet.INVALID_STATION_KEY:
                continue
            
            #hexdump_p(packet.dbnet_packet.payload, "Received:")
            return (packet.dbnet_packet.msg_id, packet.dbnet_packet.payload)

        raise DBNetUdpException('Failed to receive valid reply packet (' +
            ', '.join(last_exc) + ")")


class Server(_Connection):
    def __init__(self, addr, handler, password, timeout = 3):
        super().__init__(password, timeout)
        self._handler = handler

        self._socket.bind(addr)

    def run(self):
        """
        Run a server in the current thread.
        We're ignoring crypto here as much as possible,
        because it's pointless anyway. Only exception is the master password,
        to keep the interface for client and server as consistent as possible.
        """
        while True:
            try:
                packet, address = self._receive()
            except DBNetUdpTimeoutException:
                continue

            reply = self._handler(
                packet.dbnet_packet.msg_id, packet.dbnet_packet.payload)

            if reply is None:
                reply_msg_id = 0
                reply_payload = None
            else:
                reply_msg_id, reply_payload = reply
            
            reply = DBNetUdpPacket()
            reply.id_trans = packet.id_trans
            reply.station_key = 0xbadf00d # instead of making up random keys...
            reply.password = self._password
            reply.dbnet_packet = db_net.DBNetPacket()

            reply.dbnet_packet.da = packet.dbnet_packet.sa
            reply.dbnet_packet.sa = packet.dbnet_packet.da
            reply.dbnet_packet.msg_id = reply_msg_id
            reply.dbnet_packet.payload = reply_payload

            self._socket.sendto(bytes(reply), address)


