# VOD Chat Activity Analyzer

![screenshot](https://i.imgur.com/7ElycXy.png)

## Project Overview

VOD Chat Activity Analyzer, is a web application designed to provide an interactive visualization of activity within a Twitch and YouTube stream's chat. It allows users to track the pace and volume of messages in a VOD's chat over time. 

The visualizations are particularly useful for streamers who want to understand when their chats are most active. It can help to identify key moments during a stream when viewer engagement is high. This information may help to choose moments for a video highlights, etc.

## Features

- **VOD Chat Download**: The application downloads chat history from Twitch/YouTube VODs using the URL provided by the user.
- **Interactive Visualization**: The application generates an interactive graphs that plots the number of chat messages/emoticons over time. The X-axis represents time in minutes since the start of the VOD, and the Y-axis represents the metric. 
- **Rolling Averages**: The line graph displays rolling averages of chat activity for three different time intervals: 15 seconds, 60 seconds, and 5 minutes. This allows users to observe chat activity trends at different granularity.

## Usage

### Local Setup

First, clone this repository to your local machine.

Then try to use Docker Compose to start the web-application:

```shell
git clone <repo URL>
cp compose.override-example.yaml compose.override.yaml
cp .env.example .env
docker compose up -d
```

If you don't have the Docker Engine, then you can run the project via a local Python:

1. Install the [`virtualenv`](https://virtualenv.pypa.io/en/latest/user_guide.html) package to isolate the project dependencies: `pip install virtualenv`
2. Init the virtual environment: `python -m virtualenv venv`
3. Activate the virtual environment: `.\venv\Scripts\activate`
4. Install the dependencies: `pip install -r requirements.txt`
5. Start the web-server: `python web_app.py`
6. Start the tasks server: `luigid --pidfile ./data/luigid.pid --logdir ./data/`
7. Visit http://localhost:8080 in your web browser to view the application.

### User Guide

1. On the homepage, enter the URL of a Twitch/YouTube VOD whose chat activity you want to analyze.
2. Click the "Analyze chats" button. The application will start downloading the chat history and processing it.
3. Once the data processing is done, you will see a plot and other widgets. You can hover over the graph to see the exact stats at any given time point.
4. You can click the button to show a video player, then Shift+Click on the graph to navigate the video to this time.

## Known Limitations

1. The bundled EXE file `chat-analyzer.exe` is not signed, so Microsoft Defender SmartScreen will always warn you about an unrecognized app.

## Technology Stack

- **Language**: Python 3.11
- **Web Framework**: Flask 2.3
- **Chat Data Fetching**: chat-downloader with patches
- **Data Processing**: pandas 2.0
- **Visualization**: Plotly 5.15

## Bundle Windows EXE

If the contents of the `chat-analyzer.spec` file are up-to-date, it is sufficient to use a Compose `bundler` service to build the `chat-analyzer.exe` file:

    docker compose run --rm bundler

Otherwise, you need a Windows machine to sync the spec file.  First of all, install Python and PyInstaller locally.  Then install the application dependencies:

    pip install -r requirements.txt

Then run the command to update the spec file:

    pyinstaller --name chat-analyzer --onefile --collect-datas chat_downloader.formatting --add-data "flask_app/templates:flask_app/templates" --add-data "flask_app/static:flask_app/static" standalone_app.py

(Optional) If you have changed the application dependencies, it's better to rebuild the `bundler` image to speed up the bundling.
