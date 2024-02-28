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

Now install colima:

Do `brew install colima`

Once installed verify its working by running `docker info` build -t api-app .     

Next navigate to the api folder and run:

`docker build -t api-app .`

This should build the docker image. 

Next run the image by running:

`docker run -p 8000:8000 api-app`   

Check that the api responds by next running `python /labear_api/test_api_submit.py`

## Fly.io

For now our chosen cloude service is Fly.io and we deploy the api-app on this service using the Docker container.
For the detials check out [Fly.io](https://fly.io/docs/)

Fly.io needs to be installed first by running:

`brew install flyctl`

You will need to sign up and sign in to use Fly.io  - follow the link to do this (https://fly.io/docs/hands-on/sign-up/). 


Next, you should be ready to launch the app (requires a functioning docker image - see above), navigate to the labear_api folder which contains the docker file.

`fly launch`

The  `fly.toml` file this will be used for the launch configuration. 

Once launched the app shoul be running at: https://albinai.fly.dev. Upon opedning the webpage you should see the
following `{"message":"Hello World"}`

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

