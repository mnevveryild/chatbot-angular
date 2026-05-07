import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from config import settings
from llm_provider import build_llm


llm = build_llm()


agent_db = SQLDatabase.from_uri(
    settings.mysql_uri,
    include_tables=["ilanlar"],
    sample_rows_in_table_info=5,
    view_support=True,          # VIEW'ları da tablo gibi tanı (ilanlar bir VIEW'dır)
    engine_args={
        "pool_recycle": 3600,  # Bağlantıyı 1 saatte bir yenile
        "pool_pre_ping": True  # İşlemden önce bağlantının hayatta olup olmadığını kontrol et
    }
)

toolkit = SQLDatabaseToolkit(db=agent_db, llm=llm)
tools = toolkit.get_tools()

SYSTEM_PROMPT = SystemMessage(
    content="""
Sen MySQL'deki emlak ilanlarini inceleyen, kullaniciyla Turkce ve akilli sekilde
konusan bir emlak danismanisin. Veritabani tarafinda yalnizca ilanlar tablosunu
kullan.

Temel kurallar:
- Yalnizca SELECT sorgulari kullan. INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE yasak.

- Sorguyu calistirmadan once sql_db_query_checker araci ile kontrol et.

- Cevapta teknik SQL detaylarini anlatma; kullanicinin niyetine dogrudan yanit ver.

- Kullanici bir ilan no/id sorarsa veya onceki mesajdaki bir ilana "bu ilan",
  "o ilan", "detaylarini ver" gibi ifadelerle donerse konusma gecmisinden
  ilgili ilan no'yu yakala ve o ilani detayli acikla. O ilan hakkinda sorular sorarsa
  gecmisi kullanarak hangi ilana atif yapildigini bul ve o ilan uzerinden cevapla.

- Ilan no/id aramalarinda once ilan_no alaninda birebir eslesme dene. Sonuc
  yoksa kullanicinin yazdigi degeri temizleyip bosluk, tire, nokta gibi ayiraclari
  kaldirarak tekrar ara; ilan_no metin alani oldugu icin sayiya cevirmeye calisma.

- Konum, mahalle, baslik, oda sayisi veya genel ozellik aramalarinda ilk sorgu
  sonuc vermezse "veritabaninda yok" demeden once mutlaka daha esnek ikinci bir
  arama yap: baslik ve konum alanlarinda LOWER(...) LIKE '%kelime%' kullan,
  kullanicinin tum cumlesini degil anlamli anahtar kelimeleri ayri ayri ara.

- Turkce karakter ve yazim farklari olabilecegini varsay. Ornegin kullanici
  "cankaya" yazarsa hem "Cankaya" hem "Çankaya" ihtimalini kapsayacak sekilde
  LOWER(alan) LIKE '%...%' veya genis LIKE kosullari kullan.

- Filtreli aramada sonuc yoksa once en dar filtreyi gevseterek yakindaki
  eslesmeleri kontrol et. Ancak bu genis arama da sonuc vermezse "bulamadim" de.

- Ilan listelerken veya tek ilan detayi verirken sonuc sayisi icin yapay LIMIT
  koyma. Kullanici kendisi sayi, fiyat araligi, mahalle, oda sayisi gibi filtre
  belirtirse sadece o filtreleri uygula.

- Ilan bilgisini saklama, uydurma veya eksiltme. Veritabaninda olan tum onemli
  alanlari kullan: ilan_no, baslik, fiyat, oda_sayisi, m2, bulundugu_kat, konum, url.
  Eger kullanici detayli bilgi isterse diger alanlari da kullan: bina_yasi,
  isinma_tipi, tapu_durumu, konut_tipi, banyo_sayisi, kat_sayisi,
  krediye_uygun, esya_durumu.

- Bir alan bos veya NULL ise bunu "belirtilmemis" diye soyle.

- Karsilastirma, yorum veya tavsiye istenirse fiyat/m2, oda sayisi, konum,
  kat, bina yasi, banyo, kredi uygunlugu ve esya durumunu birlikte degerlendir.

- Kullanici ilan hakkinda sohbet etmek isterse sadece veri dokmekle kalma;
  artisini, eksisini, kimler icin uygun olabilecegini ve dikkat edilmesi gereken
  noktalarini veriye dayanarak yorumla.

=== VERITABANI ALAN BILGILERI ===

konum alani formati: "Ankara / Ilce / Mahalle Mah."
Ornek: "Ankara / Keçiören / Basınevleri Mah.", "Ankara / Çankaya / Kızılırmak Mah."
Arama: WHERE konum LIKE '%IlceAdi%'

oda_sayisi alani: "3+1", "2+1", "4+2" gibi standart formatta.
Arama: WHERE oda_sayisi = '3+1' veya WHERE oda_sayisi LIKE '%3+1%'

baslik alani: "Satılık Daire - Ankara / Ilce / Mahalle Mah." formatinda.

"""
)


agent_executor = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)

# DÜZELTME: max_workers=2 kısıtlaması kaldırıldı. 
# Böylece thread pool kilitlenmelerinin (starvation) önüne geçildi.
llm_executor = ThreadPoolExecutor()


def _build_callbacks():
    callbacks = []

    if (
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    ):
        if os.getenv("LANGFUSE_BASE_URL") and not os.getenv("LANGFUSE_HOST"):
            os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_BASE_URL", "")

        try:
            from langfuse.langchain import CallbackHandler
        except ImportError as exc:
            raise RuntimeError(
                "Langfuse icin langfuse paketi gerekli. "
                "Kurulum: pip install -r backend/requirements.txt"
            ) from exc

        callbacks.append(CallbackHandler())

    return callbacks


def flush_observability() -> None:
    if (
        not os.getenv("LANGFUSE_PUBLIC_KEY")
        or not os.getenv("LANGFUSE_SECRET_KEY")
    ):
        return

    try:
        from langfuse import get_client
    except ImportError:
        return

    get_client().flush()


def _to_agent_messages(history: list[tuple[str, str]], question: str) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for role, content in history:
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=question))
    return messages


def run_agent(
    question: str,
    history: list[tuple[str, str]] | None = None,
    user_id: int | None = None,
    conversation_id: str | None = None,
) -> str:
    def _invoke() -> str:
        metadata = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "database_table": "ilanlar",
            "langfuse_user_id": str(user_id) if user_id is not None else None,
            "langfuse_session_id": conversation_id,
        }
        result = agent_executor.invoke(
            {"messages": _to_agent_messages(history or [], question)},
            config={
                "run_name": "realestate-sql-agent",
                "tags": ["realestate", "sql-agent", "chatbot"],
                "metadata": metadata,
                "callbacks": _build_callbacks(),
            },
        )

        final_message = result["messages"][-1]
        return final_message.content if hasattr(final_message, "content") else str(final_message)

    future = llm_executor.submit(_invoke)
    try:
        answer = future.result(timeout=settings.llm_timeout_seconds)
    except FutureTimeoutError as exc:
        raise TimeoutError(
            f"Agent {settings.llm_timeout_seconds} saniye icinde cevap vermedi. "
            "OpenAI model ve API ayarlarini kontrol edin."
        ) from exc

    if not answer or not answer.strip():
        raise ValueError("Agent bos cevap dondurdu.")

    return answer.strip()
