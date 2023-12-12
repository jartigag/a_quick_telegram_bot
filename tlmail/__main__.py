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
# Description=Telegram bot for (on-call) notification of Cytomic alerts, received by mail
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

__author__  = "@jartigag"
__version__ = '1.4'
__date__    = '2023-05-22'

__changelog__ = """
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

import base64
import configparser
import datetime as dt
import email
import email.header
from email.policy import default as default_policy
import imaplib
import locale
import json
import re
import schedule
from socket import error as SocketError
import threading
from .telegram_utils import setup_telegram_bot, send_telegram_message, format_as_event_message, scape_telegram_chars
import time
import unicodedata

def connect_to_server_and_select_email_inbox(server, email, password):
    print("connecting to mail server:", flush=True)
    mail_object = None

    mail_object = imaplib.IMAP4_SSL(server)

    status_code, status_msg = 'unknown status code', 'unknown status msg'
    print(f"EMAIL={EMAIL}", flush=True)
    status_code, status_msg = mail_object.login(email, password)
    status_code, status_msg = mail_object.select('inbox')

    return mail_object

def archive_emails(uids_list, keep_n_emails_in_inbox, archive_folder_name):
    archived_uids = []

    for uid in uids_list[:-keep_n_emails_in_inbox]:
        apply_lbl_msg = mail_object.uid('COPY', uid, archive_folder_name)
        if apply_lbl_msg[0] == 'OK':
            mov, data = mail_object.uid('STORE', uid , '+FLAGS', '(\Deleted)')
            mail_object.expunge()
            archived_uids.append(uid)
    print(f"archived_uids={archived_uids}", flush=True)

    return list( set(uids_list) - set(archived_uids) )

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
    body = ''

    if email_message.is_multipart():
        parts_list = [x for x in email_message.iter_parts()]
        body = "".join([p.get_content() for p in parts_list])
    else:
        body = email_message.get_body(('plain',)).get_content()
    if remove_html_tags:
        html_tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)') # https://stackoverflow.com/a/19730306
        body        = html_tag_re.sub('', body)

    return body

def extract_fields(content):

    result = {}

    result['host']                = content.split('Equipo:')[-1].split('Grupo:')[0].strip()
    result['group']               = content.split('Grupo:')[-1].split('Nombre:')[0].strip()
    result['name']                = content.split('Nombre:')[-1].split('Ruta:')[0].strip() if 'Nombre:' in content else 'N.A.'
    result['path']                = content.split('Ruta:')[-1].split('Hash:')[0].strip()
    result['hash_md5']            = content.split('Hash:')[-1].split('Equipo origen de la infección:')[0].strip()
    result['url_hybrid_analysis'] = "https://www.hybrid-analysis.com/search?query="+hash_md5
    result['url_virus_total']     = "https://www.virustotal.com/gui/search/"+hash_md5
    result['url_cytomic']         = "https://manage.cytomicmodel.com/#/devices/criteria/none?query="+host

    return result

def query_mails(mail_object, already_assigned_uids):
    if not mail_object:
        return {}

    status1, data_uids = mail_object.uid("search", None, "ALL")
    print(f"{status1}. uids={data_uids}", flush=True)

    data_uids_list = data_uids[0].split()
    if KEEP_N_EMAILS_IN_INBOX!=0 and len(data_uids_list)>KEEP_N_EMAILS_IN_INBOX:
        data_uids_list = archive_emails(data_uids_list, KEEP_N_EMAILS_IN_INBOX, ARCHIVE_FOLDER_NAME)

    mail_uids = [x for x in data_uids_list if int(x) not in already_assigned_uids]
    mail_dicts = []
    locale.setlocale(locale.LC_ALL, 'en_US.utf8')

    for mail_uid in mail_uids:
        status2, data_mail = mail_object.uid("fetch", mail_uid, "(RFC822)")

        email_blob    = data_mail[0][1]
        email_message = email.message_from_bytes(email_blob, policy=default_policy)

        try:
            date = try_parsing_date(email_message['date'])
        except Exception as e:
            print("[!]", e, flush=True)
            date = dt.datetime.utcnow().replace(microsecond=0).isoformat() + '+00:00'
            #example:                                                              '2022-07-06T10:00:00+00:00'

        content = extract_body_from_email_message(email_message, remove_html_tags=True)

        subject = email_message['subject']
        # if subject is composed by encoded-words,
        # ( example: =?UTF-8?B?W0ROUy1GVyAjODkzOTY0XSBBcHJvYmFjacOzbiBhbHRhIFVQVi9FVUggZW4g?= =?UTF-8?B?c2VydmljaW8gRE5TIEZpcmV3YWxs?= ),
        # apply this decodification: https://stackoverflow.com/a/12904228
        if '?utf-8?' in subject.lower() or '?iso-8859-1?' in subject.lower():
            subject = ""
            for subject_bytes,subject_encoding in email.header.decode_header(email_message['subject']):
            #example: email.header.decode_header(mail_message['subject']) = [(b'Se ', None), (b'agreg\xf3 la informaci\xf3n', 'iso-8859-1'), (b' de seguridad de la cuenta Microsoft', None)]
                subject += subject_bytes.decode(subject_encoding) if subject_encoding!=None else subject_bytes.decode('utf-8')

        mail_dicts.append(
            extract_fields(content) | {
                                        'mail_uid': int(mail_uid),
                                        'subject': subject,
                                        'date_received': date,
                                        'assigned': '-'
                                      }
            )

    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')

    return mail_dicts

def update_events():
    already_sent_mails = [ json.loads(line) for line in open(SENT_MAILS_FILENAME).readlines() if line!="\n" ]
    already_assigned_uids = [ int(x['mail_uid']) for x in already_sent_mails if x['assigned']!='-' ]

    if connect_to_email_server:
        print(f"[+] T1: query_mails()", flush=True)
        last_unassigned_mails = query_mails(mail_object, already_assigned_uids)
    else:
        last_unassigned_mails = {}
    print(f"[+] T1: len(last_unassigned_mails):", len(last_unassigned_mails), flush=True)

    for mail in last_unassigned_mails:

        print("new:",          mail['mail_uid'], "-", mail['subject'], flush=True)
        msg = format_as_event_message(mail)
        if msg_meets_filtering_conditions(msg, FILTERING_CONDITIONS):
            print("[+]",mail['mail_uid'],"meets the filtering condition:", flush=True)
            print("   ",FILTERING_CONDITIONS, flush=True)
            if send_to_bot:
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
        else:
            print("[-]",mail['mail_uid'],"doesn't meet the filtering condition:", flush=True)
            print("   ",FILTERING_CONDITIONS, flush=True)

        if ON_CALL:
            if not is_time_between(dt.time(WAVING_HOURS[0],0), dt.time(WAVING_HOURS[1],0)):
                print(f"[+] ON_CALL={ON_CALL}, so",
                    mail['mail_uid'],
                    "will be re-sent until assigned!='-' (that is, until auto-assigned)", flush=True
                    )
            else:
                mail['assigned'] = 'N/A'
        if not ON_CALL:
            mail['assigned'] = 'N/A'

        with open(SENT_MAILS_FILENAME, 'a') as sent_mails_file:
            json.dump(mail, sent_mails_file)
            sent_mails_file.write('\n')

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

    bot_header  = "Tlmail"
    mail_header = "Mail Server"
    tg_header   = "Telegram API Token"

    # feature flags (for debugging):
    connect_to_email_server = True
    send_to_bot = True

    print("initiating:", flush=True)

    FILTERING_CONDITIONS     =     config.get(bot_header, 'FILTERING_CONDITIONS').split(',')
    ON_CALL                  =     config.getboolean(bot_header, 'ON_CALL')
    SCHEDULE_DELAY_SECS      = int(config.get(bot_header, 'SCHEDULE_DELAY_SECS'))
    WAVING_HOURS             = [int(x) for x in config.get(bot_header, 'WAVING_HOURS', fallback="7").split(',')]
    SENT_MAILS_FILENAME      =     config.get(bot_header, 'SENT_MAILS_FILE')
    SYSTEMCTL_SERVICE_NAME   =     config.get(bot_header, 'SYSTEMCTL_SERVICE_NAME')
    open(SENT_MAILS_FILENAME,'a+').close() # touch file (create the file if it doesn't exist, leave it if it exists)

    print(f"FILTERING_CONDITIONS={FILTERING_CONDITIONS}, ON_CALL={ON_CALL}, SYSTEMCTL_SERVICE_NAME={SYSTEMCTL_SERVICE_NAME}", flush=True)
    print(f"SCHEDULE_DELAY_SECS={SCHEDULE_DELAY_SECS}", flush=True)


    if connect_to_email_server:
        SERVER                 = config.get(mail_header, 'SERVER')
        EMAIL                  = config.get(mail_header, 'EMAIL')
        PASSWORD               = config.get(mail_header, 'PASSWORD')
        KEEP_N_EMAILS_IN_INBOX = int(config.get(mail_header, 'KEEP_N_EMAILS_IN_INBOX'))
        ARCHIVE_FOLDER_NAME    = config.get(mail_header, 'ARCHIVE_FOLDER_NAME')

        mail_object = connect_to_server_and_select_email_inbox(SERVER, EMAIL, PASSWORD)

    if send_to_bot:
        TOKEN                  = config.get(tg_header,   'TOKEN')
        CHAT_ID                = config.get(tg_header,   'CHAT_ID')
        telegram_config_params = {'TOKEN': TOKEN, 'FILTERING_CONDITIONS': FILTERING_CONDITIONS, 'ON_CALL': ON_CALL}

        process_params = {'VERSION': __version__, 'DATE': __date__, 'CHANGELOG': __changelog__, 'AUTHOR': __author__, 'EMAIL': EMAIL,
            'SYSTEMCTL_SERVICE_NAME': SYSTEMCTL_SERVICE_NAME, 'SCHEDULE_DELAY_SECS': SCHEDULE_DELAY_SECS, 'SENT_MAILS_FILENAME': SENT_MAILS_FILENAME}
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
