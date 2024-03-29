import pytest
from event_detecter_bot.telegram_utils import format_time

def test_format_time():

    assert format_time("2022-01-12T15:17:56.145906462Z") == "16:17" # UTC+1
    assert format_time("2022-02-11T11:05:53.289Z")       == "12:05" # UTC+1

    assert format_time("2022-02-11T11:05:53.289Z", include_date=True) == "11Feb 12:05:53" # Europe/Madrid in winter: UTC+1
    assert format_time("2022-04-25T06:16:26Z",     include_date=True) == "25Apr 08:16:26" # Europe/Madrid in summer: UTC+2

    assert format_time("2022-02-11T11:05:53.289Z", include_date=True, return_in_utc=True) == "11Feb 11:05:53 UTC"
    assert format_time("2022-04-25T06:16:26Z",     include_date=True, return_in_utc=True) == "25Apr 06:16:26 UTC"
