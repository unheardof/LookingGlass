import subprocess
import threading

# Reference: https://stackoverflow.com/questions/7168508/background-function-in-python
class PcapParser(threading.Thread):

    def __init__(self, pcap_file):
        threading.Thread.__init__(self)
        self.runnable = parse_pcap(pcap_file)
        self.daemon = True

    def run(self):
        self.runnable()

def parse_pcap(pcap_file):
    results = subprocess.check_output(["tcpdump", "-nt", "-r", pcap_file])

    connections = {}
    
    # Line format (note: data past the IP addresses can vary based on the contents of the packet):
    #
    # IP 130.193.12.185.44755 > 170.129.1.50.68: Flags [S], seq 1656191770, win 1024, options [mss 1460], length 0
    for r in results.split("\n"):
        words = r.split(' ')
        src_ip = words[1]
        dst_ip = words[3]

        if connections[src_ip] is None:
            connections[src_ip] = []

        if not dst_ip in connections[src_ip]:
            connections[src_ip].append(dst_ip)

    return connections
