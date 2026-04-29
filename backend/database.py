from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:muni1234.@localhost:3306/ankara_full_4"                   

# SQLAlchemy'nin MySQL ile konuşma aracı
engine = create_engine(
    DATABASE_URL,
    echo=False
)

# SessionLocal: Her API isteği için ayrı bir veritabanı oturumu açar
# autocommit=False : İşlemleri biz onaylana kadar kaydetmez
# autoflush=False  : Biz istemedikçe veritabanına yazmaz


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base,tüm veritabanı modellerimiz bu sınıftan türeyecek, veritabanı bağlılığı yaptık
Base = declarative_base() 

# "yield" sayesinde istek bitince oturum otomatik kapanır

def get_db():
    db = SessionLocal()
    try:
        yield db        
    finally:
        db.close()      
