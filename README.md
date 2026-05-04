
# 🏠 Emlak Chatbot

**Angular 21 + FastAPI + LangGraph tabanlı akıllı emlak danışmanı**

[![Angular](https://img.shields.io/badge/Angular-21.x-DD0031?logo=angular)](https://angular.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct_Agent-FF6F00)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1--mini-412991?logo=openai)](https://platform.openai.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.x-4479A1?logo=mysql)](https://www.mysql.com)
[![License](https://img.shields.io/badge/Lisans-MIT-green)](LICENSE)

---

## 📌 Proje Hakkında

Emlak Chatbot, MySQL'deki emlak ilanlarını bir **LangGraph ReAct Agent** aracılığıyla sorgulayan, kullanıcıyla Türkçe konuşan ve konuşma geçmişini hatırlayan tam yığın (full-stack) bir web uygulamasıdır.

Kullanıcılar; oda sayısı, fiyat aralığı, konum veya ilan numarası gibi kriterleri doğal dille ifade edebilir. Agent bu soruları SQL sorgularına dönüştürür, sonucu yorumlar ve insan gibi bir yanıt üretir.

---

## 🖥️ Ekran Görüntüleri

| Giriş Ekranı | Chat Ekranı (Açık Tema) | Chat Ekranı (Koyu Tema) |
|:---:|:---:|:---:|
| *(Login / Kayıt / Şifre Sıfırlama)* | *(Sohbet + Yan Menü)* | *(Dark Mode)* |

---

## ✨ Özellikler

### Kullanıcı Arayüzü
- 🔐 **Kimlik doğrulama** — Kayıt, giriş ve şifre sıfırlama akışları
- 💬 **Çoklu konuşma** — Her sohbet ayrı bir `conversation_id` ile saklanır
- 🌙 **Açık / Koyu tema** — `localStorage`'da kalıcı
- 📱 **Responsive** — Masaüstü ve mobil uyumlu
- ⌨️ **Enter gönder, Shift+Enter alt satır** — Klavye kısayolları
- 🗑️ **Sohbet silme** — Onay adımı ile güvenli silme

### Backend & AI
- 🤖 **LangGraph ReAct Agent** — Düşün → Araç çağır → Gözlemle döngüsü
- 🗄️ **SQL Agent Toolkit** — `sql_db_query_checker` ile sorgu doğrulama
- 📜 **Konuşma hafızası** — Geçmiş mesajlar her istekte agent'a iletilir
- 🔒 **Salt okunur SQL** — Yalnızca `SELECT`; `INSERT/UPDATE/DELETE/DROP` yasak
- ⏱️ **Timeout koruması** — Yapılandırılabilir LLM zaman aşımı
- 📊 **Langfuse entegrasyonu** — İsteğe bağlı LLM gözlemlenebilirliği (observability)

---

## 🏗️ Mimari

```
chatbot-angular/
├── backend/                  # FastAPI uygulaması
│   ├── main.py               # API rotaları (auth + chat)
│   ├── agent.py              # LangGraph ReAct Agent
│   ├── llm_provider.py       # OpenAI LLM fabrikası
│   ├── models.py             # SQLAlchemy ORM modelleri
│   ├── schemas.py            # Pydantic şemaları
│   ├── config.py             # Ortam değişkenleri (.env)
│   ├── database.py           # DB bağlantısı
│   └── requirements.txt      # Python bağımlılıkları
│
└── realestate-chatbot/       # Angular uygulaması
    └── src/app/
        ├── login/            # Giriş / Kayıt / Şifre sıfırlama
        ├── chat/             # Ana chat ekranı
        ├── auth.ts           # AuthService (signals)
        ├── chat.ts           # ChatService (konuşma yönetimi)
        ├── auth-guard.ts     # Route koruma
        └── app.routes.ts     # /login → /chat yönlendirme
```

### Veri Akışı

```
Kullanıcı → Angular ChatComponent
    → ChatService.sendMessage()
        → POST /api/chat/ask
            → run_agent(question, history)
                → LangGraph ReAct Agent
                    → SQLDatabaseToolkit (ilanlar tablosu)
                        → MySQL
                    ← SQL sonuçları
                ← Yorumlanmış Türkçe yanıt
            ← ChatAskResponse {answer, conversation_id}
        → Mesaj UI'a eklenir
```

---

## 🗃️ Veritabanı Şeması

### `users` Tablosu

| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | INT PK AI | Kullanıcı kimliği |
| `full_name` | VARCHAR(100) | Ad soyad |
| `email` | VARCHAR(255) UNIQUE | E-posta |
| `hashed_password` | VARCHAR(255) | bcrypt hash |
| `is_active` | BOOLEAN | Hesap durumu |
| `created_at` | DATETIME | Oluşturma zamanı |

### `chat_history` Tablosu

| Sütun | Tür | Açıklama |
|---|---|---|
| `id` | INT PK AI | Mesaj kimliği |
| `user_id` | INT FK | `users.id` referansı |
| `conversation_id` | VARCHAR(36) | UUID tabanlı sohbet grubu |
| `role` | ENUM | `user` veya `assistant` |
| `content` | VARCHAR(10000) | Mesaj içeriği |
| `created_at` | TIMESTAMP | Gönderim zamanı |

### `ilanlar` Tablosu (Kaynak Veri)

| Sütun | Tür | Açıklama |
|---|---|---|
| `ilan_no` | VARCHAR(50) PK | Benzersiz ilan numarası |
| `baslik` | VARCHAR(255) | İlan başlığı |
| `fiyat` | BIGINT | Satış/kira fiyatı |
| `oda_sayisi` | VARCHAR(50) | Oda + salon (ör. "3+1") |
| `m2` | INT | Brüt metrekare |
| `bulundugu_kat` | VARCHAR(50) | Bulunduğu kat |
| `bina_yasi` | INT | Bina yaşı |
| `isinma_tipi` | VARCHAR(100) | Isıtma türü |
| `tapu_durumu` | VARCHAR(100) | Tapu bilgisi |
| `konut_tipi` | VARCHAR(100) | Daire / villa vb. |
| `banyo_sayisi` | INT | Banyo sayısı |
| `kat_sayisi` | INT | Toplam kat |
| `krediye_uygun` | VARCHAR(20) | Evet / Hayır |
| `esya_durumu` | VARCHAR(50) | Eşya durumu |
| `konum` | TEXT | Adres / konum bilgisi |
| `url` | TEXT | İlan bağlantısı |

---

## ⚙️ Kurulum

### Ön Koşullar

| Araç | Versiyon |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| Angular CLI | 21+ |
| MySQL | 8.x |

---

### 1. Repoyu Klonlayın

```bash
git clone https://github.com/kullanici-adi/chatbot-angular.git
cd chatbot-angular
```

---

### 2. Backend Kurulumu

```bash
cd backend

# Sanal ortam oluşturun (önerilir)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

#### Ortam Değişkenleri

`.env.example` dosyasını kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin:

```dotenv
# Veritabanı
DATABASE_URL=mysql+pymysql://root:sifre@localhost:3306/emlak_db
MYSQL_URI=mysql+pymysql://root:sifre@localhost:3306/emlak_db

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4.1-mini

# Timeout (saniye)
LLM_TIMEOUT_SECONDS=120

# Langfuse (isteğe bağlı — observability)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

> **Not:** `LANGFUSE_*` değişkenleri tanımlanmamışsa gözlemlenebilirlik devre dışı kalır; uygulama normal çalışır.

#### Tabloları Oluşturun

```bash
# SQLAlchemy modelleri üzerinden otomatik tablo oluşturma
python -c "from database import Base, engine; from models import *; Base.metadata.create_all(engine)"
```

#### Backend'i Başlatın

```bash
uvicorn main:app --reload --port 8000
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 3. Frontend Kurulumu

```bash
cd ../realestate-chatbot

# Bağımlılıkları yükleyin
npm install

# Geliştirme sunucusunu başlatın
ng serve
```

Uygulama: [http://localhost:4200](http://localhost:4200)

---

## 🔌 API Referansı

### Kimlik Doğrulama

| Yöntem | Endpoint | Açıklama |
|---|---|---|
| `POST` | `/api/register` | Yeni kullanıcı kaydı |
| `POST` | `/api/login` | Kullanıcı girişi |
| `POST` | `/api/reset-password` | Şifre sıfırlama |

### Chat

| Yöntem | Endpoint | Açıklama |
|---|---|---|
| `POST` | `/api/chat/ask` | Agent'a soru sor (+ geçmişi kaydet) |
| `GET` | `/api/chat/{user_id}` | Tüm sohbet geçmişini getir |
| `GET` | `/api/chat/{user_id}/{conv_id}` | Belirli sohbeti getir |
| `POST` | `/api/chat` | Manuel mesaj kaydet |
| `POST` | `/api/chat/delete-messages` | Seçili mesajları sil |
| `DELETE` | `/api/chat/{user_id}` | Tüm sohbet geçmişini sil |

#### `POST /api/chat/ask` — İstek Gövdesi

```json
{
  "user_id": 1,
  "question": "Kadıköy'de 3+1 daire arıyorum, bütçem 10 milyon TL.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### `POST /api/chat/ask` — Yanıt

```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "Kadıköy'de 10 milyon TL altında 3 adet 3+1 ilan bulunuyor...",
  "user_message": { "id": 42, "role": "user", "content": "...", "created_at": "..." },
  "assistant_message": { "id": 43, "role": "assistant", "content": "...", "created_at": "..." }
}
```

---

## 🔐 Güvenlik

- Şifreler **bcrypt** ile hashlenir (maks. 72 karakter)
- Şifre politikası: en az 6 karakter, 1 büyük harf, 1 rakam (Pydantic validator)
- SQL Agent yalnızca **SELECT** sorgularına izin verir; DDL/DML yasaklıdır
- CORS yalnızca `localhost:4200`'e açıktır (production'da güncelleyin)
- Kullanıcı oturumu **sessionStorage**'da tutulur (sekme kapanınca sona erer)

---

## 🧩 Teknoloji Yığını

### Backend

| Paket | Amaç |
|---|---|
| FastAPI | REST API çerçevesi |
| SQLAlchemy | ORM ve DB bağlantısı |
| PyMySQL | MySQL sürücüsü |
| Passlib (bcrypt) | Şifre hashleme |
| Pydantic v2 | Veri doğrulama ve şemalar |
| LangChain | LLM araç zinciri |
| LangGraph | ReAct Agent döngüsü |
| langchain-openai | OpenAI bağlayıcısı |
| langchain-community | SQL Database Toolkit |
| Langfuse | LLM gözlemlenebilirliği |
| python-dotenv | Ortam değişkeni yönetimi |

### Frontend

| Paket | Amaç |
|---|---|
| Angular 21 | SPA çerçevesi |
| Angular Signals | Reaktif durum yönetimi |
| Angular HttpClient | HTTP istekleri |
| Angular Router | Sayfa yönlendirme |
| FormsModule | Form bağlama (ngModel) |
| SCSS | Stil |

---

## 🚀 Production Notları

- CORS ayarlarını `main.py`'de production domain'inize göre güncelleyin
- `AuthService` içindeki `apiUrl`'i production backend adresine yönlendirin
- Frontend için `ng build --configuration production` çalıştırın
- Backend için Gunicorn + Nginx önerilir:
  ```bash
  gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  ```
- Langfuse ile LLM maliyetlerini ve performansını izlemeyi etkinleştirin

---

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır.
