# models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func       # Otomatik tarih için
from database import Base             # oluşturduğumuz Base için

class User(Base):
    __tablename__ = "users"   # MySQL'deki tablo adı

    id = Column(
        Integer,
        primary_key=True,   # Birincil anahtar
        index=True,         # Hızlı arama için index
        autoincrement=True  # Otomatik artan (1, 2, 3...)
    )

    full_name = Column(
        String(100),
        nullable=False      # Boş bırakılamaz
    )

    email = Column(
        String(255),
        unique=True,        # Aynı e-posta iki kez kayıt olamaz
        nullable=False,
        index=True          # E-posta ile sık arama yapacağız → index ekledik
    )

    hashed_password = Column(
        String(255),
        nullable=False      # Şifre zorunlu
    )

    is_active = Column(
        Boolean,
        default=True        # Yeni hesaplar varsayılan olarak aktif
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()  # Kayıt anında tarihi otomatik atar
    )