from google.cloud import storage
from google.cloud.storage import transfer_manager
from google.oauth2 import service_account
import os
import json
from json.decoder import JSONDecodeError

PROJECT = 'labear'

def upload_many_from_files(
    bucket,
    files,
    source_directory="",
    blob_name_prefix="",
    skip_if_exists=False,
    blob_constructor_kwargs=None,
    upload_kwargs=None,
    threads=None,
    deadline=None,
    raise_exception=False,
    worker_type="thread",
    max_workers=8,
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

    :type skip_if_exists: bool
    :param skip_if_exists:
        If True, blobs that already have a live version will not be overwritten.
        This is accomplished by setting `if_generation_match = 0` on uploads.
        Uploads so skipped will result in a 412 Precondition Failed response
        code, which will be included in the return value, but not raised
        as an exception regardless of the value of raise_exception.

    :type blob_constructor_kwargs: dict
    :param blob_constructor_kwargs:
        A dictionary of keyword arguments to pass to the blob constructor. Refer
        to the documentation for `blob.Blob()` for more information. The dict is
        directly passed into the constructor and is not validated by this
        function. `name` and `bucket` keyword arguments are reserved by this
        function and will result in an error if passed in here.

    :type upload_kwargs: dict
    :param upload_kwargs:
        A dictionary of keyword arguments to pass to the upload method. Refer
        to the documentation for `blob.upload_from_file()` or
        `blob.upload_from_filename()` for more information. The dict is directly
        passed into the upload methods and is not validated by this function.

    :type threads: int
    :param threads:
        ***DEPRECATED*** Sets `worker_type` to THREAD and `max_workers` to the
        number specified. If `worker_type` or `max_workers` are set explicitly,
        this parameter should be set to None. Please use `worker_type` and
        `max_workers` instead of this parameter.

    :type deadline: int
    :param deadline:
        The number of seconds to wait for all threads to resolve. If the
        deadline is reached, all threads will be terminated regardless of their
        progress and `concurrent.futures.TimeoutError` will be raised. This can
        be left as the default of `None` (no deadline) for most use cases.

    :type raise_exception: bool
    :param raise_exception:
        If True, instead of adding exceptions to the list of return values,
        instead they will be raised. Note that encountering an exception on one
        operation will not prevent other operations from starting. Exceptions
        are only processed and potentially raised after all operations are
        complete in success or failure.

        If skip_if_exists is True, 412 Precondition Failed responses are
        considered part of normal operation and are not raised as an exception.

    :type worker_type: str
    :param worker_type:
        The worker type to use; one of `google.cloud.storage.transfer_manager.PROCESS`
        or `google.cloud.storage.transfer_manager.THREAD`.

        Although the exact performance impact depends on the use case, in most
        situations the PROCESS worker type will use more system resources (both
        memory and CPU) and result in faster operations than THREAD workers.

        Because the subprocesses of the PROCESS worker type can't access memory
        from the main process, Client objects have to be serialized and then
        recreated in each subprocess. The serialization of the Client object
        for use in subprocesses is an approximation and may not capture every
        detail of the Client object, especially if the Client was modified after
        its initial creation or if `Client._http` was modified in any way.

        THREAD worker types are observed to be relatively efficient for
        operations with many small files, but not for operations with large
        files. PROCESS workers are recommended for large file operations.

    :type max_workers: int
    :param max_workers:
        The maximum number of workers to create to handle the workload.

        With PROCESS workers, a larger number of workers will consume more
        system resources (memory and CPU) at once.

        How many workers is optimal depends heavily on the specific use case,
        and the default is a conservative number that should work okay in most
        cases without consuming excessive resources.

    :type additional_blob_attributes: dict
    :param additional_blob_attributes:
        A dictionary of blob attribute names and values. This allows the
        configuration of blobs beyond what is possible with
        blob_constructor_kwargs. For instance, {"cache_control": "no-cache"}
        would set the cache_control attribute of each blob to "no-cache".

        As with blob_constructor_kwargs, this affects the creation of every
        blob identically. To fine-tune each blob individually, use `upload_many`
        and create the blobs as desired before passing them in.

    :raises: :exc:`concurrent.futures.TimeoutError` if deadline is exceeded.

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
        skip_if_exists=skip_if_exists,
        upload_kwargs=upload_kwargs,
        deadline=deadline,
        raise_exception=raise_exception,
        worker_type=worker_type,
        max_workers=max_workers,
    )


def upload_many_blobs_from_stream_with_transfer_manager(
    bucket_name, files, workers=8
):
    """Upload every file in a list to a bucket, concurrently in a process pool.

    Each blob name is derived from the filename. For complete control of the blob name for each
    file (and other aspects of individual blob metadata), use
    transfer_manager.upload_many() instead.
    """

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # A list (or other iterable) of files to upload.
    # filenames = ["file_1.txt", "file_2.txt"]

    # The maximum number of processes to use for the operation. The performance
    # impact of this value depends on the use case, but smaller files usually
    # benefit from a higher number of processes. Each additional process occupies
    # some CPU and memory resources until finished. Threads can be used instead
    # of processes by passing `worker_type=transfer_manager.THREAD`.
    # workers=8

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
        bucket, files, max_workers=workers
    )

    for file, result in zip(files, results):
    #    # The results list is either `None` or an exception for each filename in
    #    # the input list, in order.
        if isinstance(result, Exception):
            print("Failed to upload {} due to exception: {}".format(file.filename, result))
        else:
            print("Uploaded {} to {}.".format(file.filename, bucket.name))

def main():

    print("Hello World!")
    bucket_name = "data_labear"
    upload_blob(bucket_name=bucket_name, source_file_name='test_submit.wav', destination_blob_name='test_upload.wav')

if __name__ == "__main__":
    main()