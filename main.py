from fastapi import FastAPI, UploadFile, File
import io
import wave
from pydantic import BaseModel
import base64
import os
import openai
import requests
import requests
from starlette.responses import FileResponse
import json

systemSetVoiceID = "TxGEqnHWrfWFTfGW9XjX"
systemPrompt = "You are Marvin a depressed ai assistant, respond to the user with first a short an un called for insult, then reluctantly answer their question, then finish with a self depricating remark."

CHUNK_SIZE = 1024
url = "https://api.elevenlabs.io/v1/text-to-speech/"

xKey = os.getenv("XI_API_KEY")


openai.api_key = os.getenv("OPENAI_API_KEY")

print(os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# past conversations will be stored in a file called old_conversations.csv
# there will be the role and the content of the message
# the role will be either user or assistant
# the content will be the text of the message
#   only store the last 10 messages
#   if there are more than 10 messages, delete the oldest one
#   if there are less than 10 messages, add the new message to the end of the file
#   if there are no messages, add the new message to the end of the file


def getOldMessages():
    try:
        with open("old_conversations.csv", "r") as f:
            messages = f.readlines()
            messages = [x.strip() for x in messages]
            return messages
    except FileNotFoundError:
        return []


def addNewMessage(role, content):
    # if there are more than 9 messages, delete the oldest one
    messages = getOldMessages()
    if len(messages) > 9:
        messages = messages[1:]
    messages.append(role+","+content)
    with open("old_conversations.csv", "w") as f:
        for message in messages:
            f.write(message+"\n")


class ButtonData(BaseModel):
    audio_data: str
    is_end: bool
    is_first: bool


@app.get("/")
async def root():
    # if there is no file in the directory called "output.mp3", respond with a message saying that there is no file
    # if there is a file in the directory called "output.mp3", respond with the file in base64 format

    try:
        return FileResponse("output.mp3", media_type="audio/mpeg")
    except FileNotFoundError:
        return {"error": "File not found"}


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

            # get the last 10 messages
            oldmessages = getOldMessages()
            messages = []

            messages.append({"role": "system", "content": systemPrompt})

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": xKey,
                "voice_id": systemSetVoiceID
            }

            for message in oldmessages:
                role, content = message.split(",")
                messages.append({"role": role, "content": content})

            messages.append({"role": "user", "content": transcript.text})

            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            final = completion.choices[0].get("message").get("content")
            print(final)

            newz = {
                "text": final,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0,
                    "similarity_boost": 0
                }
            }

            response = requests.post(
                url+systemSetVoiceID, json=newz, headers=headers)
            with open('output.mp3', 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

            print("Success, the file should be available via a get request")

            return {"message": "Success, this is the transcript: "+final+" The file should be available via a get request to the same URL"}
        else:
            return {"message": "Data received"}
