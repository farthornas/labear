from cloudpathlib import GSPath, GSClient
from pathlib import Path
from loguru import logger
from torch import load
import json
from dataclasses import dataclass, field
from labear_api.cloud_connect import storage_client_gc

# Constants
CLASSIFIER_PATH = Path("data/")
GC_BUCKET_NAME = "data_labear"
GC_USERS = "users"
STORAGE_CLIENT = storage_client_gc()

client = GSClient(storage_client=STORAGE_CLIENT)

@dataclass
class Brains:
    fine_tuned_classifiers: dict = field(default_factory=dict)
    gc_users_path: GSPath = field(init=False)

    def __post_init__(self) -> None:
        # Initialize the GSPath object
        self.gc_users_path = GSPath(f"gs://{GC_BUCKET_NAME}/{GC_USERS}", client=client)

    def load_classifier(self, user: str):
        """Attempt to load a fine-tuned classifier for a user."""
        user_path = self.gc_users_path / user
        classifier_name = self.get_latest_file_in_folder(user_path, file_extension=".pt")
        if classifier_name:
            return self._load_user_file(user, classifier_name, 'classifier')
        else:
            logger.info(f"No classifier available for user: {user}. Reverting to default classifier.")
            return None

    def load_classes(self, user: str):
        """Load classes for a user from the user's 'cats.json' file."""
        user_path = self.gc_users_path / user
        class_name = self.get_latest_file_in_folder(user_path, file_extension=".json")
        return self._load_user_file(user, class_name, 'classes') or {}

    def brain(self, user: str):
        """Return the classifier and classes for a user."""
        # Lazy loading of classifiers and classes if not already loaded
        if user not in self.fine_tuned_classifiers:
            logger.info(f"Loading model and classes for user: {user}")
            classifier = self.load_classifier(user)
            if classifier is None:
                return None, None
            classes = self.load_classes(user)
            self.fine_tuned_classifiers[user] = {'classifier': classifier, 'classes': classes}

        user_data = self.fine_tuned_classifiers.get(user)
        return user_data['classifier'], user_data['classes']['cats']

    def _load_user_file(self, user: str, filename: str, file_type: str):
        """Helper function to load a user's file from cloud or local storage."""
        user_file_path = self.gc_users_path / user / filename
        local_path = CLASSIFIER_PATH / user / filename

        # Try downloading directly from cloud
        if not local_path.exists():
            try:
                logger.info(f"Downloading {file_type} from GCS: {user_file_path}")
                user_file_path.download_to(local_path)
            except FileNotFoundError:
                logger.info(f"{file_type} not found for user: {user}")
                return None

        return self._load_local_file(local_path, file_type)

    def _load_local_file(self, path: Path, file_type: str):
        """Helper function to load a local file based on its type (classifier or classes)."""
        if file_type == 'classifier':
            return load(path)  # Load classifier
        elif file_type == 'classes':
            with open(path, 'r') as file:
                return json.load(file)

    def get_latest_file_in_folder(self, path: GSPath, file_extension: str):
        """Retrieve the latest file in a folder with the given file extension."""
        files = [f for f in path.glob(f"*{file_extension}") if f.is_file()]
        if files:
            # Sort files by modification time
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            return latest_file.name
        return None

def main():
    brains = Brains()
    classifier, classes = brains.brain("engine")       
if __name__ == "__main__":
    main()
