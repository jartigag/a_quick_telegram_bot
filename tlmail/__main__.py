#!/usr/bin/env python3.9

# INSTALL DEPENDENCIES:
# pip install pipenv # (if pipenv isn't installed yet. it's a tool to manage virtualenvs
#                    #  and to keep track of installed/uninstalled packages in a Pipfile)
# pipenv install

# INSTALL AS A SERVICE with systemctl:
#
# # IMPORTANT! Adapt your environment variables ($USER, WorkingDirectory)
# $ cat /etc/systemd/system/tlmail.service
# [Unit]
# Description=Telegram bot for on-call notification of open offenses in QRadar, received via the QRadar API
#
# [Service]
# #User=$USER                            # by default, root
# WorkingDirectory=/home/$USER/tlmail/   # example: /root/tlmail/
# ExecStart=/usr/bin/python -m pipenv run python -m tlmail
# Restart=always
# RuntimeMaxSec=1h                       # so the bot keeps listening for 1h, but it reconnects
#                                        # to smtp server just in case something crashes
#
# [Install]
# WantedBy=multi-user.target
#
# $ sudo systemctl daemon-reload

__author__  = ["@jartigag", "@cataand"]
__version__ = '1.6'
__date__    = '2024-01-17'

__changelog__ = """
v1.6
      - Add support for QRadar API as a source.
v1.5:
      - better html handling
v1.4:
      - refactor (extract_body_from_email_message, try_parsing_date, extract_fields)
v1.3:
      - handling exceptions: just restart the service every 1h
v1.2:
      - if len(uids)>KEEP_N_EMAILS_IN_INBOX: archive_emails()
v1.1:
      - Special requirement: ON_CALL only when out of WAVING_HOURS.
v1.0:
      - Tlmail functional, auto-assign button works.
      - It supports encoded-words subjects (RFC 2047).
v0.9:
      - Forked from event_detecter_bot and adapted to get events from an email inbox.
"""

import configparser
import datetime as dt
import locale
import re
import schedule
import threading
from .telegram_utils import setup_telegram_bot, send_telegram_message, format_as_event_message, scape_telegram_chars, get_cache, set_cache
from .qradar import QRadarAPI
import time
import unicodedata
import html
import telebot

def try_parsing_date(text):
    for fmt in (
            '%a, %d %b %Y %H:%M:%S %z', #'Wed, 06 Jul 2022 12:00:00 +0200' -> '2022-07-06T12:00:00+02:00'
            '%d %b %Y %H:%M:%S %z'      #'20 May 2023 07:40:59 +0000'      -> '2023-05-20T09:40:59+02:00'
        ):
        try:
            return dt.datetime.strptime(text, fmt).isoformat()
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def extract_body_from_email_message(email_message, remove_html_tags=False):
    body = ""
    if email_message.is_multipart():
        parts_list = [x for x in email_message.iter_parts()]
        body = "".join([p.get_content() for p in parts_list])
    else:
        body = email_message.get_body().get_content()

    if email_message.get_content_type() == "text/html":
        remove_html_tags = True

    if remove_html_tags:
        html_tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)') # https://stackoverflow.com/a/19730306
        body        = html_tag_re.sub('', body)
        body = html.unescape(body)

    return body.strip()

def extract_fields(content):
    result = {}

    result['url']       = content.split('URL: ')[-1].lstrip('<').rstrip(' >')
    result['ticket_id'] = result['url'].split('?id=')[-1].split()[0]

    return result

def update_events():
    cache = get_cache()

    # Get new offenses
    new_offenses = list(reversed(qradar.get_offenses(f"id>{cache['last_offense_id']} and start_time>{start_epoch}")))
    for offense in new_offenses:
        offense["assigned"] = "-"

    # Get previous offenses
    previous_offenses = cache["previous_offenses"]
    previous_unassigned_offenses = filter(lambda o: o["assigned"] == "-", previous_offenses)

    offenses = list(previous_unassigned_offenses) + list(new_offenses)
    for offense in offenses:
        print("", offense['id'], "-", offense['description'], flush=True)
        msg = format_as_event_message(offense)
        if msg_meets_filtering_conditions(msg, FILTERING_CONDITIONS):
            print("[+]",offense['id'],"meets the filtering condition:", flush=True)
            print("   ",FILTERING_CONDITIONS, flush=True)

            if send_to_bot:
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(
                    telebot.types.InlineKeyboardButton(text='Auto-asignar', callback_data=f'{{"cb":"cb_auto_assign","oid":{offense["id"]}}}'),
                )
                try:
                    send_telegram_message(
                        bot,
                        CHAT_ID,
                        msg,
                        markup_buttons=markup
                    )
                except Exception as e:
                    print("[!]", e, flush=True)
                    continue

        if ON_CALL:
            if not is_time_between(dt.time(WAVING_HOURS[0],0), dt.time(WAVING_HOURS[1],0)):
                print(f"[+] ON_CALL={ON_CALL}, so",
                    offense['id'],
                    "will be re-sent until assigned!='-' (that is, until auto-assigned)", flush=True
                    )
            else:
                offense['assigned'] = 'N/A'
        if not ON_CALL:
            offense['assigned'] = 'N/A'

    set_cache({
        "last_offense_id": new_offenses[-1]["id"] if new_offenses else cache['last_offense_id'],
        "previous_offenses": previous_offenses + new_offenses
    })

