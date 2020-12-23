#from looking_glass import parse_arp_data
#from looking_glass.lib.arp import is_arp_table_data_header, parse_arp_data, ArpTableParser
from looking_glass.lib.arp import *

###
### Helper functions
###

def validate_arp_record(record, hostname, ip_addr, hw_type, hw_addr, flags, mask, iface, record_type):
    assert(record.hostname == hostname)
    assert(record.ip_address == ip_addr)
    assert(record.hw_type == hw_type)
    assert(record.hw_address == hw_addr)
    assert(record.flags == flags)
    assert(record.mask == mask)
    assert(record.interface == iface)
    assert(record.record_type == record_type)

###
### Test functions
###

# TODO: add failure test cases and test with different offsets, etc.
def test_col_headers_with_offsets():
    headers_with_offsets = ArpTableParser.col_headers_with_offsets("Address                  HWtype  HWaddress           Flags Mask            Iface")
    
    assert(headers_with_offsets['Address']['start'] == 0)
    assert(headers_with_offsets['Address']['end'] == 25)
    assert(headers_with_offsets['HWtype']['start'] == 25)
    assert(headers_with_offsets['HWtype']['end'] == 33)
    assert(headers_with_offsets['HWaddress']['start'] == 33)
    assert(headers_with_offsets['HWaddress']['end'] == 53)
    assert(headers_with_offsets['Flags']['start'] == 53)
    assert(headers_with_offsets['Flags']['end'] == 59)
    assert(headers_with_offsets['Mask']['start'] == 59)
    assert(headers_with_offsets['Mask']['end'] == 75)
    assert(headers_with_offsets['Iface']['start'] == 75)
    assert(headers_with_offsets['Iface']['end'] is None)
    assert(HOSTNAME_FIELD not in headers_with_offsets)

def test_col_headers_with_offsets_2():
    headers_with_offsets = ArpTableParser.col_headers_with_offsets("IP address      HW type                 HW address")

    assert(headers_with_offsets['IP address']['start'] == 0)
    assert(headers_with_offsets['IP address']['end'] == 16)
    assert(headers_with_offsets['HW type']['start'] == 16)
    assert(headers_with_offsets['HW type']['end'] == 40)
    assert(headers_with_offsets['HW address']['start'] == 40)
    assert(headers_with_offsets['HW address']['end'] == None)

    assert(HOSTNAME_FIELD not in headers_with_offsets)
    assert(ARP_FLAGS_FIELD not in headers_with_offsets)
    assert(SUBNET_MASK_FIELD not in headers_with_offsets)
    assert(INTERFACE_NAME_FIELD not in headers_with_offsets)

def test_col_headers_with_offsets_3():
    headers_with_offsets = ArpTableParser.col_headers_with_offsets("Address HWtype HWaddress Flags Mask Iface")
    
    assert(headers_with_offsets['IP address']['start'] == 0)
    assert(headers_with_offsets['IP address']['end'] == 8)
    assert(headers_with_offsets['HW type']['start'] == 8)
    assert(headers_with_offsets['HW type']['end'] == 15)
    assert(headers_with_offsets['HW address']['start'] == 15)
    assert(headers_with_offsets['HW address']['end'] == 25)
    assert(headers_with_offsets['Flags']['start'] == 25)
    assert(headers_with_offsets['Flags']['end'] == 31)
    assert(headers_with_offsets['Mask']['start'] == 31)
    assert(headers_with_offsets['Mask']['end'] == 36)
    assert(headers_with_offsets['Iface']['start'] == 36)
    assert(headers_with_offsets['Iface']['end'] is None)
    assert(HOSTNAME_FIELD not in headers_with_offsets)

def test_col_headers_with_offsets_failures():
    ArpTableParser.col_headers_with_offsets("Address HWtype HWaddress Flags Mask Iface")

# TODO: Add test for is_arp_dash_a_data too
def test_is_arp_table_data_header():
    assert(is_arp_table_data_header("Address                  HWtype  HWaddress           Flags Mask            Iface"))
    assert(is_arp_table_data_header("IP address      HW type                 HW address"))
    assert(not is_arp_table_data_header("host.name (123.123.123.1) at 06:36:fd:14:2d:b6 [ether] on eth0"))
    # TODO: Add negative cases
    
