"""
A brain is a thing that provides a classifier depending on what it has learned. This module provides a user optimised classifier if awailable. 
"""

from pathlib import Path
from labear_api.cloud_connect import download_blob, gc_is_file, gc_list_dirs
from google.api_core.exceptions import NotFound
import json
from dataclasses import dataclass, field
from torch import load



CLASSIFIER_PATH = "data/"
CLASSIFIER_NAME = "finetuned_model.pt"
CLASSIFIER_CATS = "cats.json"
GC_BUCKET_NAME = "data_labear"
GC_USERS = "users/"

fine_tuned_classifiers = {}
@dataclass
class Brains():
    users: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.users) < 1:
            print("Loading users")
            self.users = self.get_users()
        self.fine_tuned_classifiers = self.get_classifiers_classes(self.users)


    def load_classifier(self, user: str):
        """
        Attempt to load a finetuned classifier for a user. 
        If the user is not registered the classifier speechbrain/urbansound8k_ecapa will be used
        """
        user_classifier = Path(f"{user}/{user}_{CLASSIFIER_NAME}")
        gc_path = GC_USERS / user_classifier
        local_path = CLASSIFIER_PATH / user_classifier
        print(f"Attempt to load classifier locally: {local_path}")
        if local_path.exists():
            classifier = load(local_path)
        elif gc_is_file(bucket_name=GC_BUCKET_NAME, source_blob_name=str(gc_path)):
            print(f"Downloading from gcs path: {gc_path}")
            try:
                folder = local_path.parent
                folder.mkdir()
            except FileExistsError as e:
                print(f"Folder already exists: {e}")
            download_blob(bucket_name=GC_BUCKET_NAME, source_blob_name=str(gc_path), destination_file_name=local_path)
            classifier = load(local_path)
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
        user_cats = Path(f"{user}/{user}_{CLASSIFIER_CATS}")
        gc_path = GC_USERS / user_cats
        local_path = CLASSIFIER_PATH / user_cats
        print(f"Attempt to load classes locally: {local_path}")
        cats = {}
        if local_path.exists():
            with open(local_path, 'r') as file: 
                cats = json.load(file)
        elif gc_is_file(bucket_name=GC_BUCKET_NAME, source_blob_name=str(gc_path)):
            print(f"Downloading from gcs path: {gc_path}")
            try:
                folder = local_path.parent
                folder.mkdir()
            except FileExistsError as e:
                print(f"Folder already exists: {e}")
            download_blob(bucket_name=GC_BUCKET_NAME, source_blob_name=str(gc_path), destination_file_name=local_path)
            with open(local_path, 'r') as file: 
                cats = json.load(file)
        else:
            print(f"No classifier available for user: {user}. Reverting to using classifier: speechbrain/urbansound8k_ecapa")
        return cats
    
    def get_users(self):
        dirs = gc_list_dirs(bucket_name=GC_BUCKET_NAME, path=GC_USERS)
        users = [dir.strip('/') for dir in dirs]
        return users


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
    brains = Brains()
    s, t = brains.brain("g28")
    print(f"{s}, {t}")
if __name__ == "__main__":
    main()