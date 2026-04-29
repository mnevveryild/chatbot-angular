from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List
import models
import schemas
from database import get_db
import uuid 
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MAX_CONTEXT_LISTINGS = int(os.getenv("MAX_CONTEXT_LISTINGS", 7))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", 120))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", 2048))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", 350))

llm = OllamaLLM(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,
    num_ctx=OLLAMA_NUM_CTX,
    num_predict=OLLAMA_NUM_PREDICT,
    top_p=0.8,
    repeat_penalty=1.1,
    keep_alive="10m",
)
llm_executor = ThreadPoolExecutor(max_workers=2)

answer_prompt = PromptTemplate.from_template(
    """Sen bir emlak ilan asistanisin. Sadece verilen ilan verilerini kullanarak Turkce cevap ver.
Verilen ilanda olmayan bir bilgiyi uydurma. Yeterli veri yoksa bunu acikca soyle.
En fazla 7 uygun ilani kisa maddeler halinde ozetle; veritabaninda verilen tum alanlari belirt.
Uzun analiz yapma, dusunme surecini yazma, sadece son cevabi yaz.
Cevap bos olamaz; uygun ilan varsa mutlaka listele.

Kullanici sorusu:
{question}

Veritabanindan bulunan ilanlar:
{listings_context}

Cevap:"""
)

STOP_WORDS = {
    "bir", "bu", "ve", "veya", "ile", "icin", "için", "olan", "olarak",
    "da", "de", "mi", "mu", "mı", "mü", "ev", "ilan", "ilanlar",
    "konut", "bana", "goster", "göster", "var", "varmi", "var mı",
    "nedir", "kaç", "kac", "en", "uygun", "tl", "den", "dan", "ten",
    "tan", "daha", "dusuk", "düşük", "az", "fazla", "fiyat", "fiyatli",
    "fiyatlı", "evleri", "listele", "getir", "getirir", "misin", "mısın",
    "mısiniz", "mısınız", "musun", "musunuz", "ilanı", "ilani", "ilanları",
    "ilanlari", "ilanını", "ilanini", "ilanlarını", "ilanlarini",
    "ilçesinde", "ilcesinde", "ilçesi", "ilcesi", "mahalle",
    "mahallesi", "mahallesinde", "mahallesindeki", "mahallede", "mahalledeki",
    "mah", "semt", "semtinde", "semtindeki"
} # bu kelimeler arama terimlerinden çıkarılacak, çünkü çok genel ve sonuçları kirletebilirler


app = FastAPI(
    title="Chatbot Kontrol Paneli",
    description="Angular + FastAPI + MySQL kayıt sistemi",
    version="1.0.0"
)


#CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200",
    "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Şifreleme için Passlib kullanarak bcrypt algoritmasıyla güvenli şifreleme yapıyoruz
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str):
    return pwd_context.hash(plain_password[:72])


def normalize_search_word(word: str) -> str:
    if word.endswith(("ndeki", "ndaki", "nteki", "ntaki")):
        return word[:-5]
    if word.endswith(("deki", "daki", "teki", "taki")):
        return word[:-4]
    if len(word) > 5 and word.endswith("ki"):
        return word[:-2]
    if len(word) > 5 and word.endswith(("li", "lı", "lu", "lü")):
        return word[:-2]
    return word


def extract_search_terms(question: str) -> list[str]:
    words = re.findall(r"[\wçğıöşüÇĞİÖŞÜ+]+", question.lower()) # kelimeleri ayırırken Türkçe karakterleri de dahil ediyoruz, ayrıca "+" işaretini de koruyoruz çünkü bazı kullanıcılar "2+1" gibi ifadeler kullanabilir
    cleaned_words = [normalize_search_word(word) for word in words]
    return [
        word for word in cleaned_words
        if (len(word) > 2 or "+" in word) and word not in STOP_WORDS and not word.isdigit()
    ][:8]# çok fazla terim arama sonuçlarını kirletebilir, bu yüzden ilk 8 terimi alıyoruz


