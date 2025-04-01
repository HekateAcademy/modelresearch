from utils.audio import process_audio_query, text_to_speech
from utils.process_PDF import get_chain,  read_pdf

import io
import os
import tempfile

def respond_to_query(audio_file=None, pdf_file=None, text_query=None):
    """
    Xử lý file audio, PDF và văn bản người dùng nhập và tạo phản hồi dưới dạng văn bản và âm thanh.
    """
    audio_text = ""
    if audio_file:
        audio_text1 = process_audio_query(audio_file)
        audio_text = f"You said: {audio_text1}"
    else:
        audio_text1 = ""

    # Case 3: Xử lý văn bản người dùng nhập
    if text_query:
        user_input = f"You typed: {text_query}"
        user_input1 = text_query
    else:
        user_input = ""
        user_input1 = ""

    chain_response = ""
    folder_path = "./PDF_data/"
    input_query = "User wants to know about " + audio_text1 + " " + user_input1
    if pdf_file:
        chain_response = get_chain(input_query, folder_path, pdf_file)
    else:
        pdf_file = "notification.txt"
        chain_response = get_chain(input_query , folder_path, pdf_file)

    final_response = audio_text + "\n" + user_input + "\n" + chain_response + "\n"

    # Tạo âm thanh từ kết quả
    audio_path = text_to_speech(final_response)

    return final_response, audio_path