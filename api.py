from collections import Counter
from sys import stderr
import os

from esipy import App, EsiSecurity, EsiClient
from esipy.events import AFTER_TOKEN_REFRESH

from common import mineral_ids, ore_ids, typeid_to_name


def get_api(fn, scopes):
    esi_app = App.create('https://esi.tech.ccp.is/latest/swagger.json?datasource=tranquility')
    esi_security = EsiSecurity(
        app=esi_app,
        redirect_uri='http://localhost:8080/callback',
        client_id='0b9ac4978a9a4feba20a7eba4f666a46',
        secret_key='odtDKZWZbwbFnBHNXnOhRX50YrU49owBw1qE3v7p',
    )
    esi_client = EsiClient(retry_requests=True, security=esi_security)

    def write_refresh_token(refresh_token, **kwargs):
        with open(fn, "w") as f:
            f.write(refresh_token)
    AFTER_TOKEN_REFRESH.add_receiver(write_refresh_token)

    if os.path.isfile(fn):
        with open(fn) as f:
            token = open(fn).read()
        esi_security.update_token({'access_token': '', 'expires_in': -1, 'refresh_token': token})
        tokens = esi_security.refresh()
    else:
        print(esi_security.get_auth_uri(scopes=scopes))
        tokens = esi_security.auth(input())
    write_refresh_token(**tokens)

    api_info = esi_security.verify()

    return api_info, esi_app, esi_client


def mats_api():
    r = Counter()
    for i in s.find_all("row"):
        r[typeid_to_name(i["typeID"])] += int(i["quantity"])
    return r

def bps_api():
    r = Counter()
    return s.find_all("row")
