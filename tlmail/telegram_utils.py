from datetime import datetime, timedelta
import json
from pytz import timezone
import os
import pickle
import subprocess
import telebot
from telebot.apihelper import ApiTelegramException

def get_cache():
    if os.path.isfile("cache.pkl"):
        with open("cache.pkl", 'rb') as f:
            return pickle.load(f)
    else:
        return {
            "last_offense_id": 2051,
            "previous_offenses": []
        }

def set_cache(data):
    with open("cache.pkl", 'wb') as f:
        pickle.dump(data, f)

def setup_telegram_bot(config_params):
    bot = telebot.TeleBot(config_params['TOKEN'])

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        data = json.loads(call.data)
        callback = data["cb"]

        if callback == "cb_auto_assign":
            offense_id = data["oid"]

            usr = call.from_user
            name = f"{usr.first_name} {usr.last_name} (tg_user_id={usr.id})"

            try:
                cache = get_cache()
                previous_offenses = cache["previous_offenses"]

                for offense in previous_offenses:
                    if offense['id']==offense_id:
                        offense['assigned'] = name
                        break

                set_cache(cache)

                bot.reply_to(
                    call.message,
                    scape_telegram_chars(
                        f"Ofensa {offense_id} auto-asignada a {name}\n"
                    ),
                    parse_mode="MarkdownV2",
                    disable_notification=True
                )
                print(f"Offense {offense_id} auto-assigned to {name}", flush=True)
            except Exception as e:
                print("[!]",e, flush=True)
                bot.reply_to(
                    call.message,
                    scape_telegram_chars(f"[!] Error asignando la ofensa {offense_id} a {name}\n"),
                    parse_mode="MarkdownV2",
                    disable_notification=True
                )
                print(f"[!] Error assigning offense {offense_id} to {name}", flush=True)

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
                f"TeleMail v{scape_telegram_chars(config_params['VERSION'])}: "+\
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
                    f"Telefalcon v{config_params['VERSION']} ({config_params['DATE']}, "+\
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

    return bot

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
    def timestamp_to_str(ts):
        ts = ts / 1000.0
        return datetime.fromtimestamp(ts).strftime("%d-%m-%Y %H:%M:%S")

    msg = f"""
*Nueva ofensa a revisar en QRadar*
*ID*: {scape_telegram_chars(str(data_dict["id"]))}
*Desc*: {scape_telegram_chars(data_dict["description"])}
*Red origen*: {scape_telegram_chars(data_dict["source_network"])}
*IP origen*: {scape_telegram_chars(data_dict["offense_source"])}
{scape_telegram_chars("=====================")}
*Día y Hora*: {scape_telegram_chars(timestamp_to_str(data_dict["start_time"]))}
*Magnitud*: {scape_telegram_chars(str(data_dict["magnitude"]))}
*Severidad*: {scape_telegram_chars(str(data_dict["severity"]))}
    """

    return msg
