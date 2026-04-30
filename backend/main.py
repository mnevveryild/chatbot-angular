import uuid
import os
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

import models
import schemas
from database import get_db

load_dotenv()

# ─── Ortam değişkenleri ───────────────────────────────────────────────────────
OLLAMA_MODEL         = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_BASE_URL      = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_TIMEOUT_SECONDS  = int(os.getenv("LLM_TIMEOUT_SECONDS", 1000000))
MAX_CONTEXT_LISTINGS = int(os.getenv("MAX_CONTEXT_LISTINGS", 7))

# MySQL bağlantısı — agent veritabanını doğrudan okuyacak
MYSQL_URI = os.getenv(
    "MYSQL_URI",
    "mysql+pymysql://kullanici:sifre@localhost:3306/veritabani"
)


llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.0,   
    num_ctx=4096,      
    num_predict=1024,
    keep_alive="10m",
)

agent_db = SQLDatabase.from_uri(
    MYSQL_URI,
    sample_rows_in_table_info=2,  
)


toolkit = SQLDatabaseToolkit(db=agent_db, llm=llm)
tools   = toolkit.get_tools()

SYSTEM_PROMPT = SystemMessage(content=f"""
Sen bir emlak veritabanı asistanısın. Kullanıcının sorularını yanıtlamak için
SQL sorguları yaz, çalıştır ve sonuçları Türkçe olarak açıkla.

Kurallar:
- Yalnızca SELECT sorguları kullan; INSERT, UPDATE, DELETE, DROP YASAK.
- Sorgunu çalıştırmadan önce sql_db_query_checker aracıyla kontrol et.
- Hata alırsan sorguyu düzelt ve tekrar dene.
- Cevabını her zaman Türkçe ver.
- Önce sql_db_list_tables ile tabloları keşfet, sonra sql_db_schema ile
  ilgili tablonun şemasına bak, ardından sorgu yaz.
- Kullanıcının sorusunu doğrudan yanıtla, gereksiz teknik detay verme.
- ilanları listelerken tüm özellikleriyle birlikte göster, ilan no, başlık, fiyat, oda sayısı, m2, kat bilgisi, bina yaşı, ısınma tipi, tapu durumu, konut tipi, banyo sayısı, kat sayısı, krediye uygunluk, eşya durumu, konum ve url bilgilerini dahil et.
""")

agent_executor = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

llm_executor = ThreadPoolExecutor(max_workers=2)


def run_agent(question: str) -> str:
    """
    ReAct agent akışı:
      1. Tabloları listeler
      2. İlgili tablo şemasını okur
      3. SQL yazar ve checker ile doğrular
      4. SQL'i çalıştırır
      5. Sonucu Türkçe özetler
    Tüm adımlar LangGraph tarafından otomatik yönetilir.
    """
    def _invoke():
        result = agent_executor.invoke(
            {"messages": [HumanMessage(content=question)]}
        )
        final_message = result["messages"][-1]
        return final_message.content if hasattr(final_message, "content") else str(final_message)

    future = llm_executor.submit(_invoke)
    try:
        answer = future.result(timeout=LLM_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        raise TimeoutError(
            f"Agent {LLM_TIMEOUT_SECONDS} saniye içinde cevap vermedi. "
            "Ollama çalışıyor mu ve model adı doğru mu kontrol edin."
        )

    if not answer or not answer.strip():
        raise ValueError("Agent boş cevap döndürdü.")

    return answer.strip()



app = FastAPI(
    title="Emlak Chatbot API",
    description="SQL Agent tabanlı emlak chatbot",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain[:72])


@app.post("/api/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bu e-posta adresi zaten kayıtlı.")

    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
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
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active
    }


@app.post("/api/chat/ask", response_model=schemas.ChatAskResponse)
def ask_chatbot(request: schemas.ChatAskRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı.")

    conversation_id = request.conversation_id or str(uuid.uuid4())

    try:
        answer = run_agent(request.question)
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Agent hatası: {exc}")

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mesajlar kaydedilemedi: {exc}")

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "user_message": user_message,
        "assistant_message": assistant_message
    }


@app.post("/api/chat", response_model=schemas.ChatMessageResponse)
def save_chat_message(chat_message: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == chat_message.user_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı.")

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


@app.post("/api/chat/delete-messages")
def delete_messages(request: DeleteMessagesRequest, db: Session = Depends(get_db)):
    if not request.message_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Silinecek mesaj ID'si belirtilmedi.")
    db.query(models.ChatHistory).filter(
        models.ChatHistory.id.in_(request.message_ids)
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": f"{len(request.message_ids)} mesaj silindi."}


@app.delete("/api/chat/{user_id}")
def delete_chat_history(user_id: int, db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == user_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı.")
    db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user_id).delete()
    db.commit()
    return {"message": "Sohbet geçmişi silindi."}


@app.get("/api/chat/{user_id}", response_model=list[schemas.ChatMessageResponse])
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id
    ).order_by(models.ChatHistory.created_at).all()


@app.get("/api/chat/{user_id}/{conversation_id}", response_model=list[schemas.ChatMessageResponse])
def get_conversation(user_id: int, conversation_id: str, db: Session = Depends(get_db)):
    return db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == user_id,
        models.ChatHistory.conversation_id == conversation_id
    ).order_by(models.ChatHistory.created_at).all()