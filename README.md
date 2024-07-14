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

1. Clone this repository to your local machine.
2. Install the required Python packages listed in `requirements.txt`. It's recommended to do this in a virtual environment.
3. Run `web_app.py` to start the Flask server.
4. Visit http://localhost:8080 in your web browser to view the application.

### User Guide

1. On the homepage, enter the URL of the Twitch VOD whose chat activity you want to analyze.
2. Click the "Find how fast your chat was!" button. The application will start downloading the chat history and processing it.
3. Once the data processing is done, you will be redirected to a page that displays the visualization of the chat activity. You can hover over the graph to see the exact number of messages at any given time point.

## Known Limitations

1. The application may not be able to handle extremely active Twitch chats that have thousands of messages per minute. In such cases, the application might timeout before it finishes downloading and processing the chat data. This issue is primarily observed with larger streams that have high chat activity.
2. The bundled EXE file `chat-analyzer.exe` is not signed, so Microsoft Defender SmartScreen will always warn you about an unrecognized app.

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
