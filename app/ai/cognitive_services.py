import os
import urllib.request
import tempfile
import shutil
from config import DefaultConfig

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

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

class ImageAnalytics:
    def __init__(self):
        self.client = self._authenticate_client()

    def _authenticate_client(self):
        cv_credential = CognitiveServicesCredentials(DefaultConfig.COGNITIVE_SERVICES_KEY)
        computer_vision_client = ComputerVisionClient(
            endpoint=DefaultConfig.COGNITIVE_SERVICES_ENDPOINT, 
            credentials=cv_credential
        )
        return computer_vision_client
    
    def detect_objects_in_attachments(self, attachments):
        # Send the image data to the Computer Vision Service
        detected_objects = []
        for attachment in attachments:
            with urllib.request.urlopen(attachment.content_url) as response:

                data = response.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=attachment.name) as tmp_file:
                    tmp_file.write(data)
                with open(tmp_file.name, "rb") as f:
                    detect_objects_results = self.client.detect_objects_in_stream(f)

            # Unpack the response from the computer vision service in an easy to work with format
            
            for result in detect_objects_results.objects:
                object_name = result.object_property
                detection_confidence = result.confidence
                detected_objects.append(object_name)

        return detected_objects