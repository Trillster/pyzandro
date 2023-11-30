import socket
import time
from io import BytesIO
from .huffman import huffencode, huffdecode
from .utils import next_string
from .utils import next_long
from .utils import next_short
from .utils import next_float
from .utils import next_byte
from .utils import split_hostport
from .utils import log_message
from .utils import PyZandroException
from enum import Enum
import struct
import traceback as tb

LAUNCHER_CHALLENGE = 199

class GAMETYPE(Enum):
    COOPERATIVE = 0
    SURVIVAL = 1
    INVASION = 2
    DEATHMATCH = 3
    TEAMPLAY = 4
    DUEL = 5
    TERMINATOR = 6
    LASTMANSTANDING = 7
    TEAMLMS = 8
    POSSESSION = 9
    TEAMPOSSESSION = 10
    TEAMGAME = 11
    CTF = 12
    ONEFLAGCTF = 13
    SKULLTAG = 14
    DOMINATION = 15

class SQF(Enum):
    NAME = 0x00000001
    URL = 0x00000002
    EMAIL = 0x00000004
    MAPNAME = 0x00000008
    MAXCLIENTS = 0x00000010
    MAXPLAYERS = 0x00000020
    PWADS = 0x00000040
    GAMETYPE = 0x00000080
    GAMENAME = 0x00000100
    IWAD = 0x00000200
    FORCEPASSWORD = 0x00000400
    FORCEJOINPASSWORD = 0x00000800
    GAMESKILL = 0x00001000
    BOTSKILL = 0x00002000
    DMFLAGS = 0x00004000
    LIMITS = 0x00010000
    TEAMDAMAGE = 0x00020000
    TEAMSCORES = 0x00040000
    NUMPLAYERS = 0x00080000
    PLAYERDATA = 0x00100000
    TEAMINFO_NUMBER = 0x00200000
    TEAMINFO_NAME = 0x00400000
    TEAMINFO_COLOR = 0x00800000
    TEAMINFO_SCORE = 0x01000000
    TESTING_SERVER = 0x02000000
    DATA_MD5SUM = 0x04000000
    ALL_DMFLAGS = 0x08000000
    SECURITY_SETTINGS = 0x10000000
    OPTIONAL_WADS = 0x20000000
    DEH = 0x40000000
    EXTENDED_INFO = 0x80000000

class SQF2(Enum):
    PWAD_HASHES = 0x00000001
    COUNTRY = 0x00000002
    GAMEMODE_NAME = 0x00000004
    GAMEMODE_SHORTNAME = 0x00000008

def nocolor(name_bytes):
    import re
    return str(re.sub(rb'\x1c((\[[^\]]+\])|.)', b'', name_bytes), 'UTF-8')

def is_team_game(mode):
    teammodes = {
        GAMETYPE.TEAMPLAY,
        GAMETYPE.TEAMLMS,
        GAMETYPE.TEAMPOSSESSION,
        GAMETYPE.TEAMGAME,
        GAMETYPE.CTF,
        GAMETYPE.ONEFLAGCTF,
        GAMETYPE.SKULLTAG,
        GAMETYPE.DOMINATION}
    return GAMETYPE(mode) in teammodes

def dissect_flags(Enumtype, combined_flags):
    enumvalues = [e.value for e in list(Enumtype)]
    result = set()
    for i in range(0, 32):
        current_flag = 1 << i
        if current_flag & combined_flags != 0:
            result.add(Enumtype(current_flag))
    return result

def combine_flags(Enumtype, enum_values):
    result = 0
    for ev in enum_values:
        result |= Enumtype(ev).value
    return result