def parse_price_filter(question: str):
    normalized = question.lower().replace("₺", " tl ")
    number_pattern = r"(\d[\d\.\,\s]{3,}\d|\d{5,})"

    lower_than_patterns = [
        rf"{number_pattern}\s*(?:tl)?\s*(?:den|dan|ten|tan)?\s*daha\s*(?:düşük|dusuk|az|ucuz)",
        rf"{number_pattern}\s*(?:tl)?\s*(?:altı|alti|altında|altinda)",
        rf"(?:maksimum|max|en fazla)\s*{number_pattern}",
    ]
    greater_than_patterns = [
        rf"{number_pattern}\s*(?:tl)?\s*(?:den|dan|ten|tan)?\s*daha\s*(?:yüksek|yuksek|fazla|pahalı|pahali)",
        rf"{number_pattern}\s*(?:tl)?\s*(?:üstü|ustu|üzerinde|uzerinde)",
        rf"(?:minimum|min|en az)\s*{number_pattern}",
    ]

    for pattern in lower_than_patterns:
        match = re.search(pattern, normalized)
        if match:
            return "lt", int(re.sub(r"\D", "", match.group(1)))

    for pattern in greater_than_patterns:
        match = re.search(pattern, normalized)
        if match:
            return "gt", int(re.sub(r"\D", "", match.group(1)))

    return None


def retrieve_relevant_listings(question: str, db: Session):
    terms = extract_search_terms(question)
    query = db.query(models.Ilan)
    price_filter = parse_price_filter(question)

    if price_filter:
        operator, amount = price_filter
        if operator == "lt":
            query = query.filter(models.Ilan.fiyat < amount)
        elif operator == "gt":
            query = query.filter(models.Ilan.fiyat > amount)

    if terms:
        for term in terms:
            like_term = f"%{term}%" #sql'de benzer arama yapmak için % işaretleriyle terimi sarıyoruz
            term_filters = [
                models.Ilan.baslik.ilike(like_term),
                models.Ilan.bulundugu_kat.ilike(like_term),
                models.Ilan.isinma_tipi.ilike(like_term),
                models.Ilan.tapu_durumu.ilike(like_term),
                models.Ilan.konut_tipi.ilike(like_term),
                models.Ilan.krediye_uygun.ilike(like_term),
                models.Ilan.esya_durumu.ilike(like_term),
                models.Ilan.konum.ilike(like_term),
            ]
            if "+" in term:
                term_filters.append(func.replace(models.Ilan.oda_sayisi, " ", "").ilike(like_term))
            else:
                term_filters.append(models.Ilan.oda_sayisi.ilike(like_term))
            query = query.filter(or_(*term_filters)) # Her arama terimi ayrı filtrelenir; "Çankaya 4+1" gibi isteklerde iki koşul da sağlanır.

    lower_question = question.lower()
    if price_filter or any(word in lower_question for word in ["ucuz", "uygun fiyat", "en uygun"]): # eğer soru "ucuz", "uygun fiyat" veya "en uygun" gibi kelimeler içeriyorsa sonuçları fiyata göre artan şekilde sıralıyoruz
        query = query.order_by(models.Ilan.fiyat.asc())
    elif any(word in lower_question for word in ["pahali", "pahalı", "en yüksek", "en yuksek"]):# eğer soru "pahalı", "en yüksek" gibi kelimeler içeriyorsa sonuçları fiyata göre azalan şekilde sıralıyoruz
        query = query.order_by(models.Ilan.fiyat.desc())

    return query.limit(MAX_CONTEXT_LISTINGS).all() 

# format düzenleme
def format_listing_context(listings: list[models.Ilan]) -> str:
    if not listings:
        return "Soru ile eslesen ilan bulunamadi."

    lines = []
    for ilan in listings:
        lines.append(
            "\n".join([
                f"Ilan no: {ilan.ilan_no}",
                f"Baslik: {ilan.baslik}",
                f"Fiyat: {ilan.fiyat}",
                f"Oda sayisi: {ilan.oda_sayisi}",
                f"Metrekare: {ilan.m2}",
                f"Bulundugu kat: {ilan.bulundugu_kat}",
                f"Bina yasi: {ilan.bina_yasi}",
                f"Isinma tipi: {ilan.isinma_tipi}",
                f"Tapu durumu: {ilan.tapu_durumu}",
                f"Konut tipi: {ilan.konut_tipi}",
                f"Banyo sayisi: {ilan.banyo_sayisi}",
                f"Kat sayisi: {ilan.kat_sayisi}",
                f"Krediye uygun: {ilan.krediye_uygun}",
                f"Esya durumu: {ilan.esya_durumu}",
                f"Konum: {ilan.konum}",
                f"URL: {ilan.url}",
            ])
        )
    return "\n\n---\n\n".join(lines)


