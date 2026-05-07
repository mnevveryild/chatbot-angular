# 🏠 Emlak Asistanı — AI Destekli Emlak Chatbot

> Yapay zeka ile hayalinizdeki evi keşfedin. Parmaklarınızın ucundaki akıllı emlak rehberi.

![Angular](https://img.shields.io/badge/Angular-21-DD0031?logo=angular&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-ReAct_Agent-blueviolet)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4.1--mini-412991?logo=openai&logoColor=white)

---

## 📌 Proje Hakkında

**Emlak Asistanı**, kullanıcıların Türkçe doğal dil sorularıyla emlak ilanı veritabanını sorgulayabildiği, AI destekli bir chatbot uygulamasıdır. Kullanıcılar mahalle, fiyat aralığı, oda sayısı veya ilan numarası gibi kriterlere göre ev arayabilir; ilan karşılaştırması yapabilir ve danışmanlık alabilir.

### Ekran Görüntüleri

| Giriş Ekranı | Sohbet Arayüzü |

<img width="1902" height="850" alt="login" src="https://github.com/user-attachments/assets/c1bbcb6b-7887-4ade-b3c4-44764d28be6e" />
</br>
 <img width="1896" height="848" alt="chat" src="https://github.com/user-attachments/assets/f5183b2a-7f81-4393-b7c7-f1c41b7cab1d" /> 

---

## ✨ Özellikler

- 🤖 **AI SQL Agent** — LangGraph ReAct mimarisiyle MySQL üzerinde akıllı sorgu yürütme
- 💬 **Gerçek Zamanlı Sohbet** — Konuşma geçmişi destekli, bağlam farkındalıklı yanıtlar
- 🔐 **Kullanıcı Yönetimi** — Kayıt, giriş ve şifre sıfırlama (bcrypt ile güvenli şifre saklama)
- 📁 **Sohbet Yönetimi** — Geçmiş sohbetleri listele, seç, sil ve yeniden başlat
- 🌙 **Karanlık / Açık Tema** — Tercih localStorage'a kaydedilir
- 📱 **Responsive Tasarım** — Masaüstü ve mobil uyumlu split-screen arayüz

---

## 🏗️ Mimari

```
chatbot-angular/
├── realestate-chatbot/          # Angular 21 — Frontend
│   └── src/app/
│       ├── login/               # Giriş / Kayıt / Şifre sıfırlama ekranı
│       ├── chat/                # Sohbet arayüzü (sidebar + mesaj alanı)
│       ├── auth.ts              # AuthService — kimlik doğrulama servisi
│       ├── chat.ts              # ChatService — sohbet ve konuşma yönetimi
│       └── app.routes.ts        # Sayfa yönlendirme
│
└── backend/                     # Python FastAPI — Backend
    ├── main.py                  # API endpoint'leri
    ├── agent.py                 # LangGraph ReAct SQL Agent
    ├── llm_provider.py          # OpenAI LLM yapılandırması
    ├── models.py                # SQLAlchemy veritabanı modelleri
    ├── schemas.py               # Pydantic şemaları
    ├── database.py              # Veritabanı bağlantısı
    └── config.py                # Ortam değişkeni ayarları
```

### Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Frontend | Angular 21 (Standalone Components, Signals API) |
| Backend | FastAPI + Uvicorn |
| Veritabanı | MySQL 8 + SQLAlchemy ORM |
| AI Agent | LangGraph `create_react_agent` + LangChain SQL Toolkit |
| LLM | OpenAI GPT-4.1-mini |
| Kimlik Doğrulama | Passlib (bcrypt) + SessionStorage |

---

## 🚀 Kurulum

### Gereksinimler

- Node.js ≥ 18
- Python ≥ 3.11
- MySQL 8
- OpenAI API anahtarı

---

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/mnevveryild/chatbot-angular.git
cd chatbot-angular
```

---

### 2. Backend Kurulumu

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

**`.env` dosyasını oluşturun:**

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini

MYSQL_URI=mysql+pymysql://kullanici:sifre@localhost:3306/emlak_db
DATABASE_URL=mysql+pymysql://kullanici:sifre@localhost:3306/emlak_db

LLM_TIMEOUT_SECONDS=120
```

**Veritabanını oluşturun:**

MySQL istemcisine bağlanarak `emlak_db` adında bir veritabanı ve `ilanlar` tablosu oluşturun. Agent yalnızca `ilanlar` tablosunu kullanır.

**Backend'i başlatın:**

```bash
uvicorn main:app --reload --port 8000
```

API arayüzüne erişmek için: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 3. Frontend Kurulumu

```bash
cd realestate-chatbot
npm install
ng serve
```

Uygulama [http://localhost:4200](http://localhost:4200) adresinde çalışacaktır.

---

## 📡 API Endpoint'leri

| Metot | Yol | Açıklama |
|---|---|---|
| `POST` | `/api/register` | Yeni kullanıcı kaydı |
| `POST` | `/api/login` | Kullanıcı girişi |
| `POST` | `/api/reset-password` | Şifre sıfırlama |
| `POST` | `/api/chat/ask` | AI'ya soru gönderme (agent çalıştırma) |
| `GET` | `/api/chat/{user_id}` | Kullanıcının tüm sohbet geçmişini getirme |
| `GET` | `/api/chat/{user_id}/{conv_id}` | Belirli bir konuşmayı getirme |
| `POST` | `/api/chat/delete-messages` | Belirtilen mesajları silme |
| `DELETE` | `/api/chat/{user_id}` | Tüm sohbet geçmişini silme |

---

## 🤖 AI Agent Nasıl Çalışır?

Backend, **LangGraph ReAct** mimarisi üzerine kurulu bir SQL Ajanı kullanır:

1. Kullanıcının sorusu ve önceki konuşma geçmişi (`HumanMessage` / `AIMessage`) birlikte ajana iletilir.
2. Ajan, `LangChain SQL Toolkit` araçlarıyla (`sql_db_query`, `sql_db_query_checker`, `sql_db_schema`, `sql_db_list_tables`) MySQL veritabanını inceler.
3. Gerekirse sorguyu çalıştırmadan önce `sql_db_query_checker` ile doğrular; hata alırsa kendisi düzelterek yeniden dener.
4. Yalnızca `SELECT` sorguları çalıştırmasına izin verilir; `INSERT`, `UPDATE`, `DELETE`, `DROP` gibi sorgular sistem istemiyle yasaklanmıştır.
5. Ajan yanıtı Türkçe, sade ve kullanıcı odaklı biçimde üretir.

---

## 🔒 Güvenlik Notları

- Parolalar **bcrypt** ile hashlenerek saklanır (plain text saklanmaz).
- Kullanıcı oturumu `sessionStorage` ile yönetilir; tarayıcı kapandığında oturum sona erer.
- Backend, `CORS` middleware ile yalnızca `localhost:4200`'den gelen istekleri kabul eder (production'da güncellenmelidir).
- SQL Ajanı; `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` komutlarını sistem istemiyle kısıtlar.

---

## 🗂️ Veritabanı Şeması (ilanlar tablosu)

Agent'ın kullandığı `ilanlar` tablosunun beklenen sütunları:

| Sütun | Açıklama |
|---|---|
| `ilan_no` | Benzersiz ilan numarası |
| `baslik` | İlan başlığı |
| `fiyat` | İlan fiyatı (TL) |
| `oda_sayisi` | Oda sayısı (örn. 3+1) |
| `m2` | Net metrekare |
| `bulundugu_kat` | Bulunduğu kat |
| `konum` | Konum (il / ilçe / mahalle) |
| `url` | Orijinal ilan bağlantısı |
| `bina_yasi` | Bina yaşı |
| `isinma_tipi` | Isınma tipi |
| `tapu_durumu` | Tapu durumu |
| `konut_tipi` | Konut tipi |
| `banyo_sayisi` | Banyo sayısı |
| `kat_sayisi` | Toplam kat sayısı |
| `krediye_uygun` | Krediye uygunluk durumu |
| `esya_durumu` | Eşya durumu |

---

## 📝 Geliştirme Notları

- Frontend **Angular Signals API** kullanır; `signal()`, `computed()` ve `effect()` tercih edilmiştir.
- `ChatService`, `sessionStorage`'dan kullanıcı bilgisini okuyarak sayfa yenilemelerinde oturumu korur.
- Sohbet başlığı, ilk kullanıcı mesajından otomatik türetilir; ilan numarası içeriyorsa `İlan XXXXX` biçiminde adlandırılır.
- `Shift+Enter` yeni satır, `Enter` mesaj gönderme işlevi görür.

---

## 🤝 Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

---

## 📄 Lisans

Bu proje [ISC](LICENSE) lisansı ile lisanslanmıştır.

---

<p align="center">
  <i>AI ile hayalinizdeki evi keşfedin. 🏡</i>
</p>
