import asyncio
import sys
import argparse
import re
from ctypes import c_ushort

sys.stdout.reconfigure(encoding='latin1')

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

def reformat_evcc(packet):
    """ for evcc turn 
        1-0:1.7.0*255(-000333.00*W)
        1-0:2.7.0*255(01000.00000*W)
      into  
        1-0:1.7.0(00000.00000*kW)
        1-0:2.7.0(00001.33300*kW)
    """
    packet = re.sub(r'(\/[.\w]* [.\w]*)', r'\1 evcc', packet)
    # reead production
    production_re = re.search(r'(1\-0\:2\.7\.0\*255)\((.+)\*(.+)\)', packet)
    if production_re:
        p = [float(production_re.group(2)), production_re.group(3)]
        if p[1] == "MW":
            p[0] = p[0]*1000.0
            p[1] = "kW"
        if p[1] == "W":
            p[0] = p[0]/1000.0
            p[1] = "kW"
    else:
        p = [0.0,"kW"]
    
    # remove production
    packet = re.sub(r'1\-0\:2\.7\.0.*[\n\r]*', '', packet)

    # read consumption
    consumption_re = re.search(r'(1\-0\:1\.7\.0\*255)\((.+)\*(.+)\)', packet)
    c = [float(consumption_re.group(2)),consumption_re.group(3)]
    if c[1] == "MW":
        c[0] = c[0]*1000.0
        c[1] = "kW"
    if c[1] == "W":
        c[0] = c[0]/1000.0
        c[1] = "kW"

    # turn negative consumption into positive production
    if (c[0] < 0):
        p[0] = p[0] - c[0] 
        c = [0.0, "kW"]
    # p[0] = p[0] + 0.4711
    # W -> kW
    production = "1-0:2.7.0*255({:011.5f}*{})".format(p[0],p[1])
    consumption = "1-0:1.7.0*255({:011.5f}*{})".format(c[0],c[1])
    insert = consumption +"\r\n"+ production
    packet = re.sub(r'(1\-0\:1\.7\.0\*255)\((.+)\)', insert, packet)
    
    # remove *255
    packet = re.sub(r'(\d)(\*255)\(', r'\1(', packet)
    
    return packet;

def strhex(s):
    return ":".join("{:02x}".format(ord(c)) for c in s)

#   [/]=>->=[/] connected [\]=>->=[\]        disconnected  [_]X>->X[_]   spinner: |/-\

async def handle_client(reader, writer):
    global dsmr
    global dsmr_available
    while True:
        dsmr = await reader.read(4000)
        if not dsmr:
            break
        dsmr = dsmr.decode('latin1')
        if (generate_evcc):
            dsmr = reformat_evcc(dsmr)
        if (generate_crc):
            dsmr = add_crc(dsmr)
        dsmr_available.set();
        #print(dsmr,end="")

async def remote_tcp_connection(host, port):
    while True:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            await handle_client(reader, writer)
        except ConnectionError:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            break

async def serve_client(reader, writer):
    global dsmr
    global dsmr_available
    print(writer.get_extra_info('peername'))
    while True:
        try:
            await dsmr_available.wait()
            #print("dsmr_available", len(dsmr))
            response = dsmr;
            writer.write(response.encode('latin1'))
            await writer.drain()
            dsmr_available.clear()          
        except  (asyncio.CancelledError, ConnectionError, ConnectionResetError):
            break

async def serve_latest_output(host, port):
    server = await asyncio.start_server(serve_client, host, port)
    async with server:
        await server.serve_forever()

async def main():
    remote_task = asyncio.create_task(remote_tcp_connection(remote_host, remote_port))
    server_task = asyncio.create_task(serve_latest_output(server_host, server_port))

    await asyncio.gather(remote_task,server_task)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DMSR bridge to re-format DSMR suitable for evcc.')
    parser.add_argument('remotehost', help='host to read from')
    parser.add_argument('remoteport', help='TCP port to read from')
    parser.add_argument('serverport', help='TCP port to serve from')
    parser.add_argument('-c', '--crc', action='store_true', help='Enable CRC mode and removes any junk')
    parser.add_argument('-e', '--evcc', action='store_true', help='Enable EVCC mode (https://github.com/evcc-io/evcc/issues/11772)')
    args = parser.parse_args()
    server_host = '0.0.0.0'
    generate_crc = args.crc
    generate_evcc = args.evcc
    if (generate_evcc):
        generate_crc = True

    remote_host = args.remotehost
    remote_port = int(args.remoteport)
    server_port = int(args.serverport)

    dsmr_available = asyncio.Event()
    dsmr_available.clear();
    dsmr_status_change = asyncio.Event()
    dsmr_status_change.clear();
    dsmr = "X";

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()

    
