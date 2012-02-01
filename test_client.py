#!/usr/bin/python3
import db_net_udp
import binascii

def handler(msg_id, payload):
    print("msg_id: {} ; payload: {}".format(msg_id, binascii.hexlify(payload)))

client = db_net_udp.DBNetUdpClient(('localhost', 5959), 45, 12345)

msg_id, payload = client.transfer(99, bytes(range(5)))

print(msg_id, payload)
