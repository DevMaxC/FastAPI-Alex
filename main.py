from fastapi import FastAPI, UploadFile, File
import io
import wave
from pydantic import BaseModel


app = FastAPI()


class ButtonData(BaseModel):
    button_pressed: bool


@app.post("/")
async def handle_button_data(data: ButtonData):
    if data.button_pressed:
        # You can customize the response based on your application logic
        led = "green"
        return led
    return "No action"
