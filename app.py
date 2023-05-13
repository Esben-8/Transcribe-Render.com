from flask import Flask, request, jsonify
from pytube import YouTube
import openai
import tempfile
import os
import traceback
import logging
from pydub import AudioSegment

app = Flask(__name__)
app.config['DEBUG'] = True

# configure the logging module to write messages to a file
logging.basicConfig(filename='debug.log', level=logging.DEBUG)

@app.route("/")
def hello():
    print("hej")
    print("med")
    return "Hello, !"

@app.route("/transcribe", methods=["GET"])
def transcribe():
#     try:
    video_id = str(request.args.get("id"))
    url = f"https://www.youtube.com/watch?v={video_id}"
    # print(url)
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
        result = {"Message": "Empty"}
        
        with open(os.path.join(temp_path, "temp_audio.mp4"), "rb") as audio_file:
            # Get the file size in bytes
            file_size = os.fstat(audio_file.fileno()).st_size
            print(f"The file size is {file_size} bytes.")
            
            # Split the audio file into smaller chunks
            audio = AudioSegment.from_file(audio_file, format="mp4")
            chunk_size = 10 * 60 * 1000
            chunks = audio[:chunk_size]

            transcriptions = []
            for i, chunk in enumerate(chunks):
                print(f"Transcribing chunk {i + 1}/{len(chunks)}")
                with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_chunk_file:
                    chunk.export(temp_chunk_file.name, format="mp4")
                    temp_chunk_file.seek(0)

                    # Transcribe the chunk using the OpenAI whisper API
                    print("Transcribing")
                    transcription = openai.Audio.transcribe("whisper-1", temp_chunk_file)
                    transcriptions.append(transcription["text"])

            result = {
                "script": " ".join(transcriptions),
                "length": yt.length,
                "title": yt.title,
                "views": yt.views,
                "description": yt.description
            }

        return jsonify(result)
    else:
        print(f"Video is longer than {int(round(max_length/60, 0))} minutes")
        return {"Too long": f"Video is longer than {int(round(max_length/60, 0))} minutes"}

    os.remove(os.path.join(temp_path, "temp_audio.mp4"))

#     except Exception as error:
#         print(error)
#         return jsonify({"Too long": str(error)})
