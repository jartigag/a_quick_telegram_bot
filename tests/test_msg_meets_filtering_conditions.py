import pytest
from tlmail.__main__ import msg_meets_filtering_conditions

FILTERING_CONDITIONS = [ ["URGENTE"], ["REDDEREDES", "Incidencia"] ]

not_matching_msg = """
    12:43 \N{large orange square} Alta de x en el servicio REDDEREDES

    https://support.unared.es/Ticket/Display.html?id=893158

    date_received: 14jul 10:43:00 UTC
    mail_uid:      97
"""

matching_msg = """
    12:12 \N{large orange square} Alta URGENTE de Y en el servicio REDDEREDES

    https://support.unared.es/Ticket/Display.html?id=892940

    date_received: 14jul 10:12:00 UTC
    mail_uid:      101
"""

def test_msg_meets_filtering_conditions():
    from tlmail.telegram_utils import scape_telegram_chars

    assert msg_meets_filtering_conditions("", FILTERING_CONDITIONS)==False
    assert msg_meets_filtering_conditions(scape_telegram_chars(not_matching_msg), FILTERING_CONDITIONS)==False
    assert msg_meets_filtering_conditions(scape_telegram_chars(matching_msg), FILTERING_CONDITIONS)==True
