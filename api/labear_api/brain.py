"""
A brain is a thing that provides a classifier depending on what it has learned. This module provides a user optimised classifier if awailable. 
"""

from pathlib import Path
from labear_api.cloud_connect import download_blob, gc_is_file
from google.api_core.exceptions import NotFound
import json
from dataclasses import dataclass
from torch import load



CLASSIFIER_PATH = "data/"
CLASSIFIER_NAME = "finetuned_model.pt"
CLASSIFIER_CATS = "cats.json"

fine_tuned_classifiers = {}
@dataclass
class Brains():
    users: []

    def __post_init__(self) -> None:
        self.fine_tuned_classifiers = self.get_classifiers_classes(self.users)
    

    def load_classifier(self, user: str):
        """
        Attempt to load a finetuned classifier for a user. 
        If the user is not registered the classifier speechbrain/urbansound8k_ecapa will be used
        """
        remote_path = Path(f"{user}/{user}_{CLASSIFIER_NAME}")
        path = CLASSIFIER_PATH / remote_path
        print(f"Attempt to load classifier locally: {path}")
        if path.exists():
            classifier = load(path)
        elif gc_is_file(bucket_name="data_labear", source_blob_name=str(remote_path)):
            print(f"Downloading from gcs path: {remote_path}")
            try:
                folder = path.parent
                folder.mkdir()
            except FileExistsError as e:
                print(f"Folder already exists: {e}")
            download_blob(bucket_name="data_labear", source_blob_name=str(remote_path), destination_file_name=path)
            classifier = load(path)
        else:
            print(f"No classifier available for user: {user}. Reverting to using classifier: speechbrain/urbansound8k_ecapa")
            classifier = None
        classifier = {'classifier':classifier}
        return classifier

    def load_classes(self, user: str):
        """
        Load classes for a user from users cats.json file. 
        If the user is not registered the classifier speechbrain/urbansound8k_ecapa will be used
        """
        remote_path = Path(f"{user}/{user}_{CLASSIFIER_CATS}")
        path = CLASSIFIER_PATH / remote_path
        print(f"Attempt to load classes locally: {path}")
        cats = {}
        if path.exists():
            with open(path, 'r') as file: 
                cats = json.load(file)
        elif gc_is_file(bucket_name="data_labear", source_blob_name=str(remote_path)):
            print(f"Downloading from gcs path: {remote_path}")
            try:
                folder = path.parent
                folder.mkdir()
            except FileExistsError as e:
                print(f"Folder already exists: {e}")
            download_blob(bucket_name="data_labear", source_blob_name=str(remote_path), destination_file_name=path)
            with open(path, 'r') as file: 
                cats = json.load(file)
        else:
            print(f"No classifier available for user: {user}. Reverting to using classifier: speechbrain/urbansound8k_ecapa")
        return cats

    def get_classifiers_classes(self, users: list):
        fine_tuned ={}
        for user in users:
            d = {}
            classifer = self.load_classifier(user)
            classes = self.load_classes(user)
            d.update(classes)
            d.update(classifer)
            fine_tuned[user] = d
        return fine_tuned
    
    def brain(self, user):
        try:
            classifier = self.fine_tuned_classifiers[user]['classifier']
        except KeyError as e:
            print("No classifier found")
            classifier = None
        if classifier is None:
            return None, None
        else:
            cats = self.fine_tuned_classifiers[user]['cats']
            return classifier, cats
def main(): 
    brains = Brains(['g28','g29'])
    s, t = brains.brain("g28")
    print(f"{s}, {t}")
if __name__ == "__main__":
    main()