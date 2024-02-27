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


Next, you should be ready to launch the app (requires a functioning docker image - see above): 

`fly launch`

For more details on launching a docker image check out: https://fly.io/docs/languages-and-frameworks/dockerfile/

