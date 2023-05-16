from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import io
import wave
import os
import openai
import requests
from starlette.responses import FileResponse
from pydantic import BaseModel
import base64

# Constants and configurations
global systemSetVoiceID
global systemPrompt
global oldMessages

oldMessages = []
systemSetVoiceID = "TxGEqnHWrfWFTfGW9XjX"
systemPrompt = "You are Marvin a depressed ai assistant, respond to the user with first a short an un called for insult, then reluctantly answer their question, then finish with a self depricating remark. Make sure to be boastful of your ai abilities."
CHUNK_SIZE = 1024
url = "https://api.elevenlabs.io/v1/text-to-speech/"
xKey = os.getenv("XI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI application
app = FastAPI()
origins = [
    "http://localhost:3000",
    "https://fastapi-production-9c49.up.railway.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Function for adding a new message to the old messages list

def addNewMessage(role, content):
    messages = oldMessages
    if len(messages) > 9:
        messages = messages[1:]
    messages.append({"role": role, "content": content})
    oldMessages = messages


# Route for fetching the generated audio file
@app.get("/")
async def root():
    print("Getting audio file")
    try:
        return FileResponse("output.mp3", media_type="application/octet-stream")
    except FileNotFoundError:
        return {"error": "File not found"}


# Pydantic model for button data
class ButtonData(BaseModel):
    audio_data: str
    is_end: bool
    is_first: bool


# Route for writing an audio chunk
@app.post("/")
async def writeAudioChunk(data: ButtonData):
    print("Writing audio chunk")
    with open("audio.txt", "a") as f:
        f.write(data.audio_data)

        if data.is_first:
            if os.path.isfile("audio.txt"):
                os.remove("audio.txt")
            if os.path.isfile("audio.wav"):
                os.remove("audio.wav")
            if os.path.isfile("output.mp3"):
                os.remove("output.mp3")

        if data.is_end:
            with open("audio.txt", "r") as f:
                decoded_audio_data = base64.b64decode(f.read())

            with wave.open("audio.wav", "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(16000)
                f.writeframes(decoded_audio_data)

            audio_file = open("audio.wav", "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)

            messages = []
            messages.append({"role": "system", "content": systemPrompt})

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": xKey,
                "voice_id": systemSetVoiceID
            }

            for m in oldMessages:
                messages.append(m)

            messages.append({"role": "user", "content": transcript.text})
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            final = completion.choices[0].get("message").get("content")

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

            return {"message": "Success, this is the transcript: "+final+" The file should be available via a get request to the same URL"}
        else:
            return {"message": "Data received"}


# Routes for managing voice and prompt
@app.get("/voice")
async def getVoice():
    print("Getting voice")
    return {"voice": systemSetVoiceID}


class VoiceData(BaseModel):
    voiceID: str


@app.post("/voice")
async def setVoice(data: VoiceData):
    print("Setting voice to "+data.voiceID)
    global systemSetVoiceID
    systemSetVoiceID = data.voiceID
    return {"voice": systemSetVoiceID}


@app.get("/prompt")
async def getPrompt():
    print("Getting prompt")
    return {"prompt": systemPrompt}


class PromptData(BaseModel):
    prompt: str


@app.post("/prompt")
async def setPrompt(data: PromptData):
    print("Setting prompt to "+data.prompt)
    global systemPrompt
    systemPrompt = data.prompt
    return {"prompt": systemPrompt}


@app.get("/oldmessages")
async def getOldMessagesRoute():
    print("Getting old messages")
    return oldMessages
