from datetime import datetime, timedelta
import json
from .network_utils import identify_owner
from pytz import timezone
import re
import subprocess
import telebot
from telebot.apihelper import ApiTelegramException

def setup_telegram_bot(config_params):
    bot = telebot.TeleBot(config_params['TOKEN'])

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(text='Auto-asignar', callback_data="cb_auto_assign"),
    )

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):

        if call.data == "cb_auto_assign":

            mail_uid  = int(call.message.json['text'].split('mail_uid     :')[-1].split('\N{globe with meridians}')[0].strip())
            alert_id  = mail_uid

            usr = call.from_user
            name = f"{usr.first_name} {usr.last_name} (tg_user_id={usr.id})"

            try:
                already_sent_mails = [ json.loads(line) for line in open(config_params['SENT_MAILS_FILENAME']).readlines() if line!="\n" ]

                with open(config_params['SENT_MAILS_FILENAME'], 'w') as sent_mails_file:
                    for mail in already_sent_mails:
                        if mail['mail_uid']==mail_uid:
                            mail['assigned'] = name
                        json.dump(mail, sent_mails_file)
                        sent_mails_file.write('\n')

                bot.reply_to(
                    call.message,
                    scape_telegram_chars(
                        f"Alerta {alert_id} auto-asignada a {name}\n" \
                        + format_with_fixed_length_key({'mail_uid': mail_uid}, ['mail_uid'], scape_chars=False)
                    ),
                    parse_mode="MarkdownV2",
                    disable_notification=True
                )
                print(f"Alert {alert_id} auto-assigned to {name}", flush=True)
            except Exception as e:
                print("[!]",e, flush=True)
                bot.reply_to(
                    call.message,
                    scape_telegram_chars(f"[!] Error asignando la alerta {alert_id} a {name}\n"),
                    parse_mode="MarkdownV2",
                    disable_notification=True
                )
                print(f"[!] Error assigning alert {alert_id} to {name}", flush=True)

    def authentication_is_ok(message, command, admin=False):
        tg_user_id = message.from_user.id
        print("T2: user",tg_user_id,"(",message.from_user.first_name,message.from_user.last_name,")","requested command:",command, flush=True)
        if admin:
            if config_params['TG_ADMIN_IDS']:
                if tg_user_id in config_params['TG_ADMIN_IDS']:
                    print("[+] T2: user",tg_user_id,"in TG_ADMIN_IDS", flush=True)
                    return True
            else:
                print("[+] authentication by telegram user is disabled", flush=True)
                return True
            print("[-] T2: user",tg_user_id,"not in TG_ADMIN_IDS", flush=True)
            return False
        if config_params['TG_USER_IDS']:
            if tg_user_id in config_params['TG_USER_IDS']:
                print("[+] T2: user",tg_user_id,"in TG_USER_IDS", flush=True)
                return True
        else:
            print("[+] authentication by telegram user is disabled", flush=True)
            return True
        print("[-] T2: user",tg_user_id,"not in TG_USER_IDS", flush=True)
        return False

    @bot.message_handler(commands=['start','help'])
    def send_start(message):
        if authentication_is_ok(message, "/start = /help"):
            bot.reply_to(
                message,
                f"TLMail v{scape_telegram_chars(config_params['VERSION'])}: "+\
                f"Bot de notificaciones por Telegram"+"\n\n"                                             +\
                    "Comandos de administrador:\n"                                                       +\
                    "\- /status\n   devuelve al admin info de estado del servicio\n"                     +\
                    "\- /restart\n   permite al admin reiniciar el servicio\n\n"                         +\
                    "Escribe /about para ver los datos de esta versión y el registro de cambios",
                parse_mode="MarkdownV2",
                disable_notification=True
            )
        else:
            print("[-] T2: user",tg_user_id,"not in TG_USER_IDS", flush=True)

    @bot.message_handler(commands=['status'])
    def send_status(message):
        if authentication_is_ok(message, "/status", admin=True):
            c = config_params
            systemctl_output = subprocess.check_output("systemctl status "+c['SYSTEMCTL_SERVICE_NAME'], shell=True, text=True)
            if "active (running)" in systemctl_output:
                systemctl_output = "\N{large green circle}"+systemctl_output[1:]
            bot.reply_to(
                message,
                scape_telegram_chars(
                    f"FILTERING_CONDITIONS={c['FILTERING_CONDITIONS']},SYSTEMCTL_SERVICE_NAME={c['SYSTEMCTL_SERVICE_NAME']}" +\
                    f",SCHEDULE_DELAY_SECS={c['SCHEDULE_DELAY_SECS']}, ON_CALL={c['ON_CALL']}" +\
                    "\n\n"+systemctl_output
                ),
                parse_mode="MarkdownV2",
                disable_notification=True
            )

    @bot.message_handler(commands=['about'])
    def send_about(message):
        if authentication_is_ok(message, "/about"):
            bot.reply_to(
                message,
                scape_telegram_chars(
                    f"Telefalcon v{config_params['VERSION']} ({config_params['DATE']},"+\
                    f"{', '.join(config_params['AUTHOR']) if type(config_params['AUTHOR'])==list else config_params['AUTHOR']})\n"+\
                    config_params['CHANGELOG']
                ),
                parse_mode="MarkdownV2",
                disable_notification=True
            )

    @bot.message_handler(commands=['restart'])
    def restart(message):
        if authentication_is_ok(message, "/restart", admin=True):
            subprocess.check_output("systemctl restart "+config_params['SYSTEMCTL_SERVICE_NAME'], shell=True, text=True)

    return bot, markup

def send_telegram_message(bot, CHAT_ID, message_string, markup_buttons=False, send_without_sound=False):
    try:
        bot.send_message(
            CHAT_ID,
            message_string,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            disable_notification=send_without_sound,
            reply_markup=markup_buttons
        )
    except ApiTelegramException as e:
        print("[!] error - ApiTelegramException: "+e.description)
        print("[!]                               "+message_string)

def scape_telegram_chars(str_input):
    return str_input.replace('_', '\_').replace('*', '\*').replace('[', '\[').replace(']', '\]')\
                    .replace('(', '\(').replace(')', '\)').replace('~', '\~')\
                    .replace('>', '\>').replace('#', '\#').replace('+', '\+').replace('-', '\-')\
                    .replace('=', '\=').replace('|', '\|').replace('{', '\{').replace('}', '\}')\
                    .replace('.', '\.').replace('!', '\!').encode('utf-8','ignore').decode('utf-8') #.replace('`', '\`')\

def format_time(input_datetime_str, include_date=False, return_in_utc=False):

    if input_datetime_str=='-':
        return '-'

    try:
        input_datetime = datetime.fromisoformat(input_datetime_str)
    except ValueError:
        print("!! bad date string format:",input_datetime_str)
        return input_datetime_str

    if return_in_utc:
        input_datetime = input_datetime.astimezone(timezone('UTC'))
    else:
        input_datetime = input_datetime.astimezone(timezone('Europe/Madrid'))

    if include_date:
        result = datetime.strftime(input_datetime,'%d%b %H:%M:%S')
    else:
        result = datetime.strftime(input_datetime,'%H:%M')

    if return_in_utc:
        return result + " UTC"
    else:
        return result

def format_with_fixed_length_key(extractedfields_dict, dict_keylist, scape_chars=True):
    return "\n".join(

        scape_telegram_chars("`{:<13}".format(k))+"`: " + \
        #          ^^ string minimal length
        scape_telegram_chars(str(extractedfields_dict[k])) if scape_chars
        else
        "`{:<13}".format(k)+"`: " + \
        str(extractedfields_dict[k]) for k in dict_keylist

    )+"\n"

def format_as_event_message(data_dict):
    def format_duration(input_duration):
        return str(timedelta(seconds=int(input_duration))).replace(':',"h",1).replace(':',"'",1)+'"'

    # symbols:
    color_mapping = {
        'Alerta - exploit':                            "\N{large red square}",
        'Alerta - programa malicioso':                 "\N{large red square}",
        'Alerta - programa potencialmente no deseado': "\N{large orange square}",
        'Low':                                         "\N{large orange square}",
        'Informational':                               "\N{large blue square}",
        'Unknown':                                     "\N{white large square}"
    }
    arrow = "\N{black rightwards arrow}"

    # shorter keys:
    d = { k.split(':')[-1].replace('seconds','time'): v for k,v in data_dict.items() }

    partial_match_subject = {d['subject']: (k,v) for k,v in color_mapping.items() if k in d['subject']}

    #example: "13:59 HackTool/NetPass en N-2-0056"
    msg = f"{ format_time(d['date_received']) } "                                                + \
          f"{ scape_telegram_chars(d['name']) } "                                                + \
          f"{ partial_match_subject.get(d['subject'], [None,color_mapping['Unknown']])[1] } en " + \
          f"{ scape_telegram_chars(d['host']) }"

    msg += "\n"
    msg += f"{ scape_telegram_chars(partial_match_subject.get(d['subject'], [d['subject']])[0]) }"
    msg += "\n"

    msg += "\n"
    d['date_received'] = format_time(d['date_received'], include_date=True, return_in_utc=True)
    d['group'] = d['group'].replace('\\','/') # because they're like: Todos\B\N
    d['path']  = d['path'].replace('\\','/')  # because they're like: DESKTOPDIRECTORY|\Nirlauncher\NirSoft\mailpv.exe
    if identify_owner(d['host']):
        d['owner'] = identify_owner(d['host'])
    else:
        d['owner'] = "Sin documentar"
    #msg += format_with_fixed_length_key(d, ['name', 'host'])
    msg += format_with_fixed_length_key(d, ['owner', 'group'])
    msg += format_with_fixed_length_key(d, ['path', 'hash_md5'])
    msg += "\n"
    msg += format_with_fixed_length_key(d, ['date_received', 'mail_uid'])

    msg += "\n"
    msg += "            \N{globe with meridians}"+f" [Buscar en Cytomic]({d['url_cytomic']})"+" \N{globe with meridians}"
    msg += "\n"
    msg += "      \N{globe with meridians}"+f" [Buscar en Hybrid Analysis]({d['url_hybrid_analysis']})"+" \N{globe with meridians}"
    msg += "\n"
    msg += "          \N{globe with meridians}"+f" [Buscar en Virus Total]({d['url_virus_total']})"+" \N{globe with meridians}"

    return msg
