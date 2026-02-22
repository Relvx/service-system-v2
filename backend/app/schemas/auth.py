from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token: str
    user: "UserOut"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


from app.schemas.user import UserOut
TokenResponse.model_rebuild()
