#!/usr/bin/python3

import db_net_udp

for data in [
    'e029b521 0000 00000000 4f5bf337 0f ba37f7aad621b5c3833a083da3c8073ca3e80793b5',
    'e029b521 1111 eb2b9487 00000000 ',
    'e129b521 0000 eb2b9487 7b906eab 0f edf220e381e4628a3b58f7061baaf8071b8af8a80d',
    'e129b521 0000 eb2b9487 ceb93126 44 edb96be39cf92f0a1baaf90619aafd0618aafc0611aaf30612aae9061daaf0060baaf50614aaf40615aa0706e4aa0706e4aa0706e4aa0706e4aa0706e4aa0706e4aa0706e4aa07062abc',
    'e229b521 0000 eb2b9487 9b4e05e2 0f bb18af0bd70eed62ef9f982ecd8f8830cd8d88e3db',
    'e229b521 0000 eb2b9487 36ab407d f4 bbe3540bca13a0e2aae91e6fcd8f1c6fcd8f1c6fcd8f106f0043146fcd8f106f5716296fcd8f006f5716296fcd8f006fcd8f2c6fcd8f286fcd8f206fcd8f286f00438c6fcd8ff86ffebc936fcd8f286ecd8f3c6fcd8f206fabe92e6fcd8f206f0043306fcd8f206fcc8f106fcd8f1c6fabe9226fcd8ff06fcd8f1c6fcd8f086f5716f96fcd8fe06ffebc2f6fcd8f106fcd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ecd8f882ed599'
    ]:
    data = bytes.fromhex(data)

    p = db_net_udp.DBNetUdpPacket.from_bytes(data)#, 48414)
    if p.mode == db_net_udp.DBNetUdpPacket.INVALID_STATION_KEY:
        print("{}: StationKey = {}".format(p.id_trans, p.station_key))
    else:
        print("{}: {} -> {} StationKey = {}".format(p.id_trans, p.dbnet_packet.sa, p.dbnet_packet.da, p.station_key))

#conn = db_net_udp.DBNetUdpConnection(('10.0.0.202', 59), 4, 48414)