def build_fallback_answer(listings: list[models.Ilan]) -> str:
    if not listings:
        return "Bu soruya uygun ilan bulunamadı."

    answer_lines = ["Bulduğum uygun ilanlar:"]
    for index, ilan in enumerate(listings[:MAX_CONTEXT_LISTINGS], start=1):
        answer_lines.append(
            "\n".join([
                f"{index}. {ilan.baslik}",
                f"   İlan no: {ilan.ilan_no}",
                f"   Fiyat: {ilan.fiyat} TL",
                f"   Oda sayısı: {ilan.oda_sayisi}",
                f"   m2: {ilan.m2}",
                f"   Bulunduğu kat: {ilan.bulundugu_kat}",
                f"   Bina yaşı: {ilan.bina_yasi}",
                f"   Isınma tipi: {ilan.isinma_tipi}",
                f"   Tapu durumu: {ilan.tapu_durumu}",
                f"   Konut tipi: {ilan.konut_tipi}",
                f"   Banyo sayısı: {ilan.banyo_sayisi}",
                f"   Kat sayısı: {ilan.kat_sayisi}",
                f"   Krediye uygun: {ilan.krediye_uygun}",
                f"   Eşya durumu: {ilan.esya_durumu}",
                f"   Konum: {ilan.konum}",
                f"   Link: {ilan.url}",
            ])
        )
    return "\n\n".join(answer_lines)

#llm cevap
def generate_llm_answer(question: str, listings_context: str) -> str:
    chain = answer_prompt | llm 
    future = llm_executor.submit(
        chain.invoke,
        {
            "question": question,
            "listings_context": listings_context,
        }
    )
    try:
        response = future.result(timeout=LLM_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        raise TimeoutError(
            f"LLM {LLM_TIMEOUT_SECONDS} saniye içinde cevap vermedi. "
            "Ollama çalışıyor mu ve model adı doğru mu kontrol edin."
        )

    raw_answer = response if isinstance(response, str) else getattr(response, "content", "")
    answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL | re.IGNORECASE)
    answer = re.sub(r"^[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]*|[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]*$", "", answer, flags=re.DOTALL | re.IGNORECASE) #cevabın başında veya sonunda gereksiz karakterler varsa temizliyoruz
    answer = answer.strip()
    if not answer:
        raise ValueError(f"LLM bos cevap dondurdu. Ham cevap: {raw_answer[:500]}")
    return answer


# register
@app.post(
    "/api/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED, #oluşturuldu
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
            status_code=status.HTTP_409_CONFLICT, #çakışma
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


# login
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
            status_code=status.HTTP_401_UNAUTHORIZED,#yetkisiz
            detail="E-posta veya şifre hatalı."
        )
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active
    }

# sohbet sorusu ve cevap
@app.post("/api/chat/ask", response_model=schemas.ChatAskResponse)
def ask_chatbot(
    request: schemas.ChatAskRequest,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.id == request.user_id
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı."
        )

    conversation_id = request.conversation_id or str(uuid.uuid4())
    try:
        listings = retrieve_relevant_listings(request.question, db)
        listings_context = format_listing_context(listings)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"İlanlar veritabanından okunamadı. Hata: {exc}"
        )

    try:
        answer = generate_llm_answer(request.question, listings_context)
    except Exception as exc:
        answer = build_fallback_answer(listings)

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sohbet mesajları kaydedilemedi. Hata: {exc}"
        )

    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "user_message": user_message,
        "assistant_message": assistant_message
    }



# mesaj kaydet 
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
            status_code=status.HTTP_404_NOT_FOUND, #bulunamadı
            detail="Kullanıcı bulunamadı."
        )

    # eğer conversation_id yoksa yeni bir UUID oluşturuyoruz
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
# seçili mesajları sil
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

# tüm geçmişi sil
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


# kullanıcının tüm konuşmalarını getir
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

# seçili konuşmayı getir
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
