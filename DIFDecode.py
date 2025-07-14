# WXL DIF.DAT extraction code was made entirely by Needlenose! Please go check him out, most of this wouldn't have been possible without him!
# https://github.com/needlen0se
import json
import pandas as pd
import logging, coloredlogs
log = logging.getLogger(__name__)
coloredlogs.install("INFO")

def find_byte_pair(file_content, byte_pair):
    ### CREDIT TO NEEDLENOSE https://github.com/needlen0se ###
    '''Find the locations of a pair of bytes in a byte stream.'''
    try:
        match_locations = []
        pair_length = len(byte_pair)

        index = file_content.find(byte_pair)
        while index != -1:
            match_locations.append(index)
            index = file_content.find(byte_pair, index + pair_length)
        ### CREDIT TO NEEDLENOSE https://github.com/needlen0se ###
        return match_locations
    except:
        log.error(f"Couldn't find byte pair - is this a valid byte stream?")
        return None

def parse_wxl_dif(file_path):
    ### CREDIT TO NEEDLENOSE https://github.com/needlen0se ###
    '''Decodes the WXL DIF.DAT database for keys and data. Code by needlen0se'''
    log.debug(f"Parsing WXL DIF at path: '{file_path}'")
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()
        results = {}
        bytes_before_data = b"\xfa\xfa\x00\x00\x08\x52\x00\x00\x08\x48"
        match_locations = find_byte_pair(file_content, bytes_before_data)
        for match_location in match_locations:
            block_size = 2130
            match_data = file_content[match_location : match_location + block_size]
            match_data = match_data[10:]
            key_b = match_data[0:64]
            # Flags aren't important for this use case.. they're basically never used
            data_b = match_data[68:2116]
            exp_ts = int.from_bytes(match_data[2116:2120], byteorder="big")
            key_str = str(key_b.split(b"\x00")[0].decode("ascii"))
            data_str = str(data_b.split(b"\x00")[0].decode("cp1252"))
            if exp_ts == 0: # We'll ignore expiring data since we really just need the config stuff
                results[key_str] = data_str
        return results
    except:
        log.error("Couldn't decode DIF database - is this the correct file type?", exc_info=False)
        return None
    ### CREDIT TO NEEDLENOSE https://github.com/needlen0se ###

def parse_wxl_txt(file_path):
    ### written by Cable Contributes to Life ###
    '''Scrapes the TXT DIF-DB entry format for keys and data. Returns in dict'''
    log.debug(f"Parsing TXT at path: '{file_path}'")
    try:
        with open(file_path, "r") as file:
            file_content = file.readlines()
            file.close()
        results = {}
        l = 0
        for line in file_content:
            l += 1
            values = line.split(",") # split the entry data by comma
            if len(values) > 3:
                key = values[0].lstrip()
                data = values[3].lstrip().rstrip('"\n')
                if len(values) > 4:
                    exp_ts = values[4].lstrip()
                    try: exp_ts = int(exp_ts.strip('"'))
                    except: 
                        log.debug(f"Malformed data on line {l} - ignored")
                        continue
                    if exp_ts != 0:
                        log.debug(f"Expired key on line {l} - ignored")
                        continue
                key_str = key.strip('"')
                data_str = data.strip('"')
                results[key_str] = data_str
            else:
                log.debug(f"No valid data on line {l}")
        return results
    except:
        log.error("Couldn't decode DIF entries from TXT - is this a valid text file?")
        return None

def parse(file_path:str):
    if file_path.endswith(".dat"):
        log.info("Fetching database keys from compiled DIF file.")
        data = parse_wxl_dif(file_path=file_path)
        if data == None: return {} 
        else: return data
    elif file_path.endswith(".txt"):
        log.info("Fetching database keys from TXT file.")
        data = parse_wxl_txt(file_path=file_path)
        if data == None: return {} 
        else: return data
    else:
        log.warning("Unknown file type, attempting algorithm compatibility.")
        data = parse_wxl_dif(file_path=file_path)
        if not data:
            data = parse_wxl_txt(file_path=file_path)
        if not data:
            log.error("Couldn't find any database keys from the provided file.")
            return {}
        
