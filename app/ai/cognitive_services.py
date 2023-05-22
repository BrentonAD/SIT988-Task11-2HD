from config import DefaultConfig

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

from typing import List

class TextAnalytics:
    def __init__(self):
        self.client = self._authenticate_client()

    def _authenticate_client(self):
        ta_credential = AzureKeyCredential(DefaultConfig.COGNITIVE_SERVICES_KEY)
        text_analytics_client = TextAnalyticsClient(
            endpoint=DefaultConfig.COGNITIVE_SERVICES_ENDPOINT, 
            credential=ta_credential
        )
        return text_analytics_client
    
    def key_phrase_extraction(self, documents: List[str]):
        
        try:
            response = self.client.extract_key_phrases(documents=documents)[0]
            if response.is_error:
                print(response.id, response.error)
                return None
            else:
                return response.key_phrases

        except Exception as err:
            print("Encountered exception. {}".format(err))
