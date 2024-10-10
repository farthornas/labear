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

def upload_many_from_files(
    bucket,
    files,
    source_directory="",
    blob_name_prefix="",
    blob_constructor_kwargs=None,
    *,
    additional_blob_attributes=None,
):
    """Upload many files concurrently by their filenames.

    The destination blobs are automatically created, with blob names based on
    the source filenames and the blob_name_prefix.

    For example, if the `filenames` include "images/icon.jpg",
    `source_directory` is "/home/myuser/", and `blob_name_prefix` is "myfiles/",
    then the file at "/home/myuser/images/icon.jpg" will be uploaded to a blob
    named "myfiles/images/icon.jpg".

    :type bucket: :class:`google.cloud.storage.bucket.Bucket`
    :param bucket:
        The bucket which will contain the uploaded blobs.

    :type filenames: list(str)
    :param filenames:
        A list of filenames to be uploaded. This may include part of the path.
        The file will be accessed at the full path of `source_directory` +
        `filename`.

    :type source_directory: str
    :param source_directory:
        A string that will be prepended (with `os.path.join()`) to each filename
        in the input list, in order to find the source file for each blob.
        Unlike the filename itself, the source_directory does not affect the
        name of the uploaded blob.

        For instance, if the source_directory is "/tmp/img/" and a filename is
        "0001.jpg", with an empty blob_name_prefix, then the file uploaded will
        be "/tmp/img/0001.jpg" and the destination blob will be "0001.jpg".

        This parameter can be an empty string.

        Note that this parameter allows directory traversal (e.g. "/", "../")
        and is not intended for unsanitized end user input.

    :type blob_name_prefix: str
    :param blob_name_prefix:
        A string that will be prepended to each filename in the input list, in
        order to determine the name of the destination blob. Unlike the filename
        itself, the prefix string does not affect the location the library will
        look for the source data on the local filesystem.

        For instance, if the source_directory is "/tmp/img/", the
        blob_name_prefix is "myuser/mystuff-" and a filename is "0001.jpg" then
        the file uploaded will be "/tmp/img/0001.jpg" and the destination blob
        will be "myuser/mystuff-0001.jpg".

        The blob_name_prefix can be blank (an empty string).

    :type blob_constructor_kwargs: dict
    :param blob_constructor_kwargs:
        A dictionary of keyword arguments to pass to the blob constructor. Refer
        to the documentation for `blob.Blob()` for more information. The dict is
        directly passed into the constructor and is not validated by this
        function. `name` and `bucket` keyword arguments are reserved by this
        function and will result in an error if passed in here.

    :type additional_blob_attributes: dict
    :param additional_blob_attributes:
        A dictionary of blob attribute names and values. This allows the
        configuration of blobs beyond what is possible with
        blob_constructor_kwargs. For instance, {"cache_control": "no-cache"}
        would set the cache_control attribute of each blob to "no-cache".

        As with blob_constructor_kwargs, this affects the creation of every
        blob identically. To fine-tune each blob individually, use `upload_many`
        and create the blobs as desired before passing them in.

    :rtype: list
    :returns: A list of results corresponding to, in order, each item in the
        input list. If an exception was received, it will be the result
        for that operation. Otherwise, the return value from the successful
        upload method is used (which will be None).
    """

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

def storage_client_gc():

    # GOOGLE_APPLICATION_CREDENTIALS is added to secrets in fly.io which are loaded
    # as environment variables in the fly-machine at runtime. The environment variable 
    # needs convertion to json format as its saved as string in fly.io secret.
    # This method of loading environment variables does apply outside 
    # fly.io hence the try/except.
    try:
        gc_env = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        creds = json.loads(gc_env)
        credentials = service_account.Credentials.from_service_account_info(
        creds)
    except (KeyError, ValueError):
        logger.info('Loading credentials (Google service account) from JSON failed - will try default method from environment')
        storage_client = storage.Client(project=PROJECT)
    else:
        storage_client = storage.Client(project=PROJECT, credentials=credentials)
    
    return storage_client


