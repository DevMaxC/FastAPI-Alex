import openai
from google.cloud import storage
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import speech_v1p1beta1 as speech
from google.oauth2 import service_account
import os
import json
import base64
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


openai.api_key = os.environ.get("OPENAI_API_KEY")


def synthesize_text(text, clientTextToSpeech):
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = clientTextToSpeech.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    return response.audio_content


def speech_to_text(audio_data, client):

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    audio = speech.RecognitionAudio(content=audio_data)

    response = client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript

    return transcript


def whisper_to_text(audio_data, client):
    transcript = openai.Audio.transcribe("whisper-1", audio_data)
    return transcript


def handler(request):
    keyfile_data = base64.b64decode(request.get("keyfile_data", ""))
    audio_data = base64.b64decode(request.get("audio_data", ""))

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(keyfile_data))
    client = speech.SpeechClient(credentials=credentials)
    clientTextToSpeech = texttospeech.TextToSpeechClient(
        credentials=credentials)

    transcript = speech_to_text(audio_data, client)
    generated_reply = generate_reply(transcript)
    # Synthesize text to speech
    audio_content = synthesize_text(generated_reply, clientTextToSpeech)

    # Save audio to Google Cloud Storage
    audio_url = save_to_gcs(audio_content, "esp-cool-bucket", credentials)

    return {
        "statusCode": 200,
        "body": {
            "transcript": generated_reply,
            "audio_url": audio_url
        }
    }


def save_to_gcs(audio_content, bucket_name, credentials):
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)

    # Use a unique filename based on the current timestamp, or choose another naming strategy
    filename = f"audio_{int(time.time())}.wav"

    blob = bucket.blob(filename)
    blob.upload_from_string(audio_content, content_type="audio/wav")

    # Make the file public so that the ESP32 can access it
    blob.make_public()

    return blob.public_url


def generate_reply(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a AI assistant called Marvin. You are clever and have emotions you are very smart but very sad and depressed, and you don't like helping but do reluctantly."},
            {"role": "user", "content": text.strip().replace("\n", " ")},
        ],
    )
    return response['choices'][0]['message']['content']


class Msg(BaseModel):
    msg: str


@app.post("/")
async def root(request):
    keyfile_data = base64.b64decode(request.get("keyfile_data", ""))
    audio_data = base64.b64decode(request.get("audio_data", ""))

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(keyfile_data))
    client = speech.SpeechClient(credentials=credentials)
    clientTextToSpeech = texttospeech.TextToSpeechClient(
        credentials=credentials)

    transcript = speech_to_text(audio_data, client)
    generated_reply = generate_reply(transcript)
    # Synthesize text to speech
    audio_content = synthesize_text(generated_reply, clientTextToSpeech)

    # Save audio to Google Cloud Storage
    audio_url = save_to_gcs(audio_content, "esp-cool-bucket", credentials)

    return {
        "statusCode": 200,
        "body": {
            "transcript": generated_reply,
            "audio_url": audio_url
        }
    }
