from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    worker_id: str = None

class LoginRequest(BaseModel):
    worker_id: str
    password: str
