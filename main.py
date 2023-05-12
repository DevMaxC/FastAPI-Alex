from fastapi import FastAPI, UploadFile, File
import io
import wave

app = FastAPI()


@app.post("/upload")
async def receive_audio(audio: UploadFile = File(...)):
    contents = await audio.read()
    audio_data = io.BytesIO(contents)

    with wave.open(audio_data, "rb") as wav_file:
        n_frames = wav_file.getnframes()
        frame_rate = wav_file.getframerate()
        duration = n_frames / float(frame_rate)

    return {"length": duration}
