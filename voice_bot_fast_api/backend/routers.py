from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from controllers import respond_to_query
from schemas import voice_text_Output, voice_text_Response
import os
import shutil  #Dùng để lưu file mà không cần `open()`

router = APIRouter()

@router.post("/")
async def predict_voice_text(
    audio_file: Optional[UploadFile] = File(None), 
    text_query: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
):
    print(f"Received text_query: {text_query}")  
    print(f"Received audio_file: {audio_file.filename if audio_file else 'No audio'}")  
    print(f"Received pdf_file: {pdf_file.filename if pdf_file else 'No PDF'}")  

    # Kiểm tra ít nhất một input
    if not text_query and not audio_file and not pdf_file:
        raise HTTPException(status_code=400, detail="At least one input is required")

    # Định nghĩa thư mục lưu file
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TEMP_DIR = os.path.join(BASE_DIR, "fontend", "temp")
    os.makedirs(TEMP_DIR, exist_ok=True)  # Đảm bảo thư mục tồn tại

    #Lưu file AUDIO trực tiếp mà không cần `open()`
    audio_file_path = None
    if audio_file:
        audio_filename = os.path.basename(audio_file.filename)
        audio_file_path = os.path.join(TEMP_DIR, audio_filename)
        with audio_file.file as src, open(audio_file_path, "wb") as dest:
            shutil.copyfileobj(src, dest) 

    pdf_file_path = None
    if pdf_file:
        pdf_filename = os.path.basename(pdf_file.filename)
        pdf_file_path = os.path.join(TEMP_DIR, pdf_filename)
        with pdf_file.file as src, open(pdf_file_path, "wb") as dest:
            shutil.copyfileobj(src, dest) 
        print(f"PDF saved at: {pdf_file_path}")

    # Gọi xử lý
    text_query = text_query if text_query else None
    text, audio_path = respond_to_query(audio_file_path, pdf_file_path, text_query)

    # Trả về response
    response_data = voice_text_Output(
        text_response=text,
        audio_path=audio_path
    )
    return voice_text_Response(
        data=[response_data],
        status_code=200
    )
