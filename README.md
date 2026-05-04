<img width="1918" height="852" alt="image" src="https://github.com/user-attachments/assets/062a7160-9435-493f-80ca-ea4fc2f3ecfc" />

## Backend LLM Ayarlari

ChatGPT/OpenAI API ile calistirmak icin:

1. `backend/.env` dosyasinda `OPENAI_API_KEY=` satirina kendi API key degerini yaz.
2. Istersen modeli `OPENAI_MODEL=gpt-4.1-mini` yerine baska bir OpenAI modeliyle degistir.
3. MySQL baglantisini `MYSQL_URI=` veya `DATABASE_URL=` ile ayarla.
4. Backend bagimliliklarini kur:

```powershell
pip install -r backend/requirements.txt
```

5. Backend'i calistir:

```powershell
cd backend
uvicorn main:app --reload
```

Backend, LangChain ve LangGraph tabanli SQL agent kullanir. Agent `ilanlar`
tablosunu inceler, ilanlari yapay bir sayi limiti olmadan sorgular ve tek ilan
detay sorularinda onceki sohbet baglamindaki ilan no bilgisini kullanabilir.

## LangSmith Ayarlari

Agent trace'lerini LangSmith'te izlemek icin `backend/.env` dosyasina sunlari ekle:

```powershell
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=realestate-chatbot
```

Backend LangChain/LangGraph kullandigi icin bu degiskenler aktif oldugunda agent
calismalari otomatik trace edilir. Agent cagrilarina `realestate-sql-agent` run
adi, `realestate/sql-agent/chatbot` tag'leri ve sohbet metadata bilgileri eklenir.

## Langfuse Ayarlari

Agent trace'lerini Langfuse'ta izlemek icin `backend/.env` dosyasina sunlari ekle:

```powershell
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

US region kullaniyorsan `LANGFUSE_HOST=https://us.cloud.langfuse.com` yap.
Backend, bu key'ler tanimliyken LangChain/LangGraph agent calismalarina Langfuse
callback'i ekler. Trace'lerde `realestate-sql-agent` run adi, sohbet tag'leri,
`langfuse_user_id` ve `langfuse_session_id` metadata alanlari gonderilir.
