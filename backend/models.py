
from sqlalchemy import TIMESTAMP, Column, Enum, ForeignKey, Integer, String, Boolean, DateTime
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
    content = Column(
        String(10000),
        nullable=False
    )
    created_at = Column(
        TIMESTAMP, 
        server_default=func.now()
    )
    

    