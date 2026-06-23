#!/usr/bin/env python3
"""FC16 (Write Multiple Registers) pro GBO RTU-over-TCP."""
import sys
import socket
import struct

HOST = '192.168.2.18'
PORT = 6770
SLAVE = 3

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def fc16_write(address, value):
    frame = struct.pack('>BBHHBH', SLAVE, 0x10, address, 1, 2, value & 0xFFFF)
    frame += struct.pack('<H', crc16(frame))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((HOST, PORT))
    s.send(frame)
    try:
        resp = s.recv(256)
        print(f'OK addr={address} value={value} resp={resp.hex()}', flush=True)
    except Exception as e:
        print(f'WARN no response: {e}', flush=True)
    s.close()

if __name__ == '__main__':
    fc16_write(int(sys.argv[1]), int(sys.argv[2]))
