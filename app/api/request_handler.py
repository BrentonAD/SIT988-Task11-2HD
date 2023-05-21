import requests
import urllib.parse
import json

from config import DefaultConfig

def get_user(id: str):
    
    parsed_id = urllib.parse.quote(id)
    url = DefaultConfig.API_BASE_URL + "users/" + parsed_id
    response = requests.get(url)
    try:
        user = json.loads(response.content)[0]
    except IndexError:
        user = None

    return user

def add_or_update_user(id: str, name: str):

    url = DefaultConfig.API_BASE_URL + "users"
    body = {"id": id, "name": name}
    response = requests.post(url, json=body)
