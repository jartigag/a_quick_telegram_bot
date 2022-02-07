from datetime import datetime, timedelta
from .network_utils import query_ipgeolocation, extract_resources_from_http_body
import telebot

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

def setup_telegram_bot(config, tg_header, crwd_header):
    bot        = telebot.TeleBot(config.get(tg_header, 'TOKEN'))
    USER_ID    = config.get(crwd_header, 'USER_ID')
    CHAT_ID    = config.get(tg_header, 'CHAT_ID')

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(text='Refrescar', callback_data="cb_refresh"),
    )

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):

        #event_id = "ldt:"+call.message.json['entities'][-1]['url'].split('event/detail/')[-1].replace('/',':')
        event_id = 000

        print(event_id)

        if call.data == "cb_refresh":
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
            reply_markup=markup
        )
        print(f"{event_id} sent again")

    return bot, CHAT_ID, markup

def send_telegram_message(bot, CHAT_ID, message_string, markup_buttons=False):
    bot.send_message(
        CHAT_ID,
        message_string,
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
        reply_markup=markup_buttons
    )

def scape_telegram_chars(str_input):
    return str_input.replace('*','\*').replace('-','\-').replace('_','\_').replace('.','\.').replace('(','\(').replace(')','\)')

def format_as_event_message(data_dict):

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
