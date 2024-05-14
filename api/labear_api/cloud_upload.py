from google.cloud import storage
from google.cloud.storage import transfer_manager
from google.oauth2 import service_account
import os
import json
from json.decoder import JSONDecodeError

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


def upload_many_blobs_from_stream_with_transfer_manager(
    bucket_name, files, workers=8
):
    """Upload every file in a list to a bucket, concurrently in a process pool.

    Each blob name is derived from the filename. For complete control of the blob name for each
    file (and other aspects of individual blob metadata), use
    transfer_manager.upload_many() instead.
    """

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
        print('Loading credentials (Google service account) from JSON failed - will try default method from environment')
        storage_client = storage.Client(project=PROJECT)
    else:
        storage_client = storage.Client(project=PROJECT, credentials=credentials)
    
    bucket = storage_client.bucket(bucket_name)

    results = upload_many_from_files(
        bucket, files
    )

    for file, result in zip(files, results):
    #    # The results list is either `None` or an exception for each filename in
    #    # the input list, in order.
        if isinstance(result, Exception):
            print(f"Failed to upload {file.name} due to exception: {result}")
        else:
            print(f"Uploaded {file.filename} to {bucket.name}.")

def main():

    print("Hello World!")
    bucket_name = "data_labear"
    upload_blob(bucket_name=bucket_name, source_file_name='test_submit.wav', destination_blob_name='test_upload.wav')

if __name__ == "__main__":
    main()