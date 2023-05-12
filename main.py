from fastapi import FastAPI, UploadFile, File
import io
import wave
from pydantic import BaseModel

app = FastAPI()


class ButtonData(BaseModel):
    audio_data: str


@app.post("/")
async def handle_button_data(data: ButtonData):
    try:
        audio_data = data.audio_data
        audio_file = io.BytesIO(audio_data)

    except Exception as e:
        return "Ok it didnt work in the fastapi - phase 1: " + str(e)

    # return how long the audio file is in seconds

    try:
        with wave.open(audio_file, 'rb') as audio:
            return audio.getnframes() / audio.getframerate()
    except Exception as e:

        return "Ok it didnt work in the fastapi -phase 2: " + str(e)
