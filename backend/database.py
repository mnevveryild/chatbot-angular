from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:muni1234.@localhost:3306/uygulama_db"                   

# SQLAlchemy'nin MySQL ile "konuşma" aracı
engine = create_engine(
    DATABASE_URL,
    echo=True  # Geliştirme sırasında SQL sorgularını terminalde gösterir
               # Canlıya alırken False yapabiliriz
)

# SessionLocal: Her API isteği için ayrı bir veritabanı oturumu açar

# autocommit=False → İşlemleri biz onaylana kadar kaydetmez (güvenli)
# autoflush=False  → Biz istemedikçe veritabanına yazmaz
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base: Tüm veritabanı modellerimiz bu sınıftan türeyecek


Base = declarative_base()

# Dependency (Bağımlılık): Her endpoint'e veritabanı oturumu sağlar
# "yield" sayesinde istek bitince oturum otomatik kapanır

def get_db():
    db = SessionLocal()
    try:
        yield db        # Oturumu endpoint'e ver
    finally:
        db.close()      