def parse_response(response):
    streamobj = BytesIO(response)
    r = {}
    r['response_code'] = next_long(streamobj)
    if r['response_code'] == 5660023:
        r['response_code_meaning'] = 'accepted'
    elif r['response_code'] == 5660024:
        # IP has made a request in the past sv_queryignoretime seconds
        r['response_code_meaning'] = 'denied'
    elif r['response_code'] == 5660025:
        r['response_code_meaning'] = 'banned'
    else:
        r['response_code_meaning'] = 'unknown'

    # return when receiving non accepted response code
    if r['response_code'] != 5660023:
        return

    r['query_time'] = next_long(streamobj)
    r['version'] = str(next_string(streamobj), 'utf-8')
    response_flags_value = next_long(streamobj)
    response_flags = dissect_flags(SQF, response_flags_value)
    r['response_flags_value'] = response_flags_value
    r['response_flags'] = response_flags

    if SQF.NAME in response_flags:
        name = next_string(streamobj)
        r['name'] = nocolor(name)
        r['name_formatted'] = str(name, 'utf-8')
    if SQF.URL in response_flags:
        r['url'] = str(next_string(streamobj), 'utf-8')
    if SQF.EMAIL in response_flags:
        r['email'] = str(next_string(streamobj), 'utf-8')
    if SQF.MAPNAME in response_flags:
        r['mapname'] = str(next_string(streamobj), 'utf-8')
    if SQF.MAXCLIENTS in response_flags:
        r['maxclients'] = next_byte(streamobj)
    if SQF.MAXPLAYERS in response_flags:
        r['maxplayers'] = next_byte(streamobj)
    if SQF.PWADS in response_flags:
        n_pwads = next_byte(streamobj)
        r['pwads'] = []
        for i in range(n_pwads):
            r['pwads'].append(str(next_string(streamobj), 'utf-8'))
    if SQF.GAMETYPE in response_flags:
        r['gametype'] = GAMETYPE(next_byte(streamobj)).value
        r['gametype_instagib'] = next_byte(streamobj)
        r['gametype_buckshot'] = next_byte(streamobj)
    if SQF.GAMENAME in response_flags:
        r['gamename'] = str(next_string(streamobj), 'utf-8')
    if SQF.IWAD in response_flags:
        r['iwad'] = str(next_string(streamobj), 'utf-8')
    if SQF.FORCEPASSWORD in response_flags:
        r['forcepassword'] = next_byte(streamobj)
    if SQF.FORCEJOINPASSWORD in response_flags:
        r['forcejoinpassword'] = next_byte(streamobj)
    if SQF.GAMESKILL in response_flags:
        r['gameskill'] = next_byte(streamobj)
    if SQF.BOTSKILL in response_flags:
        r['botskill'] = next_byte(streamobj)
    if SQF.DMFLAGS in response_flags:
        r['dmflags'] = next_long(streamobj)
        r['dmflags2'] = next_long(streamobj)
        r['compatflags'] = next_long(streamobj)
    if SQF.LIMITS in response_flags:
        r['fraglimit'] = next_short(streamobj)
        r['timelimit'] = next_short(streamobj)
        if r['timelimit'] > 0:
            r['timeleft'] = next_short(streamobj)
        r['duellimit'] = next_short(streamobj)
        r['pointlimit'] = next_short(streamobj)
        r['winlimit'] = next_short(streamobj)
    if SQF.TEAMDAMAGE in response_flags:
        r['teamdamage'] = next_float(streamobj)
    if SQF.TEAMSCORES in response_flags:
        r['teamscores_blue'] = next_short(streamobj)
        r['teamscores_red'] = next_short(streamobj)
    if SQF.NUMPLAYERS in response_flags:
        r['num_players'] = next_byte(streamobj)
    if SQF.PLAYERDATA in response_flags:
        players = []
        r['players'] = players
        for i in range(r['num_players']):
            player = {}
            name = next_string(streamobj)
            player['name'] = nocolor(name)
            player['name_formatted'] = str(name, 'utf-8')
            player['frags'] = next_short(streamobj)
            player['ping'] = next_short(streamobj)
            player['spec'] = next_byte(streamobj)
            player['bot'] = next_byte(streamobj)
            if is_team_game(r['gametype']):
                player['team'] = next_byte(streamobj)
            else:
                player['team'] = -1
            player['time_on_server'] = next_byte(streamobj)
            players.append(player)
    if SQF.TEAMINFO_NUMBER in response_flags:
        r['teaminfo_number'] = next_byte(streamobj)
    if SQF.TEAMINFO_NAME in response_flags:
        r['teaminfo_names'] = []
        for _ in range(r['teaminfo_number']):
            r['teaminfo_names'].append(str(next_string(streamobj), 'utf-8'))
    if SQF.TEAMINFO_COLOR in response_flags:
        r['teaminfo_colors'] = []
        for _ in range(r['teaminfo_number']):
            r['teaminfo_colors'].append(next_long(streamobj))
    if SQF.TEAMINFO_SCORE in response_flags:
        r['teaminfo_scores'] = []
        for _ in range(r['teaminfo_number']):
            r['teaminfo_scores'].append(next_short(streamobj))
    if SQF.TESTING_SERVER in response_flags:
        r['testing_server'] = next_byte()
        r['testing_server_binary'] = str(next_string(streamobj), 'utf-8')
    if SQF.DATA_MD5SUM in response_flags:
        r['data_md5sum'] = str(next_string(streamobj), 'utf-8')
    if SQF.ALL_DMFLAGS in response_flags:
        num_dmflags = next_byte()
        r['all_dmflags'] = []
        for _ in num_dmflags:
            r['all_dmflags'].append(next_long(streamobj))
    if SQF.SECURITY_SETTINGS in response_flags:
        r['security_settings'] = next_byte(streamobj)
    if SQF.OPTIONAL_WADS in response_flags:
        n_optional_wads = next_byte()
        r['optional_wads'] = []
        for _ in range(n_optional_wads):
            r['optional_wads'].append(next_byte(streamobj))
    if SQF.DEH in response_flags:
        n_deh = next_byte(streamobj)
        r['deh'] = []
        for _ in range(n_deh):
            r['deh'].append(str(next_string(streamobj), 'utf-8'))
    if SQF.EXTENDED_INFO in response_flags:
        r['extended_info'] = next_long(streamobj)
        extended_response_flags = dissect_flags(SQF2, r['extended_info'])
        if SQF2.PWAD_HASHES in extended_response_flags:
            n_pwad_hashes = next_byte(streamobj)
            r['pwad_hashes'] = []
            for _ in range(n_pwad_hashes):
                r['pwad_hashes'].append(str(next_string(streamobj), 'utf-8'))
        if SQF2.COUNTRY in extended_response_flags:
            r['country'] = bytes([next_byte(streamobj), next_byte(streamobj), next_byte(streamobj)]).decode('ascii')
        # 3.2 alpha and above only
        if SQF2.GAMEMODE_NAME in extended_response_flags:
            r['gamemode_name'] = str(next_string(streamobj), 'utf-8')
        if SQF2.GAMEMODE_SHORTNAME in extended_response_flags:
            r['gamemode_shortname'] = str(next_string(streamobj), 'utf-8')
    return r

