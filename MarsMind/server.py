from flask import Flask, jsonify, send_from_directory
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import numpy as np
import requests

DURATION = 8
SAMPLE_RATE = 16000
AUDIO_FILENAME = "astronaut_query.wav"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"

app = Flask(__name__, static_folder="static")

print("Loading Whisper model, this happens once at startup...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded.")

with open("rulebook.md", "r", encoding="utf-8") as f:
    rulebook = f.read()
with open("manual_water_recycler.md", "r", encoding="utf-8") as f:
    manual_water = f.read()
with open("manual_oxygen_system.md", "r", encoding="utf-8") as f:
    manual_oxygen = f.read()


def ask_gemma(astronaut_query):
    prompt = f"""{rulebook}

Here are the technical manuals available to you:

{manual_water}

{manual_oxygen}

The astronaut just said: "{astronaut_query}"

Fill in the template now. Output only the filled template, nothing else.
No explanations, no repeated drafts, no notes.
"""
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": prompt, "stream": False}
    )
    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"Error contacting Gemma: {response.status_code}"


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/record-and-respond", methods=["POST"])
def record_and_respond():
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    write(AUDIO_FILENAME, SAMPLE_RATE, audio)

    volume = float(np.abs(audio).mean())
    if volume < 50:
        return jsonify({"error": "No sound detected. Check your microphone and try again."})

    result = whisper_model.transcribe(AUDIO_FILENAME)
    query_text = result["text"].strip()

    answer = ask_gemma(query_text)

    return jsonify({"query": query_text, "answer": answer})


@app.route("/ask-text", methods=["POST"])
def ask_text():
    from flask import request
    data = request.get_json()
    query_text = data.get("query", "").strip()
    if not query_text:
        return jsonify({"error": "No text provided."})
    answer = ask_gemma(query_text)
    return jsonify({"query": query_text, "answer": answer})


if __name__ == "__main__":
    app.run(debug=True, port=5000)