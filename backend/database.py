from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:muni1234.@localhost:3306/uygulama_db"                   

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


from sqlalchemy import create_engine, text
from config import MYSQL_URL

engine = create_engine(MYSQL_URL)

def get_all_listings() -> list[dict]:
    """Tüm ev ilanlarını MySQL'den çek."""
    with engine.connect() as conn:
        # Kendi tablo ve kolon adlarını buraya yaz!
        result = conn.execute(text("""
            SELECT 
                id,
                baslik,
                aciklama,
                fiyat,
                metrekare,
                oda_sayisi,
                ilce,
                sehir,
                kat,
                bina_yasi,
                isitma_tipi,
                ilan_tarihi
            FROM ev_ilanlari
            WHERE aktif = 1
        """))
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]


def listing_to_text(listing: dict) -> str:
    """İlan dict'ini LLM için okunabilir metne çevir."""
    return f"""
İlan ID: {listing.get('id')}
Başlık: {listing.get('baslik', '-')}
Şehir/İlçe: {listing.get('sehir', '-')} / {listing.get('ilce', '-')}
Fiyat: {listing.get('fiyat', '-')} TL
Metrekare: {listing.get('metrekare', '-')} m²
Oda Sayısı: {listing.get('oda_sayisi', '-')}
Kat: {listing.get('kat', '-')}
Bina Yaşı: {listing.get('bina_yasi', '-')}
Isıtma: {listing.get('isitma_tipi', '-')}
Açıklama: {listing.get('aciklama', '-')}
    """.strip()