#!/usr/bin/env python3
"""FC16 (Write Multiple Registers) pro GBO RTU-over-TCP.

Pouziti:
  python3 gbo_modbus_fc16.py <address> <value>

Zapise value do address pres FC16, pak odeslat fixni EEPROM potvrzeni
(addr 76 = ChkSumEE = 0x55AA). Oba zapisy v jednom TCP spojeni.
"""
import sys
import socket
import struct
import time

HOST = '192.168.2.18'
PORT = 6770
SLAVE = 3
WAIT = 0.4  # GBO doc: min 350ms

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def build_frame(address, value):
    frame = struct.pack('>BBHHBH', SLAVE, 0x10, address, 1, 2, value & 0xFFFF)
    return frame + struct.pack('<H', crc16(frame))

def write_eeprom(address, value):
    ops = [
        (address, value),
        (76, 0x55AA),   # ChkSumEE - EEPROM potvrzeni (fixni)
    ]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((HOST, PORT))
    for addr, val in ops:
        s.send(build_frame(addr, val))
        time.sleep(WAIT)
        try:
            resp = s.recv(256)
            print(f'OK addr={addr} value={val} resp={resp.hex()}', flush=True)
        except Exception as e:
            print(f'WARN addr={addr}: {e}', flush=True)
    s.close()

if __name__ == '__main__':
    write_eeprom(int(sys.argv[1]), int(sys.argv[2]))
