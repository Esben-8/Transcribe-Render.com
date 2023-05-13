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

# Connect to Upstash Redis endpoint
r = redis.Redis(host='eu1-boss-goblin-39389.upstash.io', port=39389, password="aad265ed603b471fa7346db6e5f27066")

# Set up a route for video transcription request
@app.route('/transcribe', methods=['POST'])
def transcribe_video():
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Get video URL from the request
    video_url = request.form['video_url']
    max_length = request.form["max_length"]
    api_key = request.form["api_key"]
    
    # Push job ID and video URL to Upstash QStash queue
    r.lpush('qstash:transcription_jobs', json.dumps({'job_id': job_id, 'video_url': video_url, "max_length": max_length, "api_key": api_key}))
    
    # Respond to user with job ID and message
    return jsonify({'job_id': job_id, 'message': 'Transcription job is being processed.'})

# Set up a route for job status request
@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    # Get job status from the database
    job_status = r.get('job:{}:status'.format(job_id))
    
    if job_status is None:
        return jsonify({'message': 'Job not found.'}), 404
    
    # Respond to user with job status
    return jsonify({'job_id': job_id, 'status': job_status.decode('utf-8')})

# Set up a background worker to transcribe videos
def transcribe_worker():
    while True:
        # Pop job ID and video URL from Upstash QStash queue
        job_info = r.brpop('qstash:transcription_jobs', timeout=0)
        
        if job_info is not None:
            # Extract job ID and video URL from job info
            job_id = json.loads(job_info[1])['job_id']
            video_url = json.loads(job_info[1])['video_url']
            api_key = json.loads(job_info[1])["api_key"]
            
            # Update job status to 'in progress'
            r.set('job:{}:status'.format(job_id), 'in progress')
            
            # Create temp path
            temp_path = tempfile.gettempdir()

            # Download the video from the URL
            youtube = pytube.YouTube(video_url)
            youtube.streams.filter(only_audio=True, file_extension="mp4").first().download(output_path=temp_path, filename="temp_audio.mp4")
            
            # Transcribe the video using OpenAI API
            with open(os.path.join(temp_path, "temp_audio.mp4"), "rb") as audio_file:
                transcription = openai.Audio.transcribe("whisper-1", audio_file, api_key)
            
            # Store the transcription in the database
            r.set('job:{}:transcription'.format(job_id), transcription["text"])
            
            # Update job status to 'completed'
            r.set('job:{}:status'.format(job_id), 'completed')
        
        time.sleep(1)

# Start the worker as a separate thread
import threading
worker_thread = threading.Thread(target=transcribe_worker)
worker_thread.start()

if __name__ == '__main__':
    app.run()
