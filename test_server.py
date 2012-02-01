#!/usr/bin/python3
import db_net_udp
import binascii

def handler(msg_id, payload):
    print("msg_id: {} ; payload: {}".format(msg_id, binascii.hexlify(payload)))

server = db_net_udp.DBNetUdpServer(('localhost', 5959), handler, 12345)

server.run()