def is_time_between(begin_time, end_time, check_time=None): # https://stackoverflow.com/a/10048290
    # If check time is not given, default to current UTC time
    check_time = check_time or dt.datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

def run_scheduler():
    already_waved_today = False
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
    config.read('config_tlmail.ini')

    bot_header  = "Telemail"
    qradar_header = "QRadar"
    tg_header   = "Telegram API Token"

    start_epoch = round(time.time() * 1000)

    # feature flags (for debugging):
    connect_to_qradar = True
    send_to_bot = True

    print("initiating:", flush=True)

    FILTERING_CONDITIONS     =     config.get(bot_header, 'FILTERING_CONDITIONS').split(',')
    ON_CALL                  =     config.getboolean(bot_header, 'ON_CALL')
    SCHEDULE_DELAY_SECS      = int(config.get(bot_header, 'SCHEDULE_DELAY_SECS'))
    WAVING_HOURS             = [int(x) for x in config.get(bot_header, 'WAVING_HOURS', fallback="7").split(',')]
    #SENT_MAILS_FILENAME      =     config.get(bot_header, 'SENT_MAILS_FILE')
    SYSTEMCTL_SERVICE_NAME   =     config.get(bot_header, 'SYSTEMCTL_SERVICE_NAME')
    #open(SENT_MAILS_FILENAME,'a+').close() # touch file (create the file if it doesn't exist, leave it if it exists)

    print(f"FILTERING_CONDITIONS={FILTERING_CONDITIONS}, ON_CALL={ON_CALL}, SYSTEMCTL_SERVICE_NAME={SYSTEMCTL_SERVICE_NAME}", flush=True)
    print(f"SCHEDULE_DELAY_SECS={SCHEDULE_DELAY_SECS}", flush=True)

    if connect_to_qradar:
        QRADAR_URL = config.get(qradar_header, 'BASE_URL')
        QRADAR_TOKEN = config.get(qradar_header, 'TOKEN')
        QRADAR_VERSION = config.get(qradar_header, 'VERSION')

        qradar = QRadarAPI(QRADAR_URL, QRADAR_TOKEN, QRADAR_VERSION)

    if send_to_bot:
        TOKEN                  = config.get(tg_header,   'TOKEN')
        CHAT_ID                = config.get(tg_header,   'CHAT_ID')
        telegram_config_params = {'TOKEN': TOKEN, 'FILTERING_CONDITIONS': FILTERING_CONDITIONS, 'ON_CALL': ON_CALL}

        process_params = {'VERSION': __version__, 'DATE': __date__, 'CHANGELOG': __changelog__, 'AUTHOR': __author__,
            'SYSTEMCTL_SERVICE_NAME': SYSTEMCTL_SERVICE_NAME, 'SCHEDULE_DELAY_SECS': SCHEDULE_DELAY_SECS}#, 'SENT_MAILS_FILENAME': SENT_MAILS_FILENAME}
        x = config.get(tg_header, 'TG_USER_IDS', fallback=None)
        y = config.get(tg_header, 'TG_ADMIN_IDS', fallback=None)
        TG_USER_IDS  = [int(n) for n in x.split(',')] if x else ''
        TG_ADMIN_IDS = [int(n) for n in y.split(',')] if y else ''
        telegram_ids = {'TG_USER_IDS': TG_USER_IDS, 'TG_ADMIN_IDS': TG_ADMIN_IDS}
        if TG_USER_IDS or TG_ADMIN_IDS:
            print(f"TG_USER_IDS={TG_USER_IDS}, TG_ADMIN_IDS={TG_ADMIN_IDS}", flush=True)

        bot = setup_telegram_bot(telegram_config_params|process_params|telegram_ids)
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
