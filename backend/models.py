
from sqlalchemy import BigInteger, TIMESTAMP, Column, Enum, ForeignKey, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func       
from database import Base             

class User(Base):
    __tablename__ = "users" 
    id = Column(
        Integer,
        primary_key=True,   
        index=True,         
        autoincrement=True  
    )

    full_name = Column(
        String(100),
        nullable=False      
    )

    email = Column(
        String(255),
        unique=True,       
        nullable=False,
        index=True          
    )

    hashed_password = Column(
        String(255),
        nullable=False      
    )

    is_active = Column(
        Boolean,
        default=True        
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now() 
    )

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id"), 
        nullable=False
    )
    role = Column(
        Enum("user", "assistant", name="chat_roles"),
        nullable=False
    )
    conversation_id = Column(
        String(36), 
        nullable=False, 
        index=True
    )  
    content = Column(
        String(10000),
        nullable=False
    )
    created_at = Column(
        TIMESTAMP, 
        server_default=func.now()
    )

class Ilan(Base):
    __tablename__ = "ilanlar"

    ilan_no = Column(String(50), primary_key=True)
    baslik = Column(String(255))
    fiyat = Column(BigInteger)
    oda_sayisi = Column(String(50))
    m2 = Column(Integer)
    bulundugu_kat = Column(String(50))
    bina_yasi = Column(Integer)
    isinma_tipi = Column(String(100))
    tapu_durumu = Column(String(100))
    konut_tipi = Column(String(100))
    banyo_sayisi = Column(Integer)
    kat_sayisi = Column(Integer)
    krediye_uygun = Column(String(20))
    esya_durumu = Column(String(50))
    konum = Column(Text)
    url = Column(Text)