def query_server(address, flags=[SQF.NAME, SQF.MAPNAME, SQF.NUMPLAYERS, SQF.PLAYERDATA, SQF.GAMETYPE], timeout=3, e_flags=[]):
    # if we request playerdata we MUST also request gametype, because the presence
    # of the 'team' field depends in the playerdata response depends on the gametype
    # for non team games the byte representing the player's team is simply not sent
    # if extended flags are requested, SQF_EXTENDED_INFO must also be requested
    try:
        recv_data = b''
        huffdecoded = b''
        log_message(call='pyzandro.query_server() {', address=address, flags=str(flags), timeout=timeout, e_flags=str(e_flags))
        host, port = split_hostport(address)
        if SQF.PLAYERDATA in flags and SQF.GAMETYPE not in flags:
            flags.append(SQF.GAMETYPE)
        if len(e_flags) > 0 and SQF.EXTENDED_INFO not in flags:
            flags.append(SQF.EXTENDED_INFO)
        query_flags = combine_flags(SQF, flags)
        extended_flags = combine_flags(SQF2, e_flags)
        unencoded_query = struct.pack('<LLLL',
            LAUNCHER_CHALLENGE,
            query_flags,
            int(time.time()),
            extended_flags)
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_data = huffencode(unencoded_query)
        client.settimeout(timeout)
        client.sendto(send_data, (host, port))
        log_message(call='pyzandro.query_server() sendto', unencoded_query=unencoded_query, send_data=send_data, address=(host, port))
        recv_data = client.recv(1024)
        huffdecoded = huffdecode(recv_data)
        log_message(call='pyzandro.query_server() recv', huffdecoded=huffdecoded, recv_data=recv_data)
        return parse_response(huffdecoded)
    except Exception as e:
        traceback = ''.join(tb.format_exception(None, e, e.__traceback__))
        log_message(call='pyzandro.query_server() exception', huffdecoded=huffdecoded, recv_data=recv_data, traceback=traceback)
        raise
    finally:
        log_message(call='pyzandro.query_server() }')
