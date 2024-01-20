import sys
import asyncio
import argparse
import re
from ctypes import c_ushort

sys.stdout.reconfigure(encoding='latin1')

def read_text_records(filename):
    with open(filename, 'rb') as f:
        records = []
        record = []
        wholefile = f.read().decode('latin1')
        for line in wholefile.splitlines(keepends=True):
            record.append(line)
            if line == '\n':
                records.append(''.join(record))
                record = []

        if record:
            records.append(''.join(record))

        return records

crc16_tab = []
def crc16(telegram):
    """
    Calculate the CRC16 value for the given telegram

    :param str telegram:
    """
    crcValue = 0x0000

    if len(crc16_tab) == 0:
        for i in range(0, 256):
            crc = c_ushort(i).value
            for j in range(0, 8):
                if (crc & 0x0001):
                    crc = c_ushort(crc >> 1).value ^ 0xA001
                else:
                    crc = c_ushort(crc >> 1).value
            crc16_tab.append(hex(crc))

    for c in telegram:
        d = ord(c)
        tmp = crcValue ^ d
        rotated = c_ushort(crcValue >> 8).value
        crcValue = rotated ^ int(crc16_tab[(tmp & 0x00ff)], 0)

    return crcValue

def add_crc(packet):
    checksum_contents = re.search(r'\/.+\!', packet, re.DOTALL)
    crc = crc16(checksum_contents.group(0))
    
    return "{}{:04X}\r\n".format(checksum_contents.group(0) , crc)

async def serve_client(reader, writer):
    r=0
    while True:
        try:
            if r >= len(records):
                r=0
            response = add_crc(records[r])
            print("["+(kit[:r])+"+"+(kit[:len(kit)-r])+"] :",len(response)," byte\r",end="")
            r+=1
            writer.write(response.encode())
            await writer.drain()
            await asyncio.sleep(2)
        except  (asyncio.CancelledError, ConnectionError, ConnectionResetError):
            print("                                                                        \r",end="");
            break
            
async def main():
    server = await asyncio.start_server(serve_client, host, port)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple script with command-line options.')
    parser.add_argument('port', help='TCP port to serve from')
    parser.add_argument('file', help='data file to read DSMR paket from')
    parser.add_argument('-c', '--crc', action='store_true', help='Enable CRC mode')
    args = parser.parse_args()
    host = '0.0.0.0'
    port = args.port
    filename = args.file
    generate_crc = args.crc
    
    records = read_text_records(filename)
    print ("Port:",port,"File:",filename,"Records:",len(records))
    kit = "------------------------------------------------------------"[:len(records)-1]
    if len(records) > 0:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("                                                                        \r");
