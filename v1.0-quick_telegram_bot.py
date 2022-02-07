#!/usr/bin/env python3

#install in crontab each 2 minutes:
# */2 *    * * *   cd $QUICK_TELEGRAM_BOT_PY_DIR && /usr/bin/python quick_telegram_bot.py 1>/dev/null

# INSTALL it as a service in systemctl (logs displayed, rotated and managed in a standard way):
#
# $ cat /etc/systemd/system/quick_telegram_bot.service
# [Unit]
# Description=QuickTelegramBot
# [Service]
# User=$USER
# Type=oneshot
# WorkingDirectory=/home/$USER/quick_telegram_bot/
# ExecStart=/usr/bin/pipenv run python3 /home/$USER/quick_telegram_bot/quick_telegram_bot.py
#
# $ cat /etc/systemd/system/quick_telegram_bot.timer
# [Unit]
# Description=QuickTelegramBot
# [Timer]
# OnUnitActiveSec=1m
# OnBootSec=10s
# AccuracySec=1s
# [Install]
# WantedBy=timers.target

__author__  = "@jartigag"
__version__ = '1.0'
__date__    = '2022-01-17'


import configparser
from datetime import datetime, timedelta, time
import locale
import json
import requests
import telebot


# CONFIG:
config = configparser.ConfigParser()
config.read('config.ini')

bot_header  = "@replace_by_the_name_of_your_bot"
tg_header   = "Telegram API Token"

LAST_N_OBJECTS = int(config.get(bot_header, 'LAST_N_OBJECTS'))
# feature flag:
send_to_bot = True


locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
def format_time(input_datetime_str, include_date=False):
    input_datetime = datetime.fromisoformat(
        input_datetime_str.split('.')[0].replace('Z','')
    )
    if include_date:
        return datetime.strftime(input_datetime,'%d%b %H:%M:%S')
    else:
        return datetime.strftime(input_datetime,'%H:%M')

def format_duration(input_duration):
    return str(timedelta(seconds=int(input_duration))).replace(':',"h",1).replace(':',"'",1)+'"'

def scape_telegram_chars(str_input):
    return str_input.replace('*','\*').replace('-','\-').replace('_','\_').replace('.','\.').replace('(','\(').replace(')','\)')

def get_geoip_extract_data_from_http_body(external_ip):
    ipgeoloc_url = f"https://ipgeolocation.io/ip-location/"+external_ip
    ipgeoloc_html_lines = requests.get(ipgeoloc_url).text.split('\n')
    ipgeoloc_data = ["",""]
    for i,line in enumerate(ipgeoloc_html_lines):
            if '<td>City</td>' in line:
                ipgeoloc_data[0] = scape_telegram_chars( ipgeoloc_html_lines[i+1].replace('</td>','').replace('<td>','') )
            if '<td>ISP</td>' in line:
                ipgeoloc_data[1] = scape_telegram_chars( ipgeoloc_html_lines[i+1].replace('</td>','').replace('<td>','') )
    return ipgeoloc_data

def format_as_message(data_dict):
    # shorter keys:
    d = { k.split(':')[-1]: v for k,v in data_dict.items() }
    def print_with_fixed_length_key(extractedfields_dict, dict_keylist):
        return "\n".join(
            scape_telegram_chars("`{:<17}".format(k))+"`: "\
            #          ^^ string minimal length
            + scape_telegram_chars(str(extractedfields_dict[k])) for k in dict_keylist
        )+"\n"
    #example: "[[+]](https://ipgeolocation.io/ip-location/130.206.159.235)` external_ip   :` 130.206.159.235 (Pamplona, Entidad Publica Empresarial Red.es)
    geodata = get_geoip_extract_data_from_http_body('130.206.159.235')
    msg = f"{ format_time(time.now().isoformat()) } "                                                  + \
          f"[\( \+ \)](https://ipgeolocation.io/ip-location/{ '130.206.159.235' })` external\_ip  `: " + \
          f"`{ scape_telegram_chars('130.206.159.235') }` \({ geodata[0] }, { geodata[1] }\)\n"
    msg += print_with_fixed_length_key(
        d, d.keys() #TODO: select keys here as a list (example: ['name', 'phone'])
    )
    msg += "\n"
    msg += "       \N{globe with meridians}"+f"[View detail]({'#'})"+" \N{globe with meridians}" #TODO: replace '#' by d['object_url']
    return msg

def is_time_between(begin_time, end_time, check_time=None): # https://stackoverflow.com/a/10048290
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

if __name__ == '__main__':

    if send_to_bot:
        bot = telebot.TeleBot(config.get(tg_header, 'TOKEN'))
        chat_id = config.get(tg_header, 'CHAT_ID')

    # == FEATURE EXAMPLE ==
    # this bot stores JSON objects in a "Newline-delimited JSON" file
    # and send a message if there's a new JSON object:
    open('log_objects.json','a+').close() # touch
    with open('log_objects.json') as event_log_file:
        sent_messages_log = [ json.loads(line) for line in event_log_file.readlines() ]
    event_log_file     = open('log_objects.json','a')

    already_sent_messages = [ x['object_id'] for x in sent_messages_log ]

    #TODO: extract objects here:
    #      ( demo idea: maybe extract ssh login attempts? )
    last_objects = []

    if is_time_between(time(7,0), time(7,2)): # (!): UTC time
        print("\N{waving hand sign}")
        if send_to_bot:
            bot.send_message(chat_id, "\N{waving hand sign}")

    for object_with_extracted_fields in last_objects:

        if object_with_extracted_fields['object_id'] in already_sent_messages:
            print(datetime.now(), "- already sent:",object_with_extracted_fields['object_id'])
        else:
            print(datetime.now(), "- new:",         object_with_extracted_fields['object_id'])
            print("---")
            print(format_as_message(object_with_extracted_fields))
            print("---")

            json.dump(object_with_extracted_fields, event_log_file)
            event_log_file.write('\n')

            if send_to_bot:
                bot.send_message(
                    chat_id,
                    format_as_message(object_with_extracted_fields),
                    parse_mode="MarkdownV2",
                    disable_web_page_preview=True
                )
