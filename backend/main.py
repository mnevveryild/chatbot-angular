from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List

import models
import schemas
from database import get_db
import uuid  # ← dosyanın en üstüne ekle

import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

app = FastAPI(
    title="Kayıt Sistemi API",
    description="Angular + FastAPI + MySQL kayıt sistemi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200",
    "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str):
    return pwd_context.hash(plain_password[:72])


# ───── REGISTER ─────
@app.post(
    "/api/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta adresi zaten kayıtlı."
        )

    hashed_pw = hash_password(user_data.password)

    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_pw
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ───── LOGIN ─────
@app.post("/api/login")
def login_user(
    login_data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == login_data.email
    ).first()

    if not user or not pwd_context.verify(login_data.password[:72], user.hashed_password):
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


# ───── CHAT MESAJI KAYDET ─────


@app.post("/api/chat", response_model=schemas.ChatMessageResponse)
def save_chat_message(
    chat_message: schemas.ChatMessageCreate,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.id == chat_message.user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı."
        )

    # conversation_id boş gelirse backend otomatik üretsin
    conversation_id = chat_message.conversation_id or str(uuid.uuid4())

    new_message = models.ChatHistory(
        user_id=chat_message.user_id,
        conversation_id=conversation_id,
        role=chat_message.role,
        content=chat_message.content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


# ───── SEÇİLİ MESAJLARI SİL (önce tanımlanmalı!) ─────
class DeleteMessagesRequest(BaseModel):
    message_ids: List[int]

@app.post("/api/chat/delete-messages")
def delete_messages(
    request: DeleteMessagesRequest,
    db: Session = Depends(get_db)
):
    if not request.message_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Silinecek mesaj ID'si belirtilmedi."
        )

    db.query(models.ChatHistory).filter(
        models.ChatHistory.id.in_(request.message_ids)
    ).delete(synchronize_session=False)
    db.commit()

    return {"message": f"{len(request.message_ids)} mesaj silindi."}

# ───── TÜM GEÇMİŞİ SİL ─────
@app.delete("/api/chat/{user_id}")
def delete_chat_history(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı."
        )

    db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id
    ).delete()
    db.commit()

    return {"message": "Sohbet geçmişi silindi."}


# ───── GEÇMİŞİ GETİR ─────
@app.get("/api/chat/{user_id}", response_model=list[schemas.ChatMessageResponse])
def get_chat_history(
    user_id: int,
    db: Session = Depends(get_db)
):
    # Kullanıcının tüm conversation_id'lerini gruplu getir
    messages = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id
    ).order_by(models.ChatHistory.created_at).all()
    return messages

# Konuşmaya göre mesaj getir
@app.get("/api/chat/{user_id}/{conversation_id}", response_model=list[schemas.ChatMessageResponse])
def get_conversation(
    user_id: int,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    messages = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id,
        models.ChatHistory.conversation_id == conversation_id
    ).order_by(models.ChatHistory.created_at).all()
    return messages