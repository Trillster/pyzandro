# About

`pyzandro` is a python library for querying Zandronum and QZandronum Doom servers.

# Install

```
pip install git+https://github.com/Trillster/pyzandro
```

# Usage

## Master server query (Zandronum)
```py
import pyzandro
servers = pyzandro.query_master('master.zandronum.com:15300')
```

This will return a list of addresses:
```py
['103.25.59.27:10666',
 '142.132.155.163:10666',
 '142.132.155.163:10668',
  ...
 '80.240.16.78:16566']
```

## Master server query (QZandronum)
```py
import pyzandro
servers = pyzandro.query_master('qzandronum.com:15300')
```

## Individial server query
```py
import pyzandro
serverinfo = pyzandro.query_server('103.25.59.27:10666')
```


Example result:

```py
{'response_code': 5660023,
 'response_code_meaning': 'accepted',
 'query_time': 1674498560,
 'version': '1.3.2-r2023-01-14 01:35:53 -0500 (TSPGv26) on Linux 5.4.0-137-generic',
 'response_flags_value': 1573001,
 'response_flags': {<SQF.GAMETYPE: 128>,
  <SQF.MAPNAME: 8>,
  <SQF.NAME: 1>,
  <SQF.NUMPLAYERS: 524288>,
  <SQF.PLAYERDATA: 1048576>},
 'name': b'[DUD] QC:DE: DEATHMATCH',
 'name_nocolor': '[DUD] QC:DE: DEATHMATCH',
 'mapname': 'QCDE18',
 'gametype': <GAMETYPE.DEATHMATCH: 3>,
 'gametype_instagib': 0,
 'gametype_buckshot': 0,
 'num_players': 4,
 'players': [{'name': b'CheeBeef',
   'name_nocolor': 'CheeBeef',
   'frags': 0,
   'ping': 0,
   'spec': 0,
   'bot': 1,
   'team': None,
   'time_on_server': 0},
  {'name': b'Hayden',
   'name_nocolor': 'Hayden',
   'frags': 0,
   'ping': 0,
   'spec': 0,
   'bot': 1,
   'team': None,
   'time_on_server': 0},
  {'name': b'Leontlady36',
   'name_nocolor': 'Leontlady36',
   'frags': 0,
   'ping': 0,
   'spec': 0,
   'bot': 1,
   'team': None,
   'time_on_server': 0},
  {'name': b'Slambert',
   'name_nocolor': 'Slambert',
   'frags': 0,
   'ping': 0,
   'spec': 0,
   'bot': 1,
   'team': None,
   'time_on_server': 0}]}
```

## Timeout setting
Both `query_master` and `query_server` can get an optional timeout parameter. Which is how long a client will wait for a response in seconds.

```
pyzandro.query_server('103.25.59.27:10666', timeout=2)
```

## Packet level logging

There is a packet level logging feature that outputs into jsonlines. Binary data is base64 encoded.

```
pyzandro.set_log_target('/home/user/pyzandro_packets.log')
```

### 

## Complete Example

An example querying all zandronum servers.

```py
import pyzandro
addresses = pyzandro.query_master('master.zandronum.com:15300')
for address in addresses:
    try:
        serverinfo = pyzandro.query_server(address)
        print(f'{address}: {serverinfo["name_nocolor"]}')
    except TimeoutError:
        print(f'{address}: timeout')
    except ConnectionResetError:
        print(f'{address}: connection reset')
```


# Running tests
Run `pytest` from the repo root.

# Protocol reference
https://wiki.zandronum.com/Launcher_protocol

# Credits

Written with the help of [kultasakaali](https://github.com/kultasakaali).
