#!/usr/bin/python3
import db_net_udp
import db_net_registers

from hexdump import *

for data in open('packets.txt', 'r'):
    data = bytes.fromhex(data.strip())

    print('*' * 80)

    p = db_net_udp.Packet.from_bytes(data)#, 48414)
    if p.mode == db_net_udp.Packet.INVALID_STATION_KEY:
        print("Correcting station key (0x{:x})".format(p.station_key))
        continue
    
    print('{} -> {}'.format(p.dbnet_packet.sa, p.dbnet_packet.da))

    try:
        rq = db_net_registers.ReadRequest.from_bytes(p.dbnet_packet.payload)
    except:
        pass
    else:
        print(rq)
        continue

    resp = db_net_registers.ReadResponse.from_bytes(p.dbnet_packet.payload, rq)
    try:
        pass
    except Exception as e:
        pass
    else:
        print(resp)
        continue

    print("msg id: 0x{:x}, payload:".format(p.dbnet_packet.msg_id))
    hexdump_p(p.dbnet_packet.payload)

#conn = db_net_udp.DBNetUdpConnection(('10.0.0.202', 59), 4, 48414)
