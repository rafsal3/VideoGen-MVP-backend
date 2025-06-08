from pydantic import BaseModel
from typing import List
from typing import Optional

class Transcript(BaseModel):
    text: str
    start: int
    end: int

class Summary(BaseModel):
    text: str

class AudioResult(BaseModel):
    audio_url: str
    transcript: Transcript

class Asset(BaseModel):
    keyword: str
    type: str
    url: str
