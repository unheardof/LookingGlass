#from looking_glass import parse_arp_data
from looking_glass.lib.arp import parse_arp_data

def validate_arp_record(record, hostname, ip_addr, hw_type, hw_addr, flags, mask, iface):
    assert(record.hostname == hostname)
    assert(record.address == ip_addr)
    assert(record.hw_type == hw_type)
    assert(record.hw_address == hw_addr)
    assert(record.flags == flags)
    assert(record.mask == mask)
    assert(record.interface == iface)

def test_parse_arp_table_data():
    arp_records = parse_arp_data("""Address                  HWtype  HWaddress           Flags Mask            Iface
192.168.170.2            ether   00:50:56:e3:8e:d1   C                     eth0
192.168.170.254          ether   00:50:56:e1:ae:a6   C                     eth0""")

    validate_arp_record(arp_records[0], '', '192.168.170.2', 'ether', '00:50:56:e3:8e:d1', 'C', '', 'eth0')
    validate_arp_record(arp_records[1], '', '192.168.170.254', 'ether', '00:50:56:e1:ae:a6', 'C', '', 'eth0')

def test_parse_arp_dash_a_data():
    arp_records = parse_arp_data("""host.name (123.123.123.1) at 06:36:fd:14:2d:b6 [ether] on eth0
other-host.name (123.123.123.2) at 06:36:fd:14:2d:b6 [ether] on eth0
final-host.name (123.123.123.6) at 02:42:ac:11:00:02 [ether] on docker0""")

    validate_arp_record(arp_records[0], 'host.name', '123.123.123.1', 'ether', '06:36:fd:14:2d:b6', '', '', 'eth0')
    validate_arp_record(arp_records[1], 'other-host.name', '123.123.123.2', 'ether', '06:36:fd:14:2d:b6', '', '', 'eth0')
    validate_arp_record(arp_records[2], 'final-host.name', '123.123.123.6', 'ether', '02:42:ac:11:00:02', '', '', 'docker0')

# TODO: Test edge/failure cases
