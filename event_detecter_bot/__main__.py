#!/usr/bin/env python3

# INSTALL it as a service in systemctl (logs displayed, rotated and managed in a standard way):
#
# $ cat /etc/systemd/system/event_detecter_bot.service
# [Unit]
# Description=event_detecter_bot
#
# [Service]
# User=$USER
# WorkingDirectory=/home/$USER/event_detecter_bot/
# ExecStart=/usr/bin/pipenv run python3 -m event_detecter_bot

__author__  = "@jartigag"
__version__ = '1.1'
__date__    = '2022-01-19'

# CHANGELOG:
# v1.1:
#       - Add inline keyboard button: 'Refrescar'.
#       - Restructure code flow, so now query and messaging are scheduled in a thread
#         and the bot is always polling from telegram servers in another thread.

import configparser
import datetime as dt
import locale
import json
from .network_utils import extract_resources_from_http_body
import schedule
import threading
from .telegram_utils import setup_telegram_bot, send_telegram_message, format_as_event_message
import time

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
    print(f"[+] T1: get_event(id) for id in event_ids[:{LAST_N_EVENTS}]")

    with open(SENT_EVENTS_FILENAME, 'a') as sent_events_file:

        for event in last_events:

            event_with_extracted_fields = extract_fields(event)

            if event['event_id'] in already_sent_messages:
                print("already sent:", event['event_id'])
            else:
                print("new:",          event['event_id'])
                #print("---")
                print(format_as_event_message(event_with_extracted_fields))
                #print("---")

                json.dump(event, sent_events_file)
                sent_events_file.write('\n')

                if send_to_bot:
                    send_telegram_message(
                        bot, CHAT_ID, format_as_event_message(event_with_extracted_fields), markup_buttons=markup
                    )

    sent_events_file.close()
    print("-")

def run_scheduler():
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
        if is_time_between(dt.time(10,0), dt.time(10,15)): # (!): UTC time
            if not already_waved_today:
                print("\N{waving hand sign}")
                if send_to_bot:
                    send_telegram_message(bot, CHAT_ID, "\N{waving hand sign}")
                already_waved_today = True
        else:
            already_waved_today = False
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":

    # CONFIG:
    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
    config = configparser.ConfigParser()
    config.read('config_event_detecter.ini')

    bot_header  = "@event_detecter_bot"
    crwd_header = "Service API Keys"
    tg_header   = "Telegram API Token"

    # feature flag:
    send_to_bot = True

    print("initiating:")

    LAST_N_EVENTS        = int(config.get(bot_header, 'LAST_N_EVENTS'))
    SCHEDULE_DELAY_SECS      = int(config.get(bot_header, 'SCHEDULE_DELAY_SECS'))
    SENT_EVENTS_FILENAME = config.get(bot_header, 'SENT_EVENTS_FILE')
    open(SENT_EVENTS_FILENAME,'a+').close() # touch file (create the file if it doesn't exist, leave it if it exists)
    print("[+] env vars ready.")

    if send_to_bot:
        bot, CHAT_ID, markup = setup_telegram_bot(config, tg_header, crwd_header)
        print("[+] Telegram Bot is ready.")

    print("starting threads:")
    already_waved_today = False
    t1 = threading.Thread(target=run_scheduler)
    t1.start()
    if send_to_bot:
        t2 = threading.Thread(target=bot.infinity_polling)
        t2.start()
        print("[+] threads T1 (run_scheduler) and T2 (bot.infinity_polling) started.")
    else:
        print("[+] thread T1 (run_scheduler) started.")
