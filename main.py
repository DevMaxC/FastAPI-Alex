from fastapi import FastAPI, UploadFile, File
import io
import wave
from pydantic import BaseModel
import base64

app = FastAPI()


class ButtonData(BaseModel):
    audio_data: str
    is_end: bool


@app.post("/")
async def handle_button_data(data: ButtonData):
    # see if there is a audio.txt file
    # if there is, append the data to the file
    # if there isn't, create the file and write the data to it
    with open("audio.txt", "a") as f:
        f.write(data.audio_data)

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

            filesize = f.getnframes() * f.getsampwidth()
            duration = filesize / 16000 / 2

            with open("audio.txt", "w") as f:
                f.write("")

            return {"message": "Datalength: " + str(duration) + " seconds"}
        else:
            return {"message": "Data received"}
