
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models
import schemas
from database import get_db

import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta

# .env dosyasını yükle
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# if not SECRET_KEY:
#     print("HATA: .env dosyasından SECRET_KEY okunamadı!")
# else:
#     print("Başarılı: Gizli anahtar yüklendi.")

# FastAPI uygulaması
app = FastAPI(
    title="Kayıt Sistemi API",
    description="Angular + FastAPI + MySQL kayıt sistemi",
    version="1.0.0"
)

# CORS Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE hepsine izin ver
    allow_headers=["*"],            # Tüm header'lara izin ver
)

# Şifre Hash'leme Aracı
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str):
    # Bcrypt 72 karakterden sonrasını kabul etmez, manuel olarak kesiyoruz.
    return pwd_context.hash(plain_password[:72])



# KAYIT ENDPOINT'İ

@app.post(
    "/api/register",
    response_model=schemas.UserResponse,       # Dönecek verinin şekli Fast'ten Angular'a
    status_code=status.HTTP_201_CREATED,       # Başarıda 201 döner
)
def register_user(
    user_data: schemas.UserCreate,             # Angular'dan gelen 
    db: Session = Depends(get_db)              
):
    #E-posta zaten kayıtlı mı?
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()  # İlk eşleşen kaydı getirir, yoksa None döner

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,   # 409 = çakışma
            detail="Bu e-posta adresi zaten kayıtlı."
        )


    #Şifreyi hash'le
    hashed_pw = hash_password(user_data.password)

    #Yeni kullanıcı nesnesini oluştur
    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_pw
    )

    #Veritabanına kaydet
    db.add(new_user)       # Oturuma ekle
    db.commit()            # Veritabanına kalıcı olarak yaz
    db.refresh(new_user)   # Veritabanından güncel veriyi geri oku

    return new_user        


# Login endpoint
@app.post("/api/login")
def login_user(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    #Kullanıcıyı e-posta ile bul
    user = db.query(models.User).filter(
        models.User.email == login_data.email
    ).first()

    if not user or not pwd_context.verify(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı."
        )
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active
    }