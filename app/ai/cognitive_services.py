import os
import urllib.request
import tempfile
import shutil
from config import DefaultConfig

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials


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
        self.project_id = "891232d0-5cda-4a76-adcb-ce15dd53b584"
        self.publish_iteration_name = "IngredientDetectorModel"

    def _authenticate_client(self):
        prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": DefaultConfig.COGNITIVE_SERVICES_KEY})
        predictor = CustomVisionPredictionClient(DefaultConfig.COGNITIVE_SERVICES_ENDPOINT, prediction_credentials)
        return predictor
    
    def detect_objects_in_attachments(self, attachments):
        # Send the image data to the Computer Vision Service
        detected_objects = []
        for attachment in attachments:
            with urllib.request.urlopen(attachment.content_url) as response:

                data = response.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=attachment.name) as tmp_file:
                    tmp_file.write(data)
                with open(tmp_file.name, "rb") as f:
                    detect_objects_results = self.client.detect_image(
                        self.project_id, self.publish_iteration_name, f)

            # Unpack the response from the computer vision service in an easy to work with format
            
            for result in detect_objects_results.predictions:
                object_name = result.tag_name
                detection_confidence = result.probability
                if detection_confidence > 0.5:
                    detected_objects.append(object_name)
            # Remove duplicates
            detected_objects = list(set(detected_objects))
        return detected_objects