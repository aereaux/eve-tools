#!/usr/bin/env python3

import sys
from api import get_api

api_info, esi_app, esi_client = get_api(sys.argv[1], ["esi-location.read_location.v1"])

op = esi_app.op['get_characters_character_id_location'](character_id=api_info['CharacterID'])

print(esi_client.request(op).data["solar_system_id"])


