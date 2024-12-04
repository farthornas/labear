# Labear API

The backend service to do the things 

## Getting started 

Make sure you [have poetry installed](https://python-poetry.org/docs/#installation)

Do `poetry install` to set up the virtual environment and install dependencies 

Do `poetry run start` to start up the API 

## Docker

Make sure you have Docker installed. I installed Docker using Homebrew. I had to install `colima` [https://github.com/abiosoft/colima/blob/main/README.md] to be able to use Docker on my Macbook. 


Do `brew install docker`

Do `brew install docker-buildx`

For Docker to find the buildx component which is required to use Docker buildkit the following lines 
should be added to your Docker config.json file (mine was at ~/.docker/config.json)

  "cliPluginsExtraDirs": [
      "/opt/homebrew/lib/docker/cli-plugins"
  ]



Now install colima:

Do `brew install colima`

Once installed verify its working by running `docker info` build -t api-app .     

Next navigate to the api folder and run:

`DOCKER_BUILDKIT=1 docker build -t api_app .`

This should build the docker image. 

Next run the image by running:

`docker run -p 8000:8000 api-app`

Alternatively if you want to test the build with google cloud access  (this is required if @app.post(LEARN) is used) you will need to aquire a service account key. Once the account key is obtained, download and place in the appropriate folder (`/app/.config/gcloud/application_default_credentials.json` in this example). Then run: 

`docker run -e GOOGLE_APPLICATION_CREDENTIALS="/app/.config/gcloud/application_default_credentials.json" --mount type=bind,source=${HOME}/.config/gcloud,target=/app/.config/gcloud -p 8000:8000 api-app`



Check that the api responds by next running `python /labear_api/test_api_submit.py`

## Fly.io

UPDATE 04.12.2024: The fly.io instance has been temporary shut down for security purposes prior to making this repository public. As soon as some authetication is implemented the instance will be launched again.

For now our chosen cloude service is Fly.io and we deploy the api-app on this service using the Docker container.
For the detials check out [Fly.io](https://fly.io/docs/)

Fly.io needs to be installed first by running:

`brew install flyctl`

You will need to sign up and sign in to use Fly.io  - follow the link to do this (https://fly.io/docs/hands-on/sign-up/).

If fly.io is installed, you can log into the instance by doing:

`flyctl auth login --email <email_string> --password <password>`

Check if the app is already running by doing:


`flyctl status -a albinai` 

If it is running, skip the `fly launch` bit

If app is not running, you should be ready to launch the app (requires a functioning docker image - see above), navigate to the labear_api folder which contains the docker file.

`fly launch`

The  `fly.toml` file this will be used for the launch configuration. 

If updates to the image is needed (say from updating the code base) run:

`fly deploy`

Once launched the app should be running at: https://albinai.fly.dev. Upon opening the webpage you should be 
redirected to the docs openapi docs page.  

To test to check if the service is running as it should navigate to labear_api and run:

`poetry run python test_api_submit.py`

This will send a .wav to the api running at https://albinai.fly.dev and you should get the response:
 
 `{'Payload': {'user_id': '1234', 'class_id': 11, 'time_stamp': 12345, 'files_size': [1318912], 'Filenames': ['test_submit.wav']}}`

 You can check what apps are running (this requires you to have started the service (- I presume?)) by doing:

 `flyctl apps list`

 To check the status of the machines the app is running on do:
 
 `flyctl machine -a albinai list`

 For more information checkout the Fly.io docs @ (https://fly.io/docs/)

For more details on launching a docker image check out: https://fly.io/docs/languages-and-frameworks/dockerfile/

## Google Cloud 

Google cloud should/is now used to store training data.
The data is kept in a bucket on cloud storage:  

`data_labear`

To access the bucket the fly.io instance will need to have the appropiate premissions. 
This can be obtained with a service account key for the project on google cloud services. Once the account key is obtained, it can be downloaded and placed in the appropriate folder eg. `/app/.config/gcloud/application_default_credentials.json` 

The service account key will then need to be added to  fly.io secrets. This can be done by doing:

`flyctl secrets set GOOGLE_APPLICATION_CREDENTIALS=- < application_default_credentials.json`

To check it has been added appropriatly run:

`flyctl secrets list -a albinai`

GOOGLE_APPLICATION_CREDENTIALS is added to secrets in fly.io which are loaded
as environment variables in the fly-machine at runtime. The environment variable 
needs convertion to json format as its saved as string in fly.io secret.
This method of loading environment variables does apply outside 
fly.io hence the try/except.

The files to be uploaded are kept as file-like-objects and uploaded to
the ID of the chosen GCS bucket:

bucket_name = "your-bucket-name"

the files should be in a list (or other iterable) of files to upload:

filenames = ["file_1.txt", "file_2.txt"]

Uploading the files can be done by using `process` or `threads` - we use 
threads as the files are generally small in which case threads are more efficient.

We also set the number of processes/threads to use in the upload. 

The performance impact of this value depends on the use case, but smaller files usually
benefit from a higher number of threads.

## Preparing, training and running finetuned models in the API.

Running finetuned models in the API (fly.io) is still very much in development. 

To train a new model data can be fetched from GCS where the raw data for training a model is located.
For instance, the `engine` training data with raw recordings from two idling car engines + just silence is located under: [`data_labear/users/engine/data/raw/`]

Once the raw data is downloaded it will need some preprocessing. The [`train.ipynb`] notebook has code to split up and put in designated folders. 

Once the preprocessed data is ready the notebook [`train.ipynb`] can be executed and should produce a finetuned model. The model will be saved as [user]_[tag].pt
The model will be accopanied by the classification categories for the model in [user]_cats.json.

The .pt and .json file should then be uploaded to [data_labear/users/[user]/] on google cloud services. Which can also be done from the notbook [`train.ipynb`].

The new model will be automatically downloaded and loaded into memory for specific user when the api is next rebooted [`fly machine restart`]. This will obviously be changed in the near future. 







