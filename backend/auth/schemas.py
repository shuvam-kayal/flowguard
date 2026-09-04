from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    worker_id: str | None = None
    profile_complete: bool = False
    name: str | None = None

class TokenData(BaseModel):
    worker_id: str = None

class LoginRequest(BaseModel):
    phone: str
    password: str

class SignupRequest(BaseModel):
    email: str
    phone: str
    name: str = ""
    occupation: str = ""
    password: str
