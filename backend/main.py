import uuid
import asyncio
from typing import List
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from passlib.context import CryptContext

import models
import schemas
from config import settings
from agent import flush_observability, run_agent
from database import get_db

app = FastAPI(
    title="Emlak Chatbot API",
    description="Asenkron SQL Agent tabanlı emlak chatbot",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.on_event("shutdown")
def shutdown_observability():
    flush_observability()


# ── Kullanıcı ──────────────────────────────────────────────────────────────────

@app.post("/api/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu e-posta adresi zaten kayıtlı.")

    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=pwd_context.hash(user_data.password[:72])
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/login")
def login_user(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not pwd_context.verify(login_data.password[:72], user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-posta veya şifre hatalı.")

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
        }
    }


@app.post("/api/reset-password")
def reset_password(request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kayıtlı kullanıcı bulunamadı.")

    user.hashed_password = pwd_context.hash(request.new_password[:72])
    db.commit()
    return {"message": "Şifreniz başarıyla güncellendi."}


# ── Chatbot ────────────────────────────────────────────────────────────────────

@app.post("/api/chat/ask", response_model=schemas.ChatAskResponse)
async def ask_chatbot(request: schemas.ChatAskRequest, db: Session = Depends(get_db)):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    try:
        history = []
        if request.conversation_id:
            recent_messages = (
                db.query(models.ChatHistory)
                .filter(
                    models.ChatHistory.user_id == request.user_id,
                    models.ChatHistory.conversation_id == request.conversation_id,
                )
                .order_by(desc(models.ChatHistory.created_at))
                .limit(10)
                .all()
            )
            recent_messages.reverse()
            history = [(msg.role, msg.content) for msg in recent_messages]

        answer = await asyncio.to_thread(
            run_agent,
            request.question,
            history,
            user_id=request.user_id,
            conversation_id=conversation_id,
        )

    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc))
    except Exception as exc:
        import logging
        logging.error(f"Agent Hatası: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Yapay zeka yanıt verirken bir sorun oluştu.")

    user_message = models.ChatHistory(
        user_id=request.user_id,
        conversation_id=conversation_id,
        role="user",
        content=request.question
    )
    assistant_message = models.ChatHistory(
        user_id=request.user_id,
        conversation_id=conversation_id,
        role="assistant",
        content=answer
    )

    try:
        db.add_all([user_message, assistant_message])
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Mesajlar veritabanına kaydedilemedi.")

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "user_message": user_message,
        "assistant_message": assistant_message
    }


@app.post("/api/chat", response_model=schemas.ChatMessageResponse)
def save_chat_message(chat_message: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
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


class DeleteMessagesRequest(BaseModel):
    message_ids: List[int]
    user_id: int


@app.post("/api/chat/delete-messages")
def delete_messages(request: DeleteMessagesRequest, db: Session = Depends(get_db)):
    if not request.message_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Silinecek mesaj ID'si belirtilmedi.")

    deleted_count = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == request.user_id,
        models.ChatHistory.id.in_(request.message_ids),
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": f"{deleted_count} mesaj silindi."}


@app.delete("/api/chat")
def delete_chat_history(user_id: int, db: Session = Depends(get_db)):
    db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user_id).delete()
    db.commit()
    return {"message": "Sohbet geçmişi silindi."}


@app.get("/api/chat", response_model=list[schemas.ChatMessageResponse])
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id
    ).order_by(models.ChatHistory.created_at).all()


@app.get("/api/chat/{conversation_id}", response_model=list[schemas.ChatMessageResponse])
def get_conversation(conversation_id: str, user_id: int, db: Session = Depends(get_db)):
    return db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id,
        models.ChatHistory.conversation_id == conversation_id
    ).order_by(models.ChatHistory.created_at).all()