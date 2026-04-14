from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict

# Gelen veri şeması (Angular → FastAPI)
class UserCreate(BaseModel):
    full_name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        examples=["Ahmet Yılmaz"]
    )
    email: EmailStr
    password: str = Field(
        ...,
        min_length=6,
        examples=["Guclu@Sifre123"]
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Şifre en az bir büyük harf içermelidir.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Şifre en az bir rakam içermelidir.")
        return v

# Dönen veri şeması (FastAPI → Angular)
class UserResponse(BaseModel):
    id: int
    email: EmailStr # Burada da EmailStr kullanmak validasyon tutarlılığı sağlar
    full_name: str  # <--- Bunu eklemeyi unutmayın!

    model_config = ConfigDict(from_attributes=True)