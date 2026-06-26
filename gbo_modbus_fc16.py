#!/usr/bin/env python3
"""FC16 (Write Multiple Registers) pro GBO RTU-over-TCP.

Pouziti:
  python3 gbo_modbus_fc16.py <address> <value> [--flash]

Zapise value do address pres FC16, pak EEPROM potvrzeni (addr 76 = 0x55AA).
S --flash navic zapise trigger 0x5200 na addr 386 = GBO ulozi do Flash a restartuje.
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

def write_eeprom(address, value, save_to_flash=False):
    ops = [
        (address, value),
        (76, 0x55AA),   # ChkSumEE - EEPROM potvrzeni
    ]
    if save_to_flash:
        ops.append((386, 0x5200))  # Save to Flash trigger - GBO restartuje
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
    flash = '--flash' in sys.argv
    write_eeprom(int(sys.argv[1]), int(sys.argv[2]), save_to_flash=flash)
