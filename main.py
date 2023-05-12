from fastapi import FastAPI, UploadFile, File
import io
import wave
from pydantic import BaseModel

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
            with open("audio.txt", "r") as f:
                audio_data = f.read()
                audio_data = audio_data.split(",")
                audio_data = [int(i) for i in audio_data]
                audio_data = bytes(audio_data)
                with wave.open("audio.wav", "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(audio_data)
                    duration = wav_file.getnframes() / float(wav_file.getframerate())
            # send the wav file to the speech to text api
            # return the audio length in seconds: Datalength: n seconds
            # delete the audio.txt file
            with open("audio.txt", "w") as f:
                f.write("")

            return {"message": "Datalength: " + str(duration) + " seconds"}
        else:
            return {"message": "Data received"}

# delete the audio.txt file
