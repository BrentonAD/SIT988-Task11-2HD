import requests
import urllib.parse
import json

from config import DefaultConfig

from typing import List

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

def get_user_allergies(userid: str):
    
    parsed_id = urllib.parse.quote(userid)
    url = DefaultConfig.API_BASE_URL + "allergies/"+parsed_id
    response = requests.get(url)
    try:
        allergies_response = json.loads(response.content)
        allergies = [ row["allergy_ingredient"] for row in allergies_response ]
    except IndexError:
        allergies = None
    return allergies

def add_user_allergies(userid: str, allergies: List[str]):

    url = DefaultConfig.API_BASE_URL + "allergies"
    body = [
        { "userid": userid, "allergy_ingredient": allergy }
            for allergy in allergies
    ]
    reponse = requests.post(url, json=body)

def add_user_preferences(userid: str, preferences: List[dict]):

    url = DefaultConfig.API_BASE_URL + "preferences"
    body = [
        { 
            "userId": userid,
            "recipe": preference["recipe"] ,
            "marked_as_preference": preference["marked_as_preference"]
        }
        for preference in preferences
    ]
    reponse = requests.post(url, json=body)