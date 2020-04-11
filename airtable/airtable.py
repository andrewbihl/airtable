import requests
import urllib
from os import environ


def _api_url(base_id: str, table_name: str):
    schema = "https://"
    url = "api.airtable.com/v0/{key}/{name}".format(key=base_id, name=table_name)
    return schema + urllib.parse.quote(url)


def _auth_header(secret_key: str):
    if secret_key is None:
        secret_key = environ.get('AIRTABLE_SECRET_KEY', '')
    return {"Authorization": "Bearer %s" % secret_key}


def fetch_all_records(base_id: str, table_name: str, secret_key=None):
    url = _api_url(base_id, table_name)
    resp = requests.get(url, headers=_auth_header(secret_key))
    return resp.json()


def create_records(base_id: str, table_name: str, records: [dict], secret_key=None):
    url = _api_url(base_id, table_name)
    records = [{"fields": r} for r in records]
    resp = requests.post(url, headers=_auth_header(secret_key), json={"records": records})
    return resp.json()
