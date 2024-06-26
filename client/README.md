# Running the KIVY app on your machine

This is what will become the iOS and Android app

## Getting started 

Make sure you [have poetry installed](https://python-poetry.org/docs/#installation)

Do `poetry install` to set up the virtual environment and install dependencies.

## !! Running the App on a computer is no longer supported. !!

For the app to not crash when uploading the recordings, the API needs to be running. To run the API have a look at the API README.

Once the API is running:

Do `poetry run python kivy/AudioMon.py` to start up the application

## Running the App on Android 

To build a package for Android a automated builder called Buildozer is used. First 
install Buildozer by following the instructions here: 

`https://buildozer.readthedocs.io/en/latest/installation.html`

Where a step in the install or requirements requires [pip], use [poetry] instead.

Getting the installation to work required some efforts (java in particular gave me some grief).


First time running buildozer requires you to run: 

`poetry run buildozer init`

This will create the [buildozer.spec] file in which we can set configuratations for the builder. 

Buildozer requires there to be a main.py file in the same directory as the [buildozer.spec] file.

The [buildozer.spec] file needs to include python libraries (kivy) etc to be able to build the application. 

These additions can be added in: 

    # (list) Application requirements
    # comma separated e.g. requirements = sqlite3,kivy
    requirements = python3,pyjnius,kivy,kivymd,requests,plyer

Another important sections is `Permissions` as these are required to access microphone etc. Look at this projects [buildozer.spec] 
for an example of how to define permissions. 


Any changes or updates to the app needs to be built and packaged before being served to a phone. 

`poetry run buildozer -v android debug deploy run logcat`

Debugging is essential to troubleshoot the app - you will need a USB cable to connect to your phone for this.
You also need to put your phone in developer mode to allow the app to be served and debugged. Instructions for 
doing this is easy to find online. 







