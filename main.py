from fastapi import FastAPI, UploadFile, File
import io
import wave
from pydantic import BaseModel

app = FastAPI()


class ButtonData(BaseModel):
    audio_data: str


@app.post("/")
async def handle_button_data(data: ButtonData):
    # see if there is a audio.txt file
    # if there is, append the data to the file
    # if there isn't, create the file and write the data to it
    with open("audio.txt", "a") as f:
        f.write(data.audio_data)
    return {"message": "Data received"}

# delete the audio.txt file


@app.delete("/")
async def delete_audio():
    with open("audio.txt", "w") as f:
        f.write("")
    return {"message": "Data deleted"}
