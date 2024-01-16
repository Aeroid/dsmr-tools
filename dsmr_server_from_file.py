import sys
import asyncio

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

async def serve_client(reader, writer):
    r=0
    while True:
        try:
            if r >= len(records):
                r=0
            response = records[r]
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
    host = 'localhost'
    port = sys.argv[1]
    filename = sys.argv[2]
    
    records = read_text_records(filename)
    print ("Port:",port,"File:",filename,"Records:",len(records))
    kit = "------------------------------------------------------------"[:len(records)-1]
    if len(records) > 0:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("                                                                        \r");
