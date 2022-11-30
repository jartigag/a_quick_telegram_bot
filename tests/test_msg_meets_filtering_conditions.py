import pytest
from event_detecter_bot.__main__ import msg_meets_filtering_conditions, parse_filtering_conditions

not_matching_msg_because_of_severity_and_network = """
    15:40 Event \N{large blue square} en MiRedLocal
    \N{japanese symbol for beginner} Stopped

    HOST-1$@HOST-1 (10.1.1.1)

    ( + ) (https://ipgeolocation.io/ip-location/130.206.159.235) external_ip  : 130.206.159.235 (Pamplona, Red.es)

    tags             : -

    created_timestamp: 06jun 13:40:19 UTC
    first_behavior   : 06jun 13:39:36 UTC
    last_behavior    : 06jun 13:39:36 UTC

    status           : new
    time_to_triaged  : 0h00'00"
    time_to_resolved : 0h00'00"
    date_updated     : 06jun 13:40:22 UTC
    assigned_to_name : -
    assigned_to_uid  : -
    url_id           : 1
"""

matching_msg_because_of_severity_and_network = """
    13:17 Event \N{large red square} en MiRedLocal
    \N{white heavy check mark} Stopped

    HOST-1$@HOST-1 (10.1.1.1)

    ( + ) (https://ipgeolocation.io/ip-location/130.206.159.235) external_ip  : 130.206.159.235 (Pamplona, Red.es)

    tags             : -

    created_timestamp: 03jun 11:17:18 UTC
    first_behavior   : 03jun 11:16:35 UTC
    last_behavior    : 03jun 11:16:35 UTC

    status           : new
    time_to_triaged  : 0h00'00"
    time_to_resolved : 0h00'00"
    date_updated     : 03jun 11:17:28 UTC
    assigned_to_name : -
    assigned_to_uid  : -
    url_id           : 2
"""

matching_msg_because_of_tag = """
    11:01 Event \N{large red square}
    \N{white heavy check mark} Stopped

    HOST-1$@HOST-1 (10.1.1.1)

    ( + )    ( + ) (https://ipgeolocation.io/ip-location/130.206.159.235) external_ip  : 130.206.159.235 (Pamplona, Red.es)

    tags             :
    \N{label}MiTag

    created_timestamp: 24may 09:01:54 UTC
    first_behavior   : 24may 09:00:34 UTC
    last_behavior    : 24may 09:00:34 UTC

    status           : new
    time_to_triaged  : 0h00'00"
    time_to_resolved : 0h00'00"
    date_updated     : 24may 09:09:16 UTC
    assigned_to_name : -
    assigned_to_uid  : -
    url_id           : 3
"""

@pytest.mark.parametrize("config_file", ["tests/config_eventdetecterbot_andcondition_or_andcondition.ini", "tests/config_eventdetecterbot_one_condition.ini"])
def test_msg_meets_filtering_conditions(config_file):
    import configparser
    from event_detecter_bot.telegram_utils import scape_telegram_chars

    config = configparser.ConfigParser()
    config.read(config_file)

    FILTERING_CONDITIONS = parse_filtering_conditions(config.get("@event_detecter_bot", 'FILTERING_CONDITIONS'))

    assert msg_meets_filtering_conditions("", FILTERING_CONDITIONS)==False
    assert msg_meets_filtering_conditions(scape_telegram_chars(not_matching_msg_because_of_severity_and_network), FILTERING_CONDITIONS)==False
    assert msg_meets_filtering_conditions(scape_telegram_chars(matching_msg_because_of_severity_and_network), FILTERING_CONDITIONS)==True
    assert msg_meets_filtering_conditions(scape_telegram_chars(matching_msg_because_of_tag), FILTERING_CONDITIONS)==True
