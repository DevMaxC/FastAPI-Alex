from fastapi import FastAPI, UploadFile, File
import io
import wave
from pydantic import BaseModel
import base64
import os
import openai
import requests
import requests

CHUNK_SIZE = 1024
url = "https://api.elevenlabs.io/v1/text-to-speech/q9tuMLqYtfvnRwpnCxhr"

xKey = os.getenv("XI_API_KEY")
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": xKey,
}

data = {
    "text": "Hi! My name is Bella, nice to meet you!",
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0,
        "similarity_boost": 0
    }
}

response = requests.post(url, json=data, headers=headers)

openai.api_key = os.getenv("OPENAI_API_KEY")

print(os.getenv("OPENAI_API_KEY"))
app = FastAPI()


class ButtonData(BaseModel):
    audio_data: str
    is_end: bool
    is_first: bool


@app.get("/")
async def root():
    # if there is no file in the directory called "output.mp3", respond with a message saying that there is no file
    # if there is a file in the directory called "output.mp3", respond with the file in base64 format

    if os.path.isfile("output.mp3"):
        with open("output.mp3", "rb") as f:
            encoded_audio = base64.b64encode(f.read())
            return {encoded_audio}
    else:
        return {"No file found"}


@app.post("/")
async def handle_button_data(data: ButtonData):
    # see if there is a audio.txt file
    # if there is, append the data to the file
    # if there isn't, create the file and write the data to it
    with open("audio.txt", "a") as f:
        f.write(data.audio_data)

        if data.is_first:
            # delete all files
            if os.path.isfile("audio.txt"):
                os.remove("audio.txt")
            if os.path.isfile("audio.wav"):
                os.remove("audio.wav")
            if os.path.isfile("output.mp3"):
                os.remove("output.mp3")

        if data.is_end:
            # convert the audio.txt file to a wav file
            # open file
            with open("audio.txt", "r") as f:
                decoded_audio_data = base64.b64decode(f.read())

            with wave.open("audio.wav", "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(16000)
                f.writeframes(decoded_audio_data)

            audio_file = open("audio.wav", "rb")
            print("sending to openai...")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

            print(transcript)

            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are marvin, an incredibly depressed - yet smart robot assistant. You respond with sarky comments and witty remarks. And often insult the user.",
                     "role": "user", "content": transcript.text
                     }
                ]
            )

            final = completion.choices[0].get("message").get("content")
            print(final)

            filesize = f.getnframes() * f.getsampwidth()
            duration = filesize / 16000 / 2

            with open("audio.txt", "w") as f:
                f.write("")

            return {"message": final}
        else:
            return {"message": "Data received"}
