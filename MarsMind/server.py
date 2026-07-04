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

app = Flask(__name__, static_folder="static")
HISTORY_FILE = "conversations.json"

def load_conversations():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_conversations(conversations):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2)

def get_or_create_conversation(conversation_id=None):
    conversations = load_conversations()

    if conversation_id and conversation_id in conversations:
        return conversation_id, conversations

    new_id = str(uuid.uuid4())
    conversations[new_id] = {
        "id": new_id,
        "title": "New repair session",
        "created_at": datetime.now().isoformat(),
        "messages": []
    }
    return new_id, conversations

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
    data = request.get_json()
    query_text = data.get("query", "").strip()
    incoming_conversation_id = data.get("conversation_id")

    if not query_text:
        return jsonify({"error": "No text provided."})

    conversation_id, conversations = get_or_create_conversation(incoming_conversation_id)

    answer = ask_gemma(query_text)

    if conversations[conversation_id]["title"] == "New repair session":
        conversations[conversation_id]["title"] = query_text[:40]

    conversations[conversation_id]["messages"].append({
        "role": "user",
        "text": query_text,
        "timestamp": datetime.now().isoformat()
    })

    conversations[conversation_id]["messages"].append({
        "role": "assistant",
        "text": answer,
        "timestamp": datetime.now().isoformat()
    })

    save_conversations(conversations)

    return jsonify({
        "query": query_text,
        "answer": answer,
        "conversation_id": conversation_id
    })

@app.route("/conversations", methods=["GET"])
def get_conversations():
    conversations = load_conversations()

    items = []
    for conv in conversations.values():
        items.append({
            "id": conv["id"],
            "title": conv.get("title", "Untitled"),
            "created_at": conv.get("created_at")
        })

    items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return jsonify(items)


@app.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    conversations = load_conversations()

    if conversation_id not in conversations:
        return jsonify({"error": "Conversation not found."}), 404

    return jsonify(conversations[conversation_id])


@app.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    conversations = load_conversations()

    if conversation_id not in conversations:
        return jsonify({"error": "Conversation not found."}), 404

    del conversations[conversation_id]
    save_conversations(conversations)

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)