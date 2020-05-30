import pandas as pd
import os
import re
import sys
from io import StringIO

ARP_FIELD_NAMES = ['Address', 'HWtype', 'HWaddress', 'Flags', 'Mask', 'Iface']
ARP_DASH_A_FIELD_COUNT = 7

class ArpData:

    def __init__(self, hostname, address, hw_type, hw_address, flags, mask, interface):
        self.hostname = hostname
        self.address = address
        self.hw_type = hw_type
        self.hw_address = hw_address
        self.flags = flags
        self.mask = mask
        self.interface = interface

    def __str__(self):
        d = self.as_dict()
        lines = []

        for k in d:
            lines.append("%s: %s" % (k, str(d[k])))

        return "\n".join(lines)
        
    def as_dict(self):
        d = {}
        d['ip'] = self.address
        d['hostname'] = self.hostname
        d['hardware type'] = self.hw_type
        d['MAC address'] = self.hw_address
        d['ARP Flags'] = self.flags
        d['ARP Mask'] = self.mask
        d['network interface'] = self.interface

        return d
        
    @staticmethod
    def from_dict(record_data):
        return ArpData(
            address = record_data['Address'],
            hw_type = record_data['HWtype'],
            hw_address  = record_data['HWaddress'],
            flags = record_data['Flags'],
            mask = record_data['Mask'],
            interface = record_data['Iface']
        )

# Reference: https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/
class ArpDataParsingException(Exception):
    status_code = 500

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        return { 'message': self.message }
    
def non_empty_rows(block_str):
    return [ r.strip() for r in block_str.split("\n") if r.strip() != '' ]

def is_mac_address(addr):
    return re.match(r'^([0-9a-f]{2}\:){5}[0-9a-f]{2}$', addr)

def is_arp_table_data(arp_data_string):
    rows = non_empty_rows(arp_data_string)

    if rows is None or not isinstance(rows, list) or len(rows) == 0:
        return False

    columns = [ c for c in rows[0].split(' ') if c != '' ]
    
    for column in ARP_FIELD_NAMES:
        if not column in columns:
            return False

    for column in columns:
        if not column in ARP_FIELD_NAMES:
            return False

    return True

def is_arp_dash_a_data(arp_data_string):
    rows = non_empty_rows(arp_data_string)

    if rows is None or not isinstance(rows, list) or len(rows) == 0:
        return False

    for row in rows:
        fields = [ f for f in row.split(' ') if f.strip() != '' ]
        if len(fields) != ARP_DASH_A_FIELD_COUNT:
            return False
        elif not re.match(r'^\(([0-9]{1,3}\.){3}[0-9]{1,3}\)$', fields[1]):
            return False
        elif fields[2] != 'at':
            return False
        elif not is_mac_address(fields[3]):
            return False
        elif not re.match(r'^\[.*\]$', fields[4]):
            return False
        elif fields[5] != 'on':
            return False

    return True

# Returns a list of character indices for the start of each column based on the given table header
def space_delimeted_col_offsets(table_header):
    offsets = []
    in_word = False
    
    for i in range(0, len(table_header)):
        if table_header[i] == ' ':
            in_word = False
        elif not in_word:
            offsets.append(i)
            in_word = True

    return offsets
            
def parse_table_row(row, col_offsets):
    values = []
    for i in range(0, len(col_offsets) - 1):
        starting_offset = col_offsets[i]
        ending_offset = col_offsets[i + 1]
        values.append(row[starting_offset:ending_offset].strip())

    final_col_offset = col_offsets[-1]
    values.append(row[final_col_offset:].strip())
        
    return values

def parse_arp_table_data(arp_data_string):
    rows = non_empty_rows(arp_data_string)

    # Need to be at least two rows (header row and one data row) for the data to be useful
    if rows is None or not isinstance(rows, list) or len(rows) < 2:
        return None

    col_offsets = space_delimeted_col_offsets(rows[0])
    arp_records = []

    # Start at index 1 to skip header row
    for i in range(1, len(rows)):
        arp_values = parse_table_row(rows[i], col_offsets)
        arp_records.append(
            ArpData(
                '', # No hostname information is available from ARP table data
                arp_values[0],
                arp_values[1],
                arp_values[2],
                arp_values[3],
                arp_values[4],
                arp_values[5]                
            )
        )
    
    return arp_records

def parse_arp_row(arp_row):
    head_and_tail = arp_row.split(' (')
    hostname = head_and_tail[0]
    head_and_tail = head_and_tail[1].split(') at ')
    ip_addr = head_and_tail[0]
    head_and_tail = head_and_tail[1].split(' [')
    hw_addr = head_and_tail[0]
    head_and_tail = head_and_tail[1].split('] on ')
    hw_type = head_and_tail[0]
    iface = head_and_tail[1]

    return ArpData(hostname, ip_addr, hw_type, hw_addr, '', '', iface)

def parse_arp_dash_a_data(arp_data_string):
    rows = non_empty_rows(arp_data_string)

    # Need to be at least two rows (header row and one data row) for the data to be useful
    if rows is None or not isinstance(rows, list) or len(rows) < 2:
        return None

    return [ parse_arp_row(row) for row in rows ]

#
# Example arp output:
#
# Address                  HWtype  HWaddress           Flags Mask            Iface
# 192.168.170.2            ether   00:50:56:e3:8e:d1   C                     eth0
# 192.168.170.254          ether   00:50:56:e1:ae:a6   C                     eth0
#
# Example 'arp -a' output:
#
# host.name (123.123.123.1) at 06:36:fd:14:2d:b6 [ether] on eth0
# other-host.name (123.123.123.2) at 06:36:fd:14:2d:b6 [ether] on eth0
# final-host.name (123.123.123.6) at 02:42:ac:11:00:02 [ether] on docker0
#
def parse_arp_data(arp_data_string):
    if arp_data_string is None or arp_data_string.strip() == '':
        return None 
    if is_arp_table_data(arp_data_string):
        return parse_arp_table_data(arp_data_string)
    elif is_arp_dash_a_data(arp_data_string):
        return parse_arp_dash_a_data(arp_data_string)
    else:
        print("Unable to parse ARP data string:\n%s" % arp_data_string)
        raise ArpDataParsingException("Failed to parse ARP data")

def parse_arp_file(arp_file):
    if not os.path.exists(arp_file):
        # TODO: Change to logging (and all other print statements
        print("File %s does not exist" % arp_file)
        raise ArpDataParsingException("Internal error occurred while attempting for parse the provided ARP data file")

    with open(arp_file, 'r') as f:
        return parse_arp_data(f.read())
