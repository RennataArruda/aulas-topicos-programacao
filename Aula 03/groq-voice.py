import os
from groq import Groq
from datetime import timedelta

# Initialize the Groq client
client = Groq()

# Specify the path to the audio file
filename = os.path.dirname(__file__) + "/stray_kids_audio_local.mp3"

# Open the audio file
with open(filename, "rb") as file:
    # Create a transcription of the audio file
    transcription = client.audio.transcriptions.create(
        file=(filename, file.read()),  # Required audio file
        model="whisper-large-v3-turbo",  # Required model
        prompt="Entrevista",  # Optional
        response_format="verbose_json",  # Optional
        language="pt",  # Optional
        temperature=0.0  # Optional
    )

# Exibir texto transcrito completo (caso seja suportado)
if hasattr(transcription, "text"):
    print("\nTranscrição completa:\n")
    print(transcription.text)

# Exibir transcrição com tempo
if hasattr(transcription, "segments"):
    print("\nTranscrição com tempo:\n")
    for segment in transcription.segments:
        start = str(timedelta(seconds=segment["start"]))
        end = str(timedelta(seconds=segment["end"]))
        text = segment["text"]
        print(f"[{start} - {end}] {text}")
else:
    print("Segmentos com tempo não encontrados na transcrição.")
