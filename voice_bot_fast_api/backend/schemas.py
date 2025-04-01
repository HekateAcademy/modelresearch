from pydantic import BaseModel

class voice_text_Output(BaseModel):
    text_response: str
    audio_path: str

class voice_text_Response(BaseModel):
    data: list[voice_text_Output]
    status_code: int