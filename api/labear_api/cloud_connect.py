from google.cloud import storage
from google.cloud.storage import transfer_manager
from google.oauth2 import service_account
import os
import json
from pathlib import Path
from json.decoder import JSONDecodeError
from google.api_core.exceptions import NotFound
from datetime import datetime
from loguru import logger


PROJECT = 'labear'

TRANSFER_MANAGER_DEADLINE = None
TRANSFER_MANAGER_SKIP_IF_EXISTS = False
TRANSFER_MANAGER_RAISE_EXEPTION = False

def storage_client_gc():

    # GOOGLE_APPLICATION_CREDENTIALS is added to secrets in fly.io which are loaded
    # as environment variables in the fly-machine at runtime.
    try:
        gc_env = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        creds = json.loads(gc_env) # Convertion to json format as its saved as string in fly.io secret.
        credentials = service_account.Credentials.from_service_account_info(
        creds)
    except (KeyError, ValueError):
        logger.info('Loading credentials (Google service account) from JSON failed - will try default method from environment')
        storage_client = storage.Client(project=PROJECT)
    else:
        storage_client = storage.Client(project=PROJECT, credentials=credentials)
    
    return storage_client

STORAGE_CLIENT = storage_client_gc()

def upload_many_from_files(
    bucket,
    files,
    source_directory="",
    blob_name_prefix="",
    blob_constructor_kwargs=None,
    *,
    additional_blob_attributes=None,
):

    if blob_constructor_kwargs is None:
        blob_constructor_kwargs = {}
    if additional_blob_attributes is None:
        additional_blob_attributes = {}

    file_blob_pairs = []

    for file in files:
        blob_name = blob_name_prefix + file.filename
        blob = bucket.blob(blob_name, **blob_constructor_kwargs)
        for prop, value in additional_blob_attributes.items():
            setattr(blob, prop, value)
        file_blob_pairs.append((file.file, blob))
    
    return transfer_manager.upload_many(
        file_blob_pairs,
        skip_if_exists=TRANSFER_MANAGER_SKIP_IF_EXISTS,
        upload_kwargs=None,
        deadline=TRANSFER_MANAGER_DEADLINE,
        raise_exception=TRANSFER_MANAGER_RAISE_EXEPTION,
        worker_type=transfer_manager.THREAD, # "thread" for smallish files, "process" for large files
        max_workers=transfer_manager.DEFAULT_MAX_WORKERS,
    )



def upload_many(bucket_name, files, workers=8):
    bucket = STORAGE_CLIENT.bucket(bucket_name)

    results = upload_many_from_files(bucket, files)

    for file, result in zip(files, results):
    #    # The results list is either `None` or an exception for each filename in
    #    # the input list, in order.
        if isinstance(result, Exception):
            logger.info(f"Failed to upload {file.filename} due to exception: {result}")
        else:
            logger.info(f"Uploaded {file.filename} to {bucket.name}.")

def upload_blob(bucket_name, file_obj, destination_folder_name, destination_file_name):
    """Uploads a file to the bucket."""
    # Create the full GCS path (including the folder and file name)
    gcs_file_path = os.path.join(destination_folder_name, destination_file_name)
    bucket = STORAGE_CLIENT.bucket(bucket_name)
    blob = bucket.blob(gcs_file_path)
    blob.upload_from_file(file_obj, rewind=True)

    logger.info(
        f"File {destination_file_name} uploaded to {destination_folder_name}."
    )

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    
    bucket = STORAGE_CLIENT.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    logger.info(
        "Downloaded storage object {} from bucket {} to local file {}.".format(
            source_blob_name, bucket_name, destination_file_name
        )
    )

        
def main():

    logger.info("Hello World!")
  # Example usage
    bucket_name = 'data_labear'
    folder_path = 'users/g28/'  # Don't forget the trailing '/'
    file_type = ".pt"    
    #upload_blob(bucket_name=bucket_name, file_obj='test_submit.wav', destination_folder_name=folder_path, destination_file_name='test_upload.wav')
if __name__ == "__main__":
    main()