def test_parse_arp_table_data():
    arp_records = parse_arp_data("""Address                  HWtype  HWaddress           Flags Mask            Iface
192.168.170.2            ether   00:50:56:e3:8e:d1   C                     eth0
192.168.170.254          ether   00:50:56:e1:ae:a6   C                     eth0""")

    validate_arp_record(arp_records[0], None, '192.168.170.2', 'ether', '00:50:56:e3:8e:d1', 'C', None, 'eth0', None)
    validate_arp_record(arp_records[1], None, '192.168.170.254', 'ether', '00:50:56:e1:ae:a6', 'C', None, 'eth0', None)

def test_parse_arp_table_data_2():
    arp_records = parse_arp_data("""IP address      HW type                 HW address
191.72.1.3      10Mbps Ethernet         00:00:C0:5A:42:C1
191.72.1.2      10Mbps Ethernet         00:00:C0:90:B3:42""")

    validate_arp_record(arp_records[0], None, '191.72.1.3', '10Mbps Ethernet', '00:00:C0:5A:42:C1', None, None, None, None)
    validate_arp_record(arp_records[1], None, '191.72.1.2', '10Mbps Ethernet', '00:00:C0:90:B3:42', None, None, None, None)

def test_parse_arp_table_data_windows():
    arp_records = parse_arp_data("""
Interface: 127.0.0.1 --- 0x1
  Internet Address       Physical Address      Type
  10.100.100.05          fe-ed-be-ef-10-01     static
  10.100.100.18          he-ed-de-ed-be-ad     static

Interface: 10.0.0.4 --- 0xd
  Internet Address      Physical Address      Type
  10.100.100.1          0a-15-ef-20-5c-a1     dynamic
  10.100.100.2          10-01-90-7c-bd-01     static
  10.100.100.3          19-ac-de-ad-be-ef     dynamic
  10.100.100.8          00-00-00-00-00-00     invalid
  255.255.255.255       ff-ff-ff-ff-ff-ff     static
""")
    
    validate_arp_record(arp_records[0], None, '10.100.100.05', None, 'fe-ed-be-ef-10-01', None, None, None, 'static')
    validate_arp_record(arp_records[1], None, '10.100.100.18', None, 'he-ed-de-ed-be-ad', None, None, None, 'static')
    validate_arp_record(arp_records[2], None, '10.100.100.1', None, '0a-15-ef-20-5c-a1', None, None, None, 'dynamic')
    validate_arp_record(arp_records[3], None, '10.100.100.2', None, '10-01-90-7c-bd-01', None, None, None, 'static')
    validate_arp_record(arp_records[4], None, '10.100.100.3', None, '19-ac-de-ad-be-ef', None, None, None, 'dynamic')
    validate_arp_record(arp_records[5], None, '10.100.100.8', None, '00-00-00-00-00-00', None, None, None, 'invalid')
    validate_arp_record(arp_records[6], None, '255.255.255.255', None, 'ff-ff-ff-ff-ff-ff', None, None, None, 'static')
    
def test_parse_arp_dash_a_data():
    arp_records = parse_arp_data("""host.name (123.123.123.1) at 06:36:fd:14:2d:b6 [ether] on eth0
other-host.name (123.123.123.2) at 06:36:fd:14:2d:b6 [ether] on eth0
final-host.name (123.123.123.6) at 02:42:ac:11:00:02 [ether] on docker0""")

    validate_arp_record(arp_records[0], 'host.name', '123.123.123.1', 'ether', '06:36:fd:14:2d:b6', None, None, 'eth0', None)
    validate_arp_record(arp_records[1], 'other-host.name', '123.123.123.2', 'ether', '06:36:fd:14:2d:b6', None, None, 'eth0', None)
    validate_arp_record(arp_records[2], 'final-host.name', '123.123.123.6', 'ether', '02:42:ac:11:00:02', None, None, 'docker0', None)

# TODO: Test edge/failure cases
