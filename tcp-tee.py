import asyncio
import sys

sys.stdout.reconfigure(encoding='latin1')

# Remote server address and port
remote_host = "192.168.180.50"
remote_port = 5000

# TCP server address and port
server_host = "0.0.0.0"
server_port = 5002

remote_host = sys.argv[1]
remote_port = int(sys.argv[2])
server_port = int(sys.argv[3])

dsmr_available = asyncio.Event()
dsmr_available.clear();
dsmr_status_change = asyncio.Event()
dsmr_status_change.clear();
dsmr = "X";

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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()

    