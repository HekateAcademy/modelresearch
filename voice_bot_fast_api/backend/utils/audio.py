import os

import soundfile as sf
import torch
from groq import Groq
from transformers import AutoTokenizer, VitsModel


def process_audio_query(audio_file):
    os.environ["GROQ_API_KEY"] = (
        "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"  # Replace with your actual API key
    )
    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    with open(audio_file, "rb") as file:
        try:
            # Gửi yêu cầu chuyển đổi âm thanh thành văn bản
            transcription = client.audio.transcriptions.create(
                file=(audio_file, file.read()),  # Gửi file âm thanh
                model="whisper-large-v3-turbo",  # Model dùng để nhận diện
                prompt="Specify context or spelling",  # Tùy chọn context
                response_format="json",  # Định dạng trả về
                language="en",  # Ngôn ngữ của văn bản
                temperature=0.0,  # Điều chỉnh mức độ sáng tạo (0.0 cho kết quả chính xác nhất)
            )

            return transcription.text
        except Exception as e:
            return f"Error: {e}"


# Load mô hình TTS
model = VitsModel.from_pretrained("facebook/mms-tts-eng")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-eng")


def text_to_speech(text, output_path="output.wav"):
    """
    Chuyển văn bản thành âm thanh và lưu thành file WAV.
    """
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform

    # Lưu âm thanh thành file WAV
    sf.write(output_path, output.numpy().flatten(), 22050)  # 22050Hz là tần số lấy mẫu mặc định
    return output_path
