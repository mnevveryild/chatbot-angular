from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict
from datetime import datetime

# Gelen veri şeması (Angular -> FastAPI)
class UserCreate(BaseModel):
    full_name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
    )
    email: EmailStr
    password: str = Field(
        ...,
        min_length=6,
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Şifre en az bir büyük harf içermelidir.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Şifre en az bir rakam içermelidir.")
        return v

# Dönen veri şeması (FastAPI -> Angular)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    model_config = ConfigDict(from_attributes=True)

# Login için gelen veriyi doğrulayan şema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Chat geçmişi için gelen veriyi tanımlayan şema (Angular -> FastAPI)
class ChatMessageCreate(BaseModel):
    user_id:int
    role:str = Field(
        ...,
        pattern="^(user|assistant)$",

    )
    conversation_id: str | None = None  # nullable, yani boş olabilir
    content:str = Field(    
        ...,
        min_length=1,
        max_length=10000
    )
    
    
# Chat geçmişi için dönen veriyi tanımlayan şema (FastAPI -> Angular)    
class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    role: str
    content: str
    created_at: datetime 
    conversation_id: str | None = None  # nullable, yani boş olabilir

    model_config = ConfigDict(from_attributes=True)