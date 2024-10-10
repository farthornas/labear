"""
A brain is a thing that provides a classifier depending on what it has learned. This module provides a user optimised classifier if awailable. 
"""

from pathlib import Path
from labear_api.cloud_connect import download_blob, gc_is_file, gc_list_dirs, storage_client_gc, get_latest_file_in_folder
from google.api_core.exceptions import NotFound
import json
from dataclasses import dataclass, field
from torch import load
from loguru import logger



CLASSIFIER_PATH = "data/"
CLASSIFIER_NAME = "finetuned_model.pt"
CLASSIFIER_CATS = "cats.json"
GC_BUCKET_NAME = "data_labear"
GC_USERS = "users/"



import json
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class Brains:
    users: list[str] = field(default_factory=list)
    fine_tuned_classifiers: dict = field(default_factory=dict)
    storage_client: object = None 

    
    def __post_init__(self) -> None:
        # Allow the storage_client to be injected for testability
        if self.storage_client is None:
            self.storage_client = self.create_storage_client()
        
        # Defer loading users to a separate method to avoid side effects in the constructor
        if not self.users:
            logger.info("Loading users...")
            self.users = self.get_users()
        
        # Same for classifiers
        if not self.fine_tuned_classifiers:
            self.fine_tuned_classifiers = self.get_classifiers_classes(self.users)
    
    def create_storage_client(self):
        """
        Creates and returns a storage client.
        This function is separated out for easier mocking in unit tests.
        """
        return storage_client_gc()

    def load_classifier(self, user: str):
        """
        Attempt to load a fine-tuned classifier for a user. 
        If the user is not registered, the classifier 'speechbrain/urbansound8k_ecapa' will be used.
        """
        path = Path(f"{GC_USERS}/{user}") 
        classifier = None

        classifier_name = get_latest_file_in_folder(GC_BUCKET_NAME, path, self.storage_client, file_extension=".pt")
        if classifier_name:
            classifier = self._load_user_file(user, classifier_name, 'classifier')
        if classifier is None:
            logger.info(f"No classifier available for user: {user}. Reverting to using classifier: speechbrain/urbansound8k_ecapa")
        return {'classifier': classifier}

    def load_classes(self, user: str):
        """
        Load classes for a user from the user's 'cats.json' file.
        If the user is not registered, the classifier 'speechbrain/urbansound8k_ecapa' will be used.
        """
        path = Path(f"{GC_USERS}/{user}") 

        class_name = get_latest_file_in_folder(GC_BUCKET_NAME, path, self.storage_client, file_extension=".json")
        
        classes = self._load_user_file(user, class_name, 'classes')
        if classes is None:
            logger.info(f"No classes available for user: {user}. Reverting to using default.")
        return classes or {}

    def get_users(self):
        """Retrieve the list of users from the storage."""
        dirs = gc_list_dirs(bucket_name=GC_BUCKET_NAME, path=GC_USERS, storage_client=self.storage_client)
        return [dir.strip('/') for dir in dirs]

    def get_classifiers_classes(self, users: list):
        """Load both classifiers and classes for all users."""
        fine_tuned = {}
        for user in users:
            logger.info(f"*****Fetching model for user:{user}*****")
            user_data = {}
            user_data.update(self.load_classifier(user))
            user_data.update(self.load_classes(user))
            fine_tuned[user] = user_data
        return fine_tuned

    def brain(self, user: str):
        """Return the classifier and classes for a user, or None if not available."""
        try:
            classifier = self.fine_tuned_classifiers[user]['classifier']
        except KeyError:
            logger.info(f"No classifier found for user: {user}")
            return None, None
        cats = self.fine_tuned_classifiers.get(user, {}).get('cats')

        return classifier, cats

    def _load_user_file(self, user: str, filename: str, file_type: str):
        """
        Helper function to load a user's file (classifier or classes) from local or GCS storage.
        """ 
        user_file = Path(f"{user}/{filename}")
        local_path = CLASSIFIER_PATH / user_file
        gc_path = GC_USERS / user_file

        if local_path.exists():
            logger.info(f"Load {file_type} from local path: {local_path}")
            return self._load_local_file(local_path, file_type)
        
        if gc_is_file(GC_BUCKET_NAME, str(gc_path), storage_client=self.storage_client):
            logger.info(f"Downloading {file_type} from GCS path: {gc_path}")
            self._download_from_gcs(gc_path, local_path)
            return self._load_local_file(local_path, file_type)

        return None

    def _load_local_file(self, path: Path, file_type: str):
        """Helper function to load a local file based on file type (classifier or classes)."""
        if file_type == 'classifier':
            return load(path)  # Assuming `load` is a method to load the classifier
        elif file_type == 'classes':
            with open(path, 'r') as file:
                return json.load(file)

    def _download_from_gcs(self, gc_path: Path, local_path: Path):
        """Download a file from Google Cloud Storage and ensure the local folder exists."""
        folder = local_path.parent
        folder.mkdir(parents=True, exist_ok=True)
        download_blob(GC_BUCKET_NAME, str(gc_path), local_path, storage_client=self.storage_client)
def main():

    brains = Brains()
    users = brains.get_users()
    test = brains.brain("g28_huawei")
    logger.info(users)
if __name__ == "__main__":
    main()