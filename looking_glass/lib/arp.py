import pandas as pd
import os
import re
import sys
from io import StringIO

from .internal_error import InternalError

IP_ADDRESS_FIELD = 'IP Address'
HOSTNAME_FIELD = 'Hostname'
HARDWARE_TYPE_FIELD = 'Hardware Type'
MAC_ADDRESS_FIELD = 'MAC Address'
ARP_FLAGS_FIELD = 'ARP Flags'
SUBNET_MASK_FIELD = 'Subnet Mask'
INTERFACE_NAME_FIELD = 'Interface Name'
RECORD_TYPE_FIELD = 'Record Type'

ARP_FIELD_NAMES_BY_TYPE = {
    IP_ADDRESS_FIELD: ['IP address', 'Address', 'Internet Address'],
    HOSTNAME_FIELD: [], # Not contained in ARP table data
    HARDWARE_TYPE_FIELD: ['HW type', 'HWtype'],
    MAC_ADDRESS_FIELD: ['HW address', 'HWaddress', 'Physical Address'],
    ARP_FLAGS_FIELD: ['Flags'],
    SUBNET_MASK_FIELD: ['Mask'],
    INTERFACE_NAME_FIELD: ['Iface'],
    RECORD_TYPE_FIELD: ['Type'],
}

ARP_FIELD_NAMES = [ item for lst in ARP_FIELD_NAMES_BY_TYPE.values() for item in lst ]
ARP_DASH_A_FIELD_COUNT = 7

class ArpTableParser:
    
    def __init__(self, header_row):
        self.ip_addr_start_offset = None
        self.ip_addr_end_offset = None
        self.hw_type_start_offset = None
        self.hw_type_end_offset = None
        self.hw_addr_start_offset = None
        self.hw_addr_end_offset = None
        self.arp_flags_start_offset = None
        self.arp_flags_end_offset = None
        self.subnet_mask_start_offset = None
        self.subnet_mask_end_offset = None
        self.network_interface_start_offset = None
        self.network_interface_end_offset = None
        self.record_type_start_offset = None
        self.record_type_end_offset = None

        self.set_offsets(header_row)

    @staticmethod
    def col_headers_with_offsets(header_row):
        headers_with_offsets = {}
        curr_word = ''
        prev_word = None
        start_of_curr_word = 0
        
        for i in range(0, len(header_row)):
            char = header_row[i]
            if char == ' ':
                if curr_word == '':
                    continue
                elif curr_word.endswith(' '):
                    # There should never be two spaces between words in a column name
                    raise InternalError("Unrecognized ARP column name '%s' encountered" % curr_word.strip())
                else:
                    curr_word += ' '

            else:
                if curr_word == '':
                    start_of_curr_word = i
                    
                    if prev_word is not None:
                        headers_with_offsets[prev_word]['end'] = i
                        prev_word = None
                    
                curr_word += header_row[i]

            if curr_word in ARP_FIELD_NAMES: 
                headers_with_offsets[curr_word] = { 'start': start_of_curr_word, 'end': None }
                prev_word = curr_word
                curr_word = ''

        if curr_word != '':
            raise InternalError("Unknown/incomplete ARP column name '%s' encountered" % curr_word)
                
        return headers_with_offsets
        
    # TODO: Add unit test
    def set_offsets(self, header_row):
        headers_with_offsets = self.col_headers_with_offsets(header_row)
        
        for col_name in headers_with_offsets:
            start_offset = headers_with_offsets[col_name]['start']
            end_offset = headers_with_offsets[col_name]['end']
            
            if col_name in ARP_FIELD_NAMES_BY_TYPE[IP_ADDRESS_FIELD]:
                self.ip_addr_start_offset = start_offset
                self.ip_addr_end_offset = end_offset
            elif col_name in ARP_FIELD_NAMES_BY_TYPE[HARDWARE_TYPE_FIELD]:
                self.hw_type_start_offset = start_offset
                self.hw_type_end_offset = end_offset
            elif col_name in ARP_FIELD_NAMES_BY_TYPE[MAC_ADDRESS_FIELD]:
                self.hw_addr_start_offset = start_offset
                self.hw_addr_end_offset = end_offset
            elif col_name in ARP_FIELD_NAMES_BY_TYPE[ARP_FLAGS_FIELD]:
                self.arp_flags_start_offset = start_offset
                self.arp_flags_end_offset = end_offset
            elif col_name in ARP_FIELD_NAMES_BY_TYPE[SUBNET_MASK_FIELD]:
                self.subnet_mask_start_offset = start_offset
                self.subnet_mask_end_offset = end_offset
            elif col_name in ARP_FIELD_NAMES_BY_TYPE[INTERFACE_NAME_FIELD]:
                self.network_interface_start_offset = start_offset
                self.network_interface_end_offset = end_offset
            elif col_name in ARP_FIELD_NAMES_BY_TYPE[RECORD_TYPE_FIELD]:
                self.record_type_start_offset = start_offset
                self.record_type_end_offset = end_offset
            else:
                raise InternalError("Unrecognized ARP column name '%s' encountered" % col_name)
            
    def extract_col_val(self, row, start_offset, end_offset):
        # Note: an end offset of None will extract the substring from start_offset to the end of the string
        # (which is what we want)
        return empty_str_as_none(row[start_offset:end_offset].strip())
                
    def parse_row(self, row):
        arp_record = ArpRecord()
        
        if self.ip_addr_start_offset is not None:
            arp_record.ip_address = self.extract_col_val(row, self.ip_addr_start_offset, self.ip_addr_end_offset)
            
        if self.hw_type_start_offset is not None:
            arp_record.hw_type = self.extract_col_val(row, self.hw_type_start_offset, self.hw_type_end_offset)
            
        if self.hw_addr_start_offset is not None:
            arp_record.hw_address = self.extract_col_val(row, self.hw_addr_start_offset, self.hw_addr_end_offset)
            
        if self.arp_flags_start_offset is not None:
            arp_record.flags = self.extract_col_val(row, self.arp_flags_start_offset, self.arp_flags_end_offset)
            
        if self.subnet_mask_start_offset is not None:
            arp_record.mask = self.extract_col_val(row, self.subnet_mask_start_offset, self.subnet_mask_end_offset)
            
        if self.network_interface_start_offset is not None:
            arp_record.interface = self.extract_col_val(row, self.network_interface_start_offset, self.network_interface_end_offset)

        if self.record_type_start_offset is not None:
            arp_record.record_type = self.extract_col_val(row, self.record_type_start_offset, self.record_type_end_offset)

        return arp_record
    
class ArpRecord:

    def __init__(self, hostname = None, ip_address = None, hw_type = None, hw_address = None, flags = None, mask = None, interface = None, record_type = None):
        self.hostname = empty_str_as_none(hostname)
        self.ip_address = empty_str_as_none(ip_address)
        self.hw_type = empty_str_as_none(hw_type)
        self.hw_address = empty_str_as_none(hw_address)
        self.flags = empty_str_as_none(flags)
        self.mask = empty_str_as_none(mask)
        self.interface = empty_str_as_none(interface)
        self.record_type = empty_str_as_none(record_type)

    def __str__(self):
        d = self.as_dict()
        lines = []

        for k in d:
            lines.append("%s: %s" % (k, str(d[k])))

        return "\n".join(lines)

    def as_dict(self):
        d = {}
        
        d[IP_ADDRESS_FIELD] = self.ip_address
        d[HOSTNAME_FIELD] = self.hostname
        d[HARDWARE_TYPE_FIELD] = self.hw_type
        d[MAC_ADDRESS_FIELD] = self.hw_address
        d[ARP_FLAGS_FIELD] = self.flags
        d[SUBNET_MASK_FIELD] = self.mask
        d[INTERFACE_NAME_FIELD] = self.interface
        d[RECORD_TYPE_FIELD] = self.record_type
        
        return d

###
### "Static" utility functions
###

def empty_str_as_none(s):
    if s == '':
        return None
    else:
        return s
    
def non_empty_rows(block_str):
    return [ r.strip() for r in block_str.split("\n") if r.strip() != '' ]

def is_mac_address(addr):
    return re.match(r'^([0-9a-f]{2}\:){5}[0-9a-f]{2}$', addr)

def is_windows_network_interface_description(row):
    return re.match(r'^Interface\: ([0-9]{1,3}\.){3}[0-9]{1,3} \-\-\- 0x[0-9a-f]+$', row.strip())

def is_windows_arp_data(rows):
    return len([ r for r in rows if is_windows_network_interface_description(r) ]) > 0

def is_arp_table_data_header(header_row):
    columns = [ c for c in header_row.split(' ') if c != '' ]

    incomplete_header = None
    for column in columns:
        
        if incomplete_header is not None:
            column = incomplete_header + ' ' + column
            
        if not column in ARP_FIELD_NAMES:
            if incomplete_header is None:
                incomplete_header = column
                continue
            
            return False
        else:
            incomplete_header = None

    return True

def is_arp_dash_a_data(rows):
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

def split_windows_arp_into_tables(rows):
    tables = []
    curr_table_rows = []
    curr_interface_addr = None
    
    for row in rows:
        if is_windows_network_interface_description(row):
            if len(curr_table_rows) > 0:
                tables.append(curr_table_rows)
                curr_table_rows = []

            # TODO: Add edges from the source interface to all listed connections (do this for all ARP table data)
            curr_interface_addr = row.split(' ')[1]
        elif is_arp_table_data_header(row):
            if not len(curr_table_rows) == 0:
                raise InternalError("Out-of-order header for interface '%s'" % curr_interface_addr)

            curr_table_rows.append(row)
        else:
            if len(curr_table_rows) == 0:
                raise InternalError("Missing header for interface '%s'" % curr_interface_addr)

            curr_table_rows.append(row)

    if len(curr_table_rows) > 0:
        tables.append(curr_table_rows)

    return tables

def parse_arp_table_data(rows):
    # Need to be at least two rows (header row and one data row) for the data to be useful
    if len(rows) < 2:
        return None

    table_parser = ArpTableParser(rows[0])
    return [ table_parser.parse_row(row) for row in rows[1:] ] # Start at index 1 to skip header row

def parse_arp_dash_a_row(arp_row):
    head_and_tail = arp_row.split(' (')
    hostname = head_and_tail[0]
    head_and_tail = head_and_tail[1].split(') at ')
    ip_addr = head_and_tail[0]
    head_and_tail = head_and_tail[1].split(' [')
    hw_addr = head_and_tail[0]
    head_and_tail = head_and_tail[1].split('] on ')
    hw_type = head_and_tail[0]
    iface = head_and_tail[1]

    return ArpRecord(hostname, ip_addr, hw_type, hw_addr, '', '', iface)

def parse_arp_dash_a_data(rows):
    # Need to be at least two rows (header row and one data row) for the data to be useful
    if len(rows) < 2:
        return None

    return [ parse_arp_dash_a_row(row) for row in rows ]

#
# Example arp output:
#
# Address                  HWtype  HWaddress           Flags Mask            Iface
# 192.168.170.2            ether   00:50:56:e3:8e:d1   C                     eth0
# 192.168.170.254          ether   00:50:56:e1:ae:a6   C                     eth0
#
# OR:
#
# IP address      HW type                 HW address
# 191.72.1.3      10Mbps Ethernet         00:00:C0:5A:42:C1
# 191.72.1.2      10Mbps Ethernet         00:00:C0:90:B3:42
#
# Example 'arp -a' output:
#
# host.name (123.123.123.1) at 06:36:fd:14:2d:b6 [ether] on eth0
# other-host.name (123.123.123.2) at 06:36:fd:14:2d:b6 [ether] on eth0
# final-host.name (123.123.123.6) at 02:42:ac:11:00:02 [ether] on docker0
#
# Example Windows arp output:
# 
# Interface: 127.0.0.1 --- 0x1
#  Internet Address       Physical Address      Type
#  10.100.100.05          fe-ed-be-ef-10-01     static
#  10.100.100.18          he-ed-de-ed-be-ad     static
#
# Interface: 10.0.0.4 --- 0xd
#  Internet Address      Physical Address      Type
#  10.100.100.1          0a-15-ef-20-5c-a1     dynamic
#  10.100.100.2          10-01-90-7c-bd-01     static
#  10.100.100.3          19-ac-de-ad-be-ef     dynamic
#  10.100.100.8          00-00-00-00-00-00     invalid
#  255.255.255.255       ff-ff-ff-ff-ff-ff     static
#
def parse_arp_data(arp_data_string):
    if arp_data_string is None or arp_data_string.strip() == '':
        return None

    rows = non_empty_rows(arp_data_string)
    
    if rows is None or not isinstance(rows, list) or len(rows) == 0:
        return False

    if is_windows_arp_data(rows):
        arp_records = []
        for table_rows in split_windows_arp_into_tables(rows):
            arp_records += parse_arp_table_data(table_rows)

        return arp_records
    if is_arp_table_data_header(rows[0]):
        return parse_arp_table_data(rows)
    elif is_arp_dash_a_data(rows):
        return parse_arp_dash_a_data(rows)
    else:
        print("Unable to parse ARP data string:\n%s" % arp_data_string)
        raise InternalError("Failed to parse ARP data")

def parse_arp_file(arp_file):
    if not os.path.exists(arp_file):
        # TODO: Change to logging (and all other print statements
        print("File %s does not exist" % arp_file)
        raise InternalError("Internal error occurred while attempting for parse the provided ARP data file")

    with open(arp_file, 'r') as f:
        return parse_arp_data(f.read())
