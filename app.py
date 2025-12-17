from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
import os
import google.generativeai as genai
from gtts import gTTS
import re


#LLM MODEL
DRONAAI_SYSTEM_PROMPT = (
    "You are DronaAI, a virtual AI assistant for teachers. "
    "Respond politely, briefly, and helpfully. Use prior conversation turns for context. "
    "Prefer concise, actionable answers. If unclear, ask a short clarifying question. "
    "Avoid heavy punctuation or emojis."
    "And give reply in same language as the teacher is talking into"
)
GENAImodel = genai.GenerativeModel(
    model_name = "gemini-2.5-flash",
    system_instruction = DRONAAI_SYSTEM_PROMPT
)
chat_session = None


#WHISPER
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(BASE_DIR,'voice', 'voice.webm')
UPLOAD_FOLDER = 'voice'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
whisperModel = whisper.load_model("small")

app = Flask(__name__)
CORS(app)



@app.route('/')
def welcome():
    global chat_session
    webm_path = os.path.join('voice', 'voice.webm')
    mp3_path = os.path.join('voice', 'assistant_response.mp3')
    for file in [webm_path, mp3_path]:
        if os.path.exists(file):
            os.remove(file)
    chat_session = GENAImodel.start_chat(history=[])
    return render_template('index.html')

previous_prompts = []
@app.route('/api/upload', methods = ['POST'])
def upload_audio():
    global chat_session
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio_file = request.files['audio']
    file_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
    audio_file.save(file_path)
    print(f"✅ Audio received and saved at: {file_path}")
    # return jsonify({"message": "Audio uploaded successfully!"}), 200

    #giving audio to whisper
    result = whisperModel.transcribe(file_path)
    teacher_text = result["text"]
    detected_lang = result["language"]
    previous_prompts.append(teacher_text)
    print(teacher_text)


    #giving text to llm
    if chat_session is None:
        chat_session = GENAImodel.start_chat(history=[])
    response = chat_session.send_message(teacher_text)
    assistant_text = response.text or ""
    # assistant_text = re.sub(r'[^\w\s]', '', assistant_text, flags=re.UNICODE)
    # assistant_text = r    e.sub(r'[^\w\s\.\,\?\!\:\;\'\"-]', '', assistant_text, flags=re.UNICODE).strip()
    print(assistant_text)

    #TTS
    tts = gTTS(text=assistant_text, lang=detected_lang)
    tts_file = os.path.join(UPLOAD_FOLDER, "assistant_response.mp3")
    tts.save(tts_file)
    tts_url = "/voice/assistant_response.mp3"
    print(f"TTS saved at: {tts_file}")

    return jsonify({
        "message": "Audio processed successfully!",
        "teacher_text": teacher_text,
        "assistant_response": assistant_text,
        "tts_file": tts_url
    }), 200

@app.route('/voice/<path:filename>', methods=['GET'])
def serve_voice(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    app.run(debug = True, port = 5000)