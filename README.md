# dsmr-tools

I use an EasyMeter Q3D for my main energy incl delivery of solar panel generated energy, the second one is a "private" one just to meter my main consumption by a heat pump. Both have IR interfaces which are bridged to ethernet TCP Port 5000 by COM-1 boxes from co-met.info. These COM-1 boxes have a few issues. [see also](https://github.com/ndokter/dsmr_parser/pull/92#issue-1052354779)

One very annoying issue that they only accept one TCP connection. Further connections are simply not accepted. 

Here are few very simple scripts to run services that connect and read the stream of DSMR packets and serve the last one and any any further one to clients that connect to it. This allows multiple clients to consume the DMSR data streams in parallel.

Nothing fancy. My [Home Assistant](https://www.home-assistant.io/integrations/dsmr) is now redirected to receive from this service. 
My [evcc](https://evcc.io/) is connected to a separate instance of the service utilizing a tranformation of the dsmr telegrams to make the suitable for the [GotSmart](https://github.com/basvdlei/gotsmart) parser used by evcc. [see also](https://github.com/evcc-io/evcc/issues/11772)

## tcp-tee-crc.py

    usage: tcp-tee-crc.py [-h] [-c] [-e] remotehost remoteport serverport
    
    DMSR bridge to re-format DSMR suitable for evcc.
    
    positional arguments:
      remotehost  host to read from
      remoteport  TCP port to read from
      serverport  TCP port to serve from

    options:
      -h, --help  show this help message and exit
      -c, --crc   Enable CRC mode and removes any junk
      -e, --evcc  Enable EVCC mode (https://github.com/evcc-io/evcc/issues/11772)

### Example
    python3 tcp-tee-crc.py 192.168.180.98 5000 5002

Connects to 192.168.180.98 port 5000/tcp and accepts connections on port 5002. The telegrams a forwarded untouched, incl all junk they might contain or are padded with.

    python3 tcp-tee-crc.py 192.168.180.98 5000 5003 --evcc

Removes any junk and modifies the telegrams:
- adds CRC16, 
- turns negative consumption (1.7.0) into positive production (2.7.0), 
- removes "*255", 
- turns watts into kilo watts.

## dsmr_from_file.py

    python3 dsmr_from_file.py heat.dsmr 

Reads DSMR packets stored in a file and outputs them.

## dsmr_server_from_file.py

    python3 dsmr_server_from_file.py heat.dsmr 4002

Reads DSMR packets stored in a file, accepts connections on port 4002 and serves them round-robin to emulate a DSMR source.

