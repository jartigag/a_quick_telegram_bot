import requests

def extract_resources_from_http_body(http_response):
    return http_response['body']['resources']

def query_ipgeolocation(external_ip):
    ipgeoloc_url = f"https://ipgeolocation.io/ip-location/"+external_ip
    ipgeoloc_html_lines = requests.get(ipgeoloc_url).text.split('\n')
    ipgeoloc_data = ["",""]
    for i,line in enumerate(ipgeoloc_html_lines):
            if '<td>City</td>' in line:
                ipgeoloc_data[0] = ipgeoloc_html_lines[i+1].replace('</td>','').replace('<td>','')
            if '<td>ISP</td>' in line:
                ipgeoloc_data[1] = ipgeoloc_html_lines[i+1].replace('</td>','').replace('<td>','')
    return ipgeoloc_data
