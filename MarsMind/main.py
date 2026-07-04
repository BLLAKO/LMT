import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import numpy as np
import time
import requests
import json

DURATION = 8
SAMPLE_RATE = 16000
AUDIO_FILENAME = "astronaut_query.wav"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:1b"

# ---------- Step 1: record the astronaut's voice ----------

print("Get ready to speak your problem out loud.")
for i in [3, 2, 1]:
    print(i)
    time.sleep(1)

print(f">>> SPEAK NOW <<< (you have {DURATION} seconds)")
audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
sd.wait()
write(AUDIO_FILENAME, SAMPLE_RATE, audio)

volume = np.abs(audio).mean()
print(f"Average volume level: {volume:.1f}")

# ---------- Step 2: transcribe with Whisper ----------

print("Loading Whisper model...")
whisper_model = whisper.load_model("base")

print("Transcribing...")
result = whisper_model.transcribe(AUDIO_FILENAME)
astronaut_query = result["text"].strip()

print(f"\nAstronaut said: \"{astronaut_query}\"")

# ---------- Step 3: load the rulebook and manuals ----------

with open("rulebook.md", "r", encoding="utf-8") as f:
    rulebook = f.read()

with open("manual_water_recycler.md", "r", encoding="utf-8") as f:
    manual_water = f.read()

with open("manual_oxygen_system.md", "r", encoding="utf-8") as f:
    manual_oxygen = f.read()

# ---------- Step 4: build the prompt for Gemma ----------

prompt = f"""{rulebook}

Here are the technical manuals available to you:

{manual_water}

{manual_oxygen}

The astronaut just said: "{astronaut_query}"

Follow the rules and output format described above exactly.
"""

# ---------- Step 5: send it to Gemma via Ollama ----------

print("\nSending to Gemma for reasoning...\n")

response = requests.post(
    OLLAMA_URL,
    json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
)

if response.status_code == 200:
    answer = response.json()["response"]
    print("--- Gemma's response ---")
    print(answer)
else:
    print(f"Error: received status code {response.status_code}")
    print(response.text)
