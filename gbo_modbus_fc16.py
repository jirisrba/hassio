#!/usr/bin/env python3
"""FC16 (Write Multiple Registers) pro GBO RTU-over-TCP.

Pouziti:
  python3 gbo_modbus_fc16.py <address> <value>
  python3 gbo_modbus_fc16.py <address> <value> --flash

Bez --flash: zapise value na address + EEPROM potvrzeni (addr 76 = 0x55AA).
S --flash:   zapise value primo na flash area (addr 256+) bez ChkSumEE,
             pak trigger 0x5200 na addr 386 = GBO ulozi Flash a restartuje.

Flash area SOC target: addr 296 (= 256 + 40), hodnota = 0xFF00 | soc_percent
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

def write_registers(ops):
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

def write_eeprom(address, value):
    write_registers([
        (address, value),
        (76, 0x55AA),   # ChkSumEE - EEPROM potvrzeni
    ])

def write_flash(address, value):
    # addr 256+ je flash write area - bez ChkSumEE, pak restart trigger
    write_registers([
        (address, value),
        (386, 0x5200),  # Flash commit + GBO restart
    ])

if __name__ == '__main__':
    addr = int(sys.argv[1])
    val  = int(sys.argv[2])
    if '--flash' in sys.argv:
        write_flash(addr, val)
    else:
        write_eeprom(addr, val)
