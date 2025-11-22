import whisper
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(BASE_DIR,'voice', 'voice.webm')
print(file_path)
model = whisper.load_model("small")
result = model.transcribe(file_path)
text = result["text"]
print(text)