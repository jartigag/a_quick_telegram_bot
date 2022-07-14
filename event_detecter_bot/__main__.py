#!/usr/bin/env python3.9

# INSTALL DEPENDENCIES:
# pip install pipenv # (if pipenv isn't installed yet. it's a tool to manage virtualenvs
#                    #  and to keep track of installed/uninstalled packages in a Pipfile)
# pipenv install

# INSTALL AS A SERVICE with systemctl:
#
# # IMPORTANT! Adapt your environment variables ($USER, WorkingDirectory)
# $ cat /etc/systemd/system/event_detecter_bot.service
# [Unit]
# Description=event_detecter_bot
#
# [Service]
# #User=$USER                                      # by default, root
# WorkingDirectory=/home/$USER/event_detecter_bot/ # example: /root/event_detecter_bot/
# ExecStart=/usr/bin/python -m pipenv run python -m event_detecter_bot
# Restart=always
# RestartSec=10
#
# [Install]
# WantedBy=multi-user.target
#
# $ sudo systemctl daemon-reload

__author__  = "@jartigag"
__version__ = '1.8'
__date__    = '2022-07-13'

__changelog__ = """
v1.8:
      - Optional config: LAST_N_EVENTS=0, WAVING_HOURS
v1.7:
      - New mode: ON_CALL
      - User and admin authentication
      - Telegram commands: /restart, /status, /whois
      - Change UTC by Europe/Madrid timezone
v1.6:
      - Improve telefalcon.network_utils.identify_organization_network():
        filter by known hosts (network_lists/*csv)
      - Filter telegram messages with msg_meets_filtering_conditions(),
        for example: MiRedLocal,\N{large red square}

...

v1.1:
      - Add inline keyboard button: 'Refrescar'.
      - Restructure code flow, so now query and messaging are scheduled in a thread
        and the bot is always polling from telegram servers in another thread.
"""

import configparser
import datetime as dt
import locale
import json
from .network_utils import extract_resources_from_http_body
import schedule
import threading
from .telegram_utils import setup_telegram_bot, send_telegram_message, format_as_event_message, scape_telegram_chars
import time
import unicodedata

def query_events():
    return {
        'body': {
            'text': 'EVENT BODY', 'resources': [
                {"created_timestamp": "2022-01-30T23:00:00.145906462Z", "event_id": "ldt:99999999999999999999999999999999", "external_ip": "130.206.159.235"}
            ]
        }
    }

def extract_fields(event):
    return event

def update_events():
    with open(SENT_EVENTS_FILENAME) as sent_events_file:
        sent_events = [ json.loads(line) for line in sent_events_file.readlines() if line!="\n" ]

    already_sent_messages = [ x['event_id'] for x in sent_events ]

    last_events = extract_resources_from_http_body( query_events() )
    last_events.reverse() # so newer events come first
    print(f"[+] T1: get_event(id) for id in event_ids[:{LAST_N_EVENTS}]", flush=True)

    with open(SENT_EVENTS_FILENAME, 'a') as sent_events_file:

        for event in last_events:

            event_with_extracted_fields = extract_fields(event)

            if event['event_id'] in already_sent_messages:
                print("already sent:", event['event_id'], flush=True)
            else:
                print("new:",          event['event_id'], flush=True)
                json.dump(event, sent_events_file)
                sent_events_file.write('\n')

                msg = format_as_event_message(event_with_extracted_fields)
                if msg_meets_filtering_conditions(msg):
                    print("[+]",event[event_id],"meets the filtering condition:", flush=True)
                    print("   "+"\n   ".join(filtering_condition_code.split('\n')), flush=True)
                    print(msg, flush=True)
                    if send_to_bot:
                        try:
                            send_telegram_message(
                                bot,
                                CHAT_ID,
                                msg,
                                markup_buttons=markup
                            )
                        except Exception:
                            continue
                else:
                    print("[-]",event[event_id],"doesn't meet the filtering condition:", flush=True)
                    print("   "+"\n   ".join(filtering_condition_code.split('\n')), flush=True)

                unassigned_event = False
                if 'status' in event_with_extracted_fields.keys():
                    if event_with_extracted_fields['status']=="new":
                        unassigned_event = True
                if 'state' in event_with_extracted_fields.keys():
                    if event_with_extracted_fields['state']=="open":
                        unassigned_event = True
                if ON_CALL and unassigned_event:
                    print(f"[+] ON_CALL={ON_CALL}, so",event[event_id],"will be re-sent until status!='new' (that is, until auto-assigned)", flush=True)
                if ON_CALL and unassigned_event==False:
                    json.dump(event, sent_events_file)
                    sent_events_file.write('\n')
                if not ON_CALL:
                    json.dump(event, sent_events_file)
                    sent_events_file.write('\n')

