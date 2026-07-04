from flask import Flask, jsonify, send_from_directory, request
import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import numpy as np
import requests
import json
import os
import uuid
from datetime import datetime

DURATION = 8
SAMPLE_RATE = 16000
AUDIO_FILENAME = "astronaut_query.wav"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma3:4b"
HISTORY_FILE = "conversations.json"

recording_frames = []
recording_stream = None

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


# ---------- conversation storage ----------

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def add_message(conversation_id, role, text):
    history = load_history()
    if conversation_id not in history:
        history[conversation_id] = {
            "title": text[:40] if role == "user" else "New conversation",
            "created": datetime.now().isoformat(),
            "messages": []
        }
    history[conversation_id]["messages"].append({"role": role, "text": text})
    save_history(history)


# ---------- Gemma reasoning ----------

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
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        }
    )
    if response.status_code == 200:
        raw_answer = response.json()["response"]
        cleaned = clean_answer(raw_answer)
        return enforce_low_confidence_stop(cleaned)
    else:
        return f"Error contacting Gemma: {response.status_code}"


def ask_gemma_stream(astronaut_query):
    """Get the full, correct answer first, then yield it out gradually
    to create a typing effect. This guarantees the enforced stop-on-low-
    confidence rule always applies correctly, since we process the
    complete answer before sending anything."""
    full_answer = ask_gemma(astronaut_query)
    full_answer = enforce_low_confidence_stop(full_answer)

    import time as _time
    words = full_answer.split(" ")
    for i, word in enumerate(words):
        piece = word + (" " if i < len(words) - 1 else "")
        yield piece
        _time.sleep(0.03)


def enforce_low_confidence_stop(text):
    """If confidence is Low, cut everything after the clarifying question,
    even if the model kept generating beyond it."""
    lines = text.split("\n")
    confidence_line = next((l for l in lines if l.lower().startswith("confidence:")), "")
    if "low" not in confidence_line.lower():
        return text

    question_index = next((i for i, l in enumerate(lines) if l.lower().startswith("question:")), None)
    if question_index is not None:
        return "\n".join(lines[:question_index + 1]).strip()
    return text


def clean_answer(text):
    if "Symptom:" in text:
        text = text[text.index("Symptom:"):]
    first = text.find("Symptom:")
    second = text.find("Symptom:", first + 1)
    if second != -1:
        text = text[:second]
    return text.strip()


# ---------- routes ----------

@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/conversations", methods=["GET"])
def get_conversations():
    history = load_history()
    summary = [
        {"id": cid, "title": data["title"], "created": data["created"]}
        for cid, data in history.items()
    ]
    summary.sort(key=lambda c: c["created"], reverse=True)
    return jsonify(summary)


@app.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    history = load_history()
    if conversation_id not in history:
        return jsonify({"error": "Not found"}), 404
    return jsonify(history[conversation_id])


@app.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    history = load_history()
    if conversation_id in history:
        del history[conversation_id]
        save_history(history)
    return jsonify({"deleted": conversation_id})


@app.route("/start-recording", methods=["POST"])
def start_recording():
    global recording_frames, recording_stream

    recording_frames = []

    def callback(indata, frames, time_info, status):
        recording_frames.append(indata.copy())

    recording_stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback
    )
    recording_stream.start()

    return jsonify({"status": "recording"})


@app.route("/stop-recording", methods=["POST"])
def stop_recording():
    global recording_frames, recording_stream
    conversation_id = request.args.get("conversation_id") or str(uuid.uuid4())

    if recording_stream is not None:
        recording_stream.stop()
        recording_stream.close()
        recording_stream = None

    if not recording_frames:
        return jsonify({"error": "No audio captured. Try again."})

    audio = np.concatenate(recording_frames, axis=0)
    write(AUDIO_FILENAME, SAMPLE_RATE, audio)

    volume = float(np.abs(audio).mean())
    if volume < 50:
        return jsonify({"error": "No sound detected. Check your microphone and try again."})

    result = whisper_model.transcribe(AUDIO_FILENAME)
    query_text = result["text"].strip()

    return jsonify({"query": query_text, "conversation_id": conversation_id})


@app.route("/cancel-recording", methods=["POST"])
def cancel_recording():
    global recording_frames, recording_stream
    if recording_stream is not None:
        recording_stream.stop()
        recording_stream.close()
        recording_stream = None
    recording_frames = []
    return jsonify({"status": "cancelled"})



@app.route("/ask-stream", methods=["POST"])
def ask_stream():
    from flask import Response, stream_with_context
    data = request.get_json()
    query_text = data.get("query", "").strip()
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())

    add_message(conversation_id, "user", query_text)

    def generate():
        full_answer = ""
        for piece in ask_gemma_stream(query_text):
            full_answer += piece
            yield piece
        add_message(conversation_id, "assistant", full_answer.strip())

    resp = Response(stream_with_context(generate()), mimetype="text/plain")
    resp.headers["X-Conversation-Id"] = conversation_id
    return resp


@app.route("/record-and-respond", methods=["POST"])
def record_and_respond():
    conversation_id = request.args.get("conversation_id") or str(uuid.uuid4())

    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    write(AUDIO_FILENAME, SAMPLE_RATE, audio)

    volume = float(np.abs(audio).mean())
    if volume < 50:
        return jsonify({"error": "No sound detected. Check your microphone and try again."})

    result = whisper_model.transcribe(AUDIO_FILENAME)
    query_text = result["text"].strip()

    add_message(conversation_id, "user", query_text)
    answer = ask_gemma(query_text)
    add_message(conversation_id, "assistant", answer)

    return jsonify({"query": query_text, "answer": answer, "conversation_id": conversation_id})


@app.route("/ask-text", methods=["POST"])
def ask_text():
    data = request.get_json()
    query_text = data.get("query", "").strip()
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())

    if not query_text:
        return jsonify({"error": "No text provided."})

    add_message(conversation_id, "user", query_text)
    answer = ask_gemma(query_text)
    add_message(conversation_id, "assistant", answer)

    return jsonify({"query": query_text, "answer": answer, "conversation_id": conversation_id})


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
