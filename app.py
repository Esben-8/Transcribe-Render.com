from flask import Flask, request, jsonify
from pytube import YouTube
import openai
import tempfile
import os
import traceback
import logging
from flask_cors import CORS, cross_origin

app = Flask(__name__)

# Enable CORS for the specific domain
cors_config = {
    'origins': ['http://localhost:3000', 'https://contentchat.co']  # Replace with your front-end domain
}
CORS(app, **cors_config)

@app.route("/")
def hello():
    print("hej")
    print("med")
    return "Hello, !"

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/transcribe", methods=["GET"])
def transcribe():
    try:
        video_id = str(request.args.get("id"))
        url = f'https://youtube.com/watch?v={video_id}'
        print(url)
        max_length = int(request.args.get("max_length"))
        apikey = str(request.args.get("api_key"))
        print(apikey)

        openai.api_key = apikey
        temp_path = tempfile.gettempdir()
        yt = YouTube(url)

        print("Downloading")
        yt.streams.filter(only_audio=True, file_extension="mp4").first().download(output_path=temp_path, filename="temp_audio.mp4")

        print(yt.title)

        if yt.length < max_length:
            audio_file = open(os.path.join(temp_path, "temp_audio.mp4"), "rb")

            transcription = openai.Audio.transcribe("whisper-1", audio_file)

            audio_file.close()

            result = {
                "script": transcription["text"],
                "length": yt.length,
                "title": yt.title,
                "views": yt.views,
                "description": yt.description
            }

            return jsonify(result)
        else:
            return f"Video is longer than {int(round(max_length/60, 0))} minutes", 400

        os.remove(os.path.join(temp_path, "temp_audio.mp4"))

    except Exception as e:
        traceback.print_exc()
        return str(e), 500
