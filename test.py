#!/usr/bin/python3

import db_net_udp

data = bytes.fromhex(
    'e329b5210000eb2b94876e7023370f493d1f54252b5d3d5d6508487f7518547f77189969')


p = db_net_udp.DBNetUdpPacket.from_bytes(data, 48414)
