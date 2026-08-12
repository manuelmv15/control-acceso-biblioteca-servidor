from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class CambiarPasswordRequest(BaseModel):
    password_actual: str
    password_nueva: str
