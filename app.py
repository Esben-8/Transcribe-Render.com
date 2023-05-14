from flask import Flask, request, jsonify
import redis
import uuid
import requests
import json
import time
import openai
import tempfile
import pytube
import os

app = Flask(__name__)


# Set up a route for video transcription request
@app.route('/transcribe', methods=['POST'])
def transcribe_video():
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Get video URL from the request
    video_url = request.form['video_url']
    max_length = request.form["max_length"]
    api_key = request.form["api_key"]
    
    # Create temp path
    temp_path = tempfile.gettempdir()

    # Download the video from the URL
    youtube = pytube.YouTube(video_url)
    youtube.streams.filter(only_audio=True, file_extension="mp4").first().download(output_path=temp_path, filename="temp_audio.mp4")

    # Transcribe the video using OpenAI API
    with open(os.path.join(temp_path, "temp_audio.mp4"), "rb") as audio_file:
        transcription = openai.Audio.transcribe("whisper-1", audio_file, api_key
    
    # Respond to user with job ID and message
    return jsonify({'job_id': job_id, 'message': 'Transcription job is being processed.', data: transcription["text"]})
        

if __name__ == '__main__':
    app.run()
