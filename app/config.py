import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    API_BASE_URL = os.environ.get("API_BASE_URL","")
    COGNITIVE_SERVICES_KEY = os.environ.get("COGNITIVE_SERVICES_KEY","")
    COGNITIVE_SERVICES_ENDPOINT = os.environ.get("COGNITIVE_SERVICES_ENDPOINT","")