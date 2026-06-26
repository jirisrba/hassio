#!/usr/bin/env python3
"""GBO-Aku Modbus RTU-over-TCP writer.

Pouziti:
  python3 gbo_modbus_fc16.py <address> <value>          # EEPROM zapis
  python3 gbo_modbus_fc16.py soc <percent>              # SOC target, EEPROM
  python3 gbo_modbus_fc16.py soc <percent> --flash      # SOC target, Flash (GBO restartuje)

EEPROM zapis: FC16 na address + ChkSumEE potvrzeni (addr 76 = 0x55AA).
Flash zapis:  cte 62 registru z addr 20, modifikuje SOC byte (offset 40),
              zapise 67 registru na addr 256, trigger restart (addr 386 = 0x5200).
"""
import sys
import socket
import struct
import time

HOST = '192.168.2.18'
PORT = 6770
SLAVE = 3
WAIT = 0.4  # GBO doc: min 350ms

# Flash write area: 5 extra registry za blokem 62, hodnoty z HMI packet capture
FLASH_EXTRA = [0xFFFF, 0xFFFF, 0x3780, 0x5042, 0x3780]

def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

def build_fc16_single(address, value):
    frame = struct.pack('>BBHHBH', SLAVE, 0x10, address, 1, 2, value & 0xFFFF)
    return frame + struct.pack('<H', crc16(frame))

def build_fc16_block(address, values):
    count = len(values)
    byte_count = count * 2
    header = struct.pack('>BBHHB', SLAVE, 0x10, address, count, byte_count)
    data = b''.join(struct.pack('>H', v & 0xFFFF) for v in values)
    frame = header + data
    return frame + struct.pack('<H', crc16(frame))

def build_fc3_read(address, count):
    frame = struct.pack('>BBHH', SLAVE, 0x03, address, count)
    return frame + struct.pack('<H', crc16(frame))

def transact(ops):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((HOST, PORT))
    for label, frame in ops:
        s.send(frame)
        time.sleep(WAIT)
        try:
            resp = s.recv(512)
            print(f'OK {label} resp={resp.hex()}', flush=True)
        except Exception as e:
            print(f'WARN {label}: {e}', flush=True)
    s.close()
    return None

def read_holding(address, count):
    frame = build_fc3_read(address, count)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((HOST, PORT))
    s.send(frame)
    time.sleep(WAIT)
    resp = s.recv(512)
    s.close()
    # FC3 response: slave(1) + FC(1) + bytecount(1) + data(N) + CRC(2)
    byte_count = resp[2]
    data = resp[3:3 + byte_count]
    values = [struct.unpack('>H', data[i:i+2])[0] for i in range(0, len(data), 2)]
    print(f'READ addr={address} count={count}: {[hex(v) for v in values[:5]]}...', flush=True)
    return values

def write_eeprom(address, value):
    transact([
        (f'addr={address} val={value}', build_fc16_single(address, value)),
        ('ChkSumEE addr=76', build_fc16_single(76, 0x55AA)),
    ])

def write_flash_soc(soc_percent):
    # 1. Precti aktualni blok (addr 20, 62 registru)
    regs = read_holding(20, 62)

    # 2. Modifikuj SOC target na offsetu 40 (= addr 60 v read space, addr 296 v flash space)
    upper_byte = regs[40] >> 8  # zachovaj horni byte (bod zalomu U/I charakteristiky)
    regs[40] = (upper_byte << 8) | (soc_percent & 0xFF)
    print(f'SOC target: {hex(regs[40])} (upper={upper_byte}, soc={soc_percent}%)', flush=True)

    # 3. Zapis 67 registru na flash write area (addr 256)
    block = regs + FLASH_EXTRA
    transact([
        (f'flash block addr=256 count={len(block)}', build_fc16_block(256, block)),
        ('flash trigger addr=386', build_fc16_single(386, 0x5200)),
    ])

if __name__ == '__main__':
    args = sys.argv[1:]
    flash = '--flash' in args
    args = [a for a in args if a != '--flash']

    if args[0] == 'soc':
        soc = int(args[1])
        if flash:
            write_flash_soc(soc)
        else:
            # EEPROM: precti horni byte z aktualni hodnoty
            current = read_holding(60, 1)[0]
            upper = current >> 8
            write_eeprom(98, (upper << 8) | soc)
    else:
        write_eeprom(int(args[0]), int(args[1]))