def run_scheduler():
    already_waved_today = False
    def is_time_between(begin_time, end_time, check_time=None): # https://stackoverflow.com/a/10048290
        # If check time is not given, default to current UTC time
        check_time = check_time or dt.datetime.utcnow().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time
    schedule.every(SCHEDULE_DELAY_SECS).seconds.do(update_events)
    schedule.run_all() # for the first time, run right now
    while True:
        if any( is_time_between(dt.time(H,0), dt.time(H,2)) for H in WAVING_HOURS ): # (!): UTC time
            if not already_waved_today:
                print("[+] T1: \N{waving hand sign}", flush=True)
                if send_to_bot:
                    send_telegram_message(bot, CHAT_ID, "\N{waving hand sign}", send_without_sound=True)
                already_waved_today = True
        else:
            already_waved_today = False
        schedule.run_pending()
        time.sleep(5)

def msg_meets_filtering_conditions(msg, FILTERING_CONDITIONS):
    for i,x in enumerate(FILTERING_CONDITIONS):
        # convert emojis, if any:
        if "\\N" in x:
                FILTERING_CONDITIONS[i] = unicodedata.lookup( x.replace('\\N','').replace('{','').replace('}','') )
    for or_condition in FILTERING_CONDITIONS: #example: [ ['MiRedLocal', '\N{large red square}'],['MiTag'] ]
        if all(scape_telegram_chars(and_condition) in msg for and_condition in or_condition):
            #example:               ^^^ 'MiRedLocal'                           ^^^ ['MiRedLocal', '\N{large red square}']
                return True
    return False

if __name__ == "__main__":

    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
    config = configparser.ConfigParser()
    config.read('config_event_detecter.ini')

    bot_header  = "@event_detecter_bot"
    api_header  = "Service API Keys"
    tg_header   = "Telegram API Token"

    # feature flags (for debugging):
    send_to_bot = True

    print("initiating:", flush=True)

    FILTERING_CONDITIONS     =     config.get(bot_header, 'FILTERING_CONDITIONS').split(',')
    LAST_N_EVENTS            = int(config.get(bot_header, 'LAST_N_EVENTS'))
    ON_CALL                  =     config.getboolean(bot_header, 'ON_CALL')
    SCHEDULE_DELAY_SECS      = int(config.get(bot_header, 'SCHEDULE_DELAY_SECS'))
    WAVING_HOURS             = [int(x) for x in config.get(bot_header, 'WAVING_HOURS', fallback="7").split(',')]
    SENT_EVENTS_FILENAME     =     config.get(bot_header, 'SENT_EVENTS_FILE')
    SYSTEMCTL_SERVICE_NAME   =     config.get(bot_header, 'SYSTEMCTL_SERVICE_NAME')
    open(SENT_EVENTS_FILENAME,'a+').close() # touch file (create the file if it doesn't exist, leave it if it exists)

    print(f"FILTERING_CONDITIONS={FILTERING_CONDITIONS}, SYSTEMCTL_SERVICE_NAME={SYSTEMCTL_SERVICE_NAME}", flush=True)
    print(f"SCHEDULE_DELAY_SECS={SCHEDULE_DELAY_SECS}, LAST_N_EVENTS={LAST_N_EVENTS}", flush=True)


    if send_to_bot:
        TOKEN                  = config.get(tg_header,   'TOKEN')
        CHAT_ID                = config.get(tg_header,   'CHAT_ID')
        telegram_config_params = {'TOKEN': TOKEN, 'FILTERING_CONDITIONS': FILTERING_CONDITIONS, 'ON_CALL': ON_CALL}

        process_params = {'VERSION': __version__, 'DATE': __date__, 'CHANGELOG': __changelog__, 'AUTHOR': __author__,
                          'SYSTEMCTL_SERVICE_NAME': SYSTEMCTL_SERVICE_NAME, 'SCHEDULE_DELAY_SECS': SCHEDULE_DELAY_SECS, 'LAST_N_EVENTS': LAST_N_EVENTS}

        x = config.get(tg_header, 'TG_USER_IDS', fallback=None)
        y = config.get(tg_header, 'TG_ADMIN_IDS', fallback=None)
        TG_USER_IDS  = [int(n) for n in x.split(',')] if x else ''
        TG_ADMIN_IDS = [int(n) for n in y.split(',')] if y else ''
        telegram_ids = {'TG_USER_IDS': TG_USER_IDS, 'TG_ADMIN_IDS': TG_ADMIN_IDS}
        if TG_USER_IDS or TG_ADMIN_IDS:
            print(f"TG_USER_IDS={TG_USER_IDS}, TG_ADMIN_IDS={TG_ADMIN_IDS}", flush=True)

        bot, markup = setup_telegram_bot(telegram_config_params|process_params|telegram_ids)
        print("[+] Telegram Bot is ready.", flush=True)


    print("starting threads:", flush=True)
    already_waved_today = False
    t1 = threading.Thread(target=run_scheduler)
    t1.start()
    if send_to_bot:
        t2 = threading.Thread(target=bot.infinity_polling)
        t2.start()
        print("[+] threads T1 (run_scheduler) and T2 (bot.infinity_polling) started.", flush=True)
    else:
        print("[+] thread T1 (run_scheduler) started.", flush=True)
