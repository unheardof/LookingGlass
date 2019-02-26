import os

ARP_FIELD_NAMES = ['Address', 'HWtype', 'HWaddress', 'Flags', 'Mask', 'Iface']

class ArpData:

    def __init__(self, address, hw_type, hw_address, flags, mask, interface):
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
        
        
# Example arp output:
#
# Address                  HWtype  HWaddress           Flags Mask            Iface
# 192.168.170.2            ether   00:50:56:e3:8e:d1   C                     eth0
# 192.168.170.254          ether   00:50:56:e1:ae:a6   C                     eth0
def parse_arp_data(arp_data_string):
    arp_records = []

    is_header = True
    column_indexes = {}
    for line in arp_data_string.split("\n"):
        if len(line.strip()) == 0:
            next
        elif is_header:
            previous_field = None
            for field in ARP_FIELD_NAMES:
                index = line.index(field)
                column_indexes[field] = { 'start': index, 'end': len(line) }
                    
                if not previous_field is None:
                    column_indexes[previous_field]['end'] = index

                previous_field = field
                
            is_header = False
        else:
            record_data = {}

            for field in ARP_FIELD_NAMES:
                record_data[field] = line[column_indexes[field]['start']:column_indexes[field]['end']].strip()

            arp_records.append(ArpData.from_dict(record_data))

    return arp_records

def parse_arp_file(arp_file):
    if not os.path.exists(arp_file):
        raise Exception("File %s does not exist" % arp_file)

    with open(arp_file, 'r') as f:
        return parse_arp_data(f.read())