def upload_many_blobs_from_stream_with_transfer_manager(
    bucket_name, files, storaqge_client, workers=8,
):
    """Upload every file in a list to a bucket, concurrently in a process pool.

    Each blob name is derived from the filename. For complete control of the blob name for each
    file (and other aspects of individual blob metadata), use
    transfer_manager.upload_many() instead.
    """
    
    bucket = storage_client.bucket(bucket_name)

    results = upload_many_from_files(
        bucket, files
    )

    for file, result in zip(files, results):
    #    # The results list is either `None` or an exception for each filename in
    #    # the input list, in order.
        if isinstance(result, Exception):
            logger.info(f"Failed to upload {file.filename} due to exception: {result}")
        else:
            logger.info(f"Uploaded {file.filename} to {bucket.name}.")

def upload_blob(bucket_name, file_obj, destination_folder_name, destination_file_name, storage_client):
    """Uploads a file to the bucket."""
    # Create the full GCS path (including the folder and file name)
    gcs_file_path = os.path.join(destination_folder_name, destination_file_name)

    # Check if the file already exists in GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_file_path)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    blob.upload_from_file(file_obj, rewind=True)

    logger.info(
        f"File {destination_file_name} uploaded to {destination_folder_name}."
    )

def download_blob(bucket_name, source_blob_name, destination_file_name, storage_client):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"


    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    logger.info(
        "Downloaded storage object {} from bucket {} to local file {}.".format(
            source_blob_name, bucket_name, destination_file_name
        )
    )

def gc_is_file(bucket_name, source_blob_name, storage_client):

    bucket = storage_client.bucket(bucket_name)

    return storage.Blob(bucket=bucket, name=source_blob_name).exists(storage_client)

def gc_list_files_folders(bucket_name, prefix, storage_client, delimiter=None):

    bucket = storage_client.bucket(bucket_name)
    
    blobs = bucket.list_blobs(prefix=prefix, delimiter=delimiter)
    files = []
    folders = []
    for blob in blobs:
        files.append(blob.name)
    if delimiter:
        for pre in blobs.prefixes:
            folders.append(pre)

    return files, folders

def get_latest_file_in_folder(bucket_name, folder_path, storage_client, file_extension=None, name_only=True):

    # Initialize a Google Cloud Storage client

    folder_path = f"{folder_path}/"
    # Get the bucket
    bucket = storage_client.get_bucket(bucket_name)
    if file_extension:
        logger.info(f"Checking for latest {file_extension} file in: {folder_path} from bucket: {bucket_name}")
    else:
        logger.info(f"Checking for latest file in: {folder_path} from bucket: {bucket_name}")

    # List all the blobs (files) in the folder
    blobs = bucket.list_blobs(prefix=folder_path)

    # Initialize variables to store the latest file
    latest_blob = None
    latest_time = None

    # Iterate through the blobs
    # Filter files by the specific extension and store them along with their updated timestamps
    if file_extension:
        files = [(blob.name, blob.updated) for blob in blobs if blob.name.endswith(file_extension)]
    else:
        files = [(blob.name, blob.updated) for blob in blobs]

    # Sort the files by their updated timestamp, and retrieve the latest one
    if files:
        latest_file = max(files, key=lambda x: x[1])

        logger.info(f"Latest file: {latest_file[0]}, Last updated: {latest_file[1]}")
        latest_file = Path(latest_file[0])
        if name_only:
            return latest_file.name
        else:
            return Path(latest_file[0])
    else:
        return None


def gc_list_dirs(bucket_name, path, storage_client):
    if path[-1] != '/':
        path += '/'
    files, folders = gc_list_files_folders(bucket_name=bucket_name, prefix=path, storage_client=storage_client, delimiter='/')
    clean = []
    if len(folders) > 0:
        for dir in folders:
            clean.append(dir.split(path)[-1])
    return clean
        
def main():

    logger.info("Hello World!")
  # Example usage
    bucket_name = 'data_labear'
    folder_path = 'users/g28/'  # Don't forget the trailing '/'
    file_type = ".pt"
    client = storage_client_gc()
    latest_file = get_latest_file_in_folder(bucket_name, folder_path, client, file_extension=file_type)
    logger.info(latest_file)
if __name__ == "__main__":
    main()