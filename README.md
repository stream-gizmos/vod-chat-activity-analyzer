# VOD Chat Activity Analyzer

<a href="https://ibb.co/Ch5gz26"><img src="https://i.ibb.co/syvn2HC/Screenshot-8.png" alt="Screenshot-8" border="0" width="100%"></a>

## Table of Contents
- [Project Overview](#Project-Overview)
- [Features](#features)
- [Live Deployment](#live-deployment)
- [Usage](#usage)
- [Known Limitations](#known-limitations)
- [Technology Stack](#tech-stack)
- [Future](#future)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)


## Project Overview

Twitch Chat Activity Visualizer, is a web application designed to provide an interactive visualization of activity within a Twitch stream's chat. It allows users to track the pace and volume of messages in a Twitch VOD's chat over time. 

The visualizations are particularly useful for streamers who want to understand when their chats are most active. It can help to identify key moments during a stream when viewer engagement is high.

The application is built using Python and Flask, and leverages the chat_downloader library to fetch chat data from Twitch VODs. The visualization itself is created using Plotly and rendered in a web browser.

## Features

- **Twitch VOD Chat Download**: The application downloads chat history from Twitch VODs using the URL provided by the user. It can handle streams of various sizes, from smaller streams to medium-large streams but not very large streams due to reasons mentioned in the Known Limitations section below.
- **Interactive Visualization**: The application generates an interactive line graph that plots the number of chat messages over time. The X-axis represents time in minutes since the start of the VOD, and the Y-axis represents the number of messages. 
- **Rolling Averages**: The line graph displays rolling averages of chat activity for three different time intervals: 15 seconds, 60 seconds, and 5 minutes. This allows users to observe chat activity trends at different granularities.

## Usage

### Local Setup

1. Clone this repository to your local machine.
2. Install the required Python packages listed in `requirements.txt`. It's recommended to do this in a virtual environment.
3. Run `flask_app.py` to start the Flask server.
4. Visit `localhost:5000` in your web browser to view the application.

### Bundle Windows EXE

(Optional) You need to install Python and PyInstaller locally on a Windows machine. Then run the command to update the `app.spec` file:

    pyinstaller -F --add-data "flask_app/templates:flask_app/templates" --add-data "flask_app/static:flask_app/static" app.py

Then you can use a Compose service `bundler` to build an `app.exe` file:

    docker compose run --rm bundler

(Optional) If you have changed the `requirements.txt` content, it's better to rebuild the `bundler` image to speed up the bundling.

### User Guide

1. On the homepage, enter the URL of the Twitch VOD whose chat activity you want to analyze.
2. Click the "Find how fast your chat was!" button. The application will start downloading the chat history and processing it.
3. Once the data processing is done, you will be redirected to a page that displays the visualization of the chat activity. You can hover over the graph to see the exact number of messages at any given time point.

## Known Limitations

Due to the limitations of Heroku's 30-second timeout for requests, this application may not be able to handle extremely active Twitch chats that have thousands of messages per minute. In such cases, the application might timeout before it finishes downloading and processing the chat data. This issue is primarily observed with larger streams that have high chat activity. I am actively exploring solutions to address this limitation in future versions of the application.

## Technology Stack

- **Language**: Python 3.11
- **Web Framework**: Flask 2.3
- **Chat Data Fetching**: chat-downloader
- **Data Processing**: pandas 2.0
- **Visualization**: Plotly 5.15

## Future Work

In future versions of this project, we aim to add more detailed analysis features. These might include:

- **Peak Activity Identification**: Automatically identifying and highlighting moments in the stream with the highest chat activity.
- **User Participation Statistics**: Showing statistics on individual users' participation in the chat.
- **Keyword Analysis**: Identifying the most frequently used words or phrases in the chat.
