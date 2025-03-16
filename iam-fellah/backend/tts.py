import requests
from flask import Flask, request, jsonify
from gradio_client import Client, handle_file

app = Flask(__name__)

def generate_tts(text):
    client = Client("medmac01/Darija-Arabic-TTS")

    try:
        print(f"🔄 Requesting TTS for text: {text}")
        result = client.predict(
            text=text,
            speaker_audio_path=handle_file('https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav'),
            temperature=0.75,
            api_name="/infer_EGTTS",
            use_gpu=False  # Ensure this setting is supported
        )

        print(f"✅ Gradio TTS Response: {result}")

        if not result:
            print("⚠️ Empty response from TTS API!")
            return None

        # If response is a /tmp/gradio/... path, convert it to a public URL
        if result.startswith("/tmp/gradio/"):
            filename = result.split("/")[-2] + "/" + result.split("/")[-1]
            gradio_audio_url = f"https://medmac01-darija-arabic-tts.hf.space/file={filename}"
            print(f"🌍 Gradio File URL: {gradio_audio_url}")
            return gradio_audio_url

        else:
            print("⚠️ Unexpected response format from TTS API!")
            return None

    except Exception as e:
        print(f"❌ Exception in generate_tts(): {e}")
        return None

