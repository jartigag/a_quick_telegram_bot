from datetime import datetime, timedelta
from .network_utils import query_ipgeolocation, extract_resources_from_http_body, identify_organization_network
from pytz import timezone
import re
import subprocess
import telebot
from telebot.apihelper import ApiTelegramException

def extract_fields(event):
    return event

def get_events(event_id):
    return {
        'body': {
            'text': 'EVENT BODY', 'resources': [
                {"created_timestamp": "2022-01-30T23:00:00.145906462Z", "event_id": "ldt:99999999999999999999999999999999", "external_ip": "130.206.159.235"}
            ]
        }
    }

def setup_telegram_bot(config_params):
    bot = telebot.TeleBot(config_params['TOKEN'])

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(text='Refrescar', callback_data="cb_refresh"),
    )

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):

        #event_id = "ldt:"+call.message.json['entities'][-1]['url'].split('event/detail/')[-1].replace('/',':')
        event_id = 000

        if call.data == "cb_refresh":
            print(f"[+] T2: {event_id} re-sent", flush=True)
            bot.answer_callback_query(call.id, "Se ha enviado el evento de nuevo")

        print(call.id)

        last_event = extract_resources_from_http_body( get_events(event_id) )[-1]
        event_with_extracted_fields = extract_fields(last_event)

        print(event_with_extracted_fields)

        bot.reply_to(
            call.message,
            format_as_event_message(event_with_extracted_fields),
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            disable_notification=True,
            reply_markup=markup
        )
        print(f"{event_id} sent again")

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
                f"EventDetecterBot v{scape_telegram_chars(config_params['VERSION'])}: "+\
                f"Bot de notificaciones por Telegram"+"\n\n"                                             +\
                    "Comandos:\n"                                                                        +\
                    "\- /whois` 192.168.1.24`\n identifica una dirección IP en las redes documentadas\n" +\
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
                    f",SCHEDULE_DELAY_SECS={c['SCHEDULE_DELAY_SECS']}, LAST_N_EVENTS={c['LAST_N_EVENTS']}" +\
                    "\n\n"+systemctl_output
                ),
                parse_mode="MarkdownV2",
                disable_notification=True
            )

    @bot.message_handler(commands=['whois'])
    def send_whois(message):
        if authentication_is_ok(message, "/whois"):
            input_ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}', message.text )
            for inputip_str in input_ips:
                identified_network = identify_organization_network(inputip_str)
                if identified_network:
                    reply = inputip_str+" está en "+identified_network
                else:
                    reply = inputip_str+" no está en ninguna subred conocida"
                bot.reply_to(
                    message,
                    reply,
                    disable_notification=True
                )
            if not input_ips:
                bot.reply_to(
                    message,
                    "Por favor, especifique al menos una dirección IP válida",
                    disable_notification=True
                )

    @bot.message_handler(commands=['about'])
    def send_about(message):
        if authentication_is_ok(message, "/about"):
            bot.reply_to(
                message,
                scape_telegram_chars(
                    f"Telefalcon v{config_params['VERSION']} ({config_params['DATE']}, {config_params['AUTHOR']})\n"+\
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

def scape_telegram_chars(str_input):
    return str_input.replace('_', '\_').replace('*', '\*').replace('[', '\[').replace(']', '\]')\
                    .replace('(', '\(').replace(')', '\)').replace('~', '\~')\
                    .replace('>', '\>').replace('#', '\#').replace('+', '\+').replace('-', '\-')\
                    .replace('=', '\=').replace('|', '\|').replace('{', '\{').replace('}', '\}')\
                    .replace('.', '\.').replace('!', '\!').encode('utf-8','ignore').decode('utf-8') #.replace('`', '\`')\

def format_as_event_message(data_dict):
    def format_time(input_datetime_str, include_date=False):
        try:
            input_datetime = datetime.fromisoformat(
                input_datetime_str.replace('Z','').split('.')[0]+".000000+00:00"
                #                           so a datetime object is obtained ^^
                #                           with tzinfo=datetime.timezone.utc
            )
        except ValueError:
            print("!! bad date string format:",input_datetime_str)
            return input_datetime_str
        if include_date:
            return datetime.strftime(input_datetime,'%d%b %H:%M:%S UTC')
        else:
            return datetime.strftime(input_datetime.astimezone(timezone('Europe/Madrid')),'%H:%M')
            #                                   so it will be printed as local time ^^

    def format_duration(input_duration):
        return str(timedelta(seconds=int(input_duration))).replace(':',"h",1).replace(':',"'",1)+'"'

    def format_with_fixed_length_key(extractedfields_dict, dict_keylist):
        return "\n".join(
            scape_telegram_chars("`{:<17}".format(k))+"`: " + \
            #          ^^ string minimal length
            scape_telegram_chars(str(extractedfields_dict[k])) for k in dict_keylist
        )+"\n"

    # symbols:
    color_mapping = {
        'High': "\N{large red square}",   'Medium': "\N{large orange square}",
        'Low': "\N{large orange square}", 'Informational': "\N{large blue square}"
    }
    arrow = "\N{black rightwards arrow}"

    # shorter keys:
    d = { k.split(':')[-1].replace('seconds','time'): v for k,v in data_dict.items() }

    #example: "15:17 PrettyGoodNewOffer 🟧 in Infojobs.com"
    #network = scape_telegram_chars(identify_network(d['local_ip']))
    #if network!="otra red":
    #    network = "*"+network+"*"
    msg = f"{ format_time(d['created_timestamp']) } "          + \
          f"{ scape_telegram_chars('PrettyGoodNewOffer') } "        + \
          f"{ color_mapping['Medium'] } "

    #example: "[[+]](https://ipgeolocation.io/ip-location/130.206.159.235)` external_ip   :` 130.206.159.235 (Pamplona, Red.es)
    geodata = query_ipgeolocation(d['external_ip'])
    msg += "\n"
    msg += f"[\( \+ \)](https://ipgeolocation.io/ip-location/{ d['external_ip'] })` external\_ip  `: "  + \
           f"`{ scape_telegram_chars(d['external_ip']) }` "                                             + \
           f"\({ scape_telegram_chars(geodata[0]) }, { scape_telegram_chars(geodata[1]) }\)"

    #msg += "\n"
    #msg += format_with_fixed_length_key(
    #    d, ['site_name', 'machine_domain']
    #)

    #msg += "\n"
    #for time_key in ['created_timestamp', 'date_updated']:
    #    d[time_key] = format_time(d[time_key], include_date=True)
    #msg += format_with_fixed_length_key(
    #    d, ['created_timestamp', 'date_updated']
    #)

    msg += "\n"
    msg += "       \N{globe with meridians}"+f" [Open in the website](https://google.es)"+" \N{globe with meridians}"

    return msg
