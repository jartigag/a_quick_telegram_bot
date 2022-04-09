#usage:
#$ python event_detecter_bot/network_utils.py
#$ python event_detecter_bot/network_utils.py 192.168.1.10

import requests
import ipaddress
import csv
from pathlib import Path

def extract_resources_from_http_body(http_response):
    return http_response['body']['resources']

def query_ipgeolocation(external_ip):
    ipgeoloc_url = f"https://ipgeolocation.io/ip-location/"+external_ip
    ipgeoloc_data = requests.get(ipgeoloc_url, headers={'Referer': 'https://api.ipgeolocation.io/'}).json()
    return ipgeoloc_data['city'],ipgeoloc_data['isp']

network_lists = []
csv_files = [f for f in Path('event_detecter_bot/network_lists').iterdir() if f.suffix=='.csv']
for csv_file in csv_files:
    with open(csv_file) as f:
        reader = csv.reader(f, delimiter=",")
        header_columns = next(reader)                                        # discard first line
        network_lists.append( [ [csv_file.name[:-4]] + x for x in reader ] ) # append the rest

networks = {
    "MiRedLocal": {
        'startip': ipaddress.IPv4Address('192.168.1.0'),
        'endip':   ipaddress.IPv4Address('192.168.1.31'),
        'comment': "192.168.1.0/27 (mask 255.255.255.224)",
    },
}

def calculate_cidr_address_ranges(start_ip, end_ip):
    return [ip_addr for ip_addr in ipaddress.summarize_address_range(start_ip, end_ip)]

# CIDR format:
for netw_name, netw in networks.items():
    networks[netw_name]['cidr_address_ranges'] = calculate_cidr_address_ranges(netw['startip'], netw['endip'])

def identify_organization_network(localip_str):

    local_ip = ipaddress.IPv4Address(localip_str)

    def is_in_address_ranges(input_ip, address_ranges):
        return any(input_ip in address_range for address_range in address_ranges)

    for netw_name, netw in networks.items():
        if is_in_address_ranges(local_ip, netw['cidr_address_ranges']):
                return netw_name
    for network_list in network_lists: # iterate through MISSM network inventaries
        for line in network_list:
            if localip_str in line:
                return line[0] #example: "MISSM - María de Guzmán, 25"

    return False


if __name__ == "__main__":

    import sys

    if len(sys.argv)>1:
        try:
            inputip_str = sys.argv[1]
            identified_network = identify_organization_network(inputip_str)
            if identified_network:
                print("[+]",inputip_str,"is in",identified_network)
                sys.exit(0)
            print("[-]",inputip_str,"is not in any known subnet")
            sys.exit(-1)
        except ipaddress.AddressValueError:
            print("[!] Invalid IP Address")
    else:
        for netw_name, netw in networks.items():
            print(netw_name.ljust(50),", ".join([str(x) for x in netw['cidr_address_ranges']]))
