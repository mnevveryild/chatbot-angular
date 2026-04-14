
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models
import schemas
from database import engine, get_db

# Uygulama başlarken tabloları otomatik oluştur
# (MySQL'de tablo yoksa CREATE TABLE çalıştırır)

models.Base.metadata.create_all(bind=engine)

# FastAPI uygulaması
app = FastAPI(
    title="Kayıt Sistemi API",
    description="Angular + FastAPI + MySQL kayıt sistemi",
    version="1.0.0"
)

# CORS Ayarları
# Angular geliştirme sunucusu genellikle localhost:4200'de çalışır
# CORS olmadan tarayıcı bu isteği engeller!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",    # Angular geliştirme ortamı
        "http://localhost:3000",    # (gerekirse ekstra portlar)
    ],
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE hepsine izin ver
    allow_headers=["*"],            # Tüm header'lara izin ver
)

# Şifre Hash'leme Aracı
# bcrypt: Endüstri standardı, güvenli hash algoritması
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    """Düz metin şifreyi bcrypt ile hash'ler"""
    return pwd_context.hash(plain_password)



# KAYIT ENDPOINT'İ
# POST /api/register

@app.post(
    "/api/register",
    response_model=schemas.UserResponse,       # Dönecek verinin şekli
    status_code=status.HTTP_201_CREATED,       # Başarıda 201 döner
    summary="Yeni kullanıcı kaydı oluştur"
)
def register_user(
    user_data: schemas.UserCreate,             # Angular'dan gelen JSON → otomatik doğrulanır
    db: Session = Depends(get_db)              # Veritabanı oturumu → otomatik enjekte edilir
):
    """
    Yeni kullanıcı kaydı oluşturur.
    - E-posta benzersizliği kontrol edilir
    - Şifre bcrypt ile hash'lenerek saklanır
    - Başarıda kullanıcı bilgileri döner (şifre HARİÇ)
    """

    # 1. ADIM: E-posta zaten kayıtlı mı?
    existing_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()  # İlk eşleşen kaydı getirir, yoksa None döner

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,   # 409 = çakışma
            detail="Bu e-posta adresi zaten kayıtlı."
        )


    # 2. ADIM: Şifreyi hash'le (ASLA düz metin kaydetme!)
    hashed_pw = hash_password(user_data.password)

    # 3. ADIM: Yeni kullanıcı nesnesini oluştur

    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_pw   # Hash'lenmiş şifre kaydediliyor
    )

    # 4. ADIM: Veritabanına kaydet
    db.add(new_user)       # Oturuma ekle
    db.commit()            # Veritabanına kalıcı olarak yaz
    db.refresh(new_user)   # Veritabanından güncel veriyi geri oku (id, created_at gibi alanlar için)

    return new_user        # UserResponse şemasına göre döner (şifre YOK)


# SAĞLIK KONTROLÜ — API çalışıyor mu?
# GET /health → {"status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API çalışıyor"}