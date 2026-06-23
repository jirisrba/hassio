#!/usr/bin/env python3
"""FC16 (Write Multiple Registers) pro GBO RTU-over-TCP.

Pouziti:
  python3 gbo_modbus_fc16.py <addr> <value>          - jeden zapis
  python3 gbo_modbus_fc16.py soc <soc_percent>       - zapise SOC cil + EEPROM potvrzeni
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

def send_frames(frames):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((HOST, PORT))
    for addr, val, frame in frames:
        s.send(frame)
        time.sleep(WAIT)
        try:
            resp = s.recv(256)
            print(f'OK addr={addr} value={val} resp={resp.hex()}', flush=True)
        except Exception as e:
            print(f'WARN addr={addr} no response: {e}', flush=True)
    s.close()

if __name__ == '__main__':
    if sys.argv[1] == 'soc':
        # Bezpecny mod: addr 98 + EEPROM potvrzeni addr 76, jedno TCP spojeni
        soc = int(sys.argv[2])
        # Zachovani horního byte ze senzoru neni mozne bez cteni - predpokladame 0xFF
        # Pokud sensor.gbo_eeudczadana_raw je dostupny, upper byte se pocita v HA skriptu
        upper = int(sys.argv[3]) if len(sys.argv) > 3 else 255
        new_val = upper * 256 + soc
        frames = [
            (98, new_val, build_frame(98, new_val)),
            (76, 21930,   build_frame(76, 21930)),
        ]
        send_frames(frames)
    else:
        addr = int(sys.argv[1])
        val  = int(sys.argv[2])
        send_frames([(addr, val, build_frame(addr, val))])
