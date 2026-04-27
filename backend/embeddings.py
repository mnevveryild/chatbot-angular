from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from database import get_all_listings, listing_to_text
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

VECTORSTORE_PATH = "faiss_index"

def build_vectorstore():
    """MySQL'deki ilanları embedding'e çevirip FAISS'e kaydet."""
    print("📦 İlanlar MySQL'den yükleniyor...")
    listings = get_all_listings()
    print(f"✅ {len(listings)} ilan bulundu.")

    documents = []
    for listing in listings:
        content = listing_to_text(listing)
        doc = Document(
            page_content=content,
            metadata={"id": listing.get("id"), "sehir": listing.get("sehir")}
        )
        documents.append(doc)

    print("🔄 Embedding oluşturuluyor (bu biraz sürebilir)...")
    embeddings = OllamaEmbeddings(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL
    )

    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(VECTORSTORE_PATH)
    print(f"✅ Vektör veritabanı '{VECTORSTORE_PATH}' klasörüne kaydedildi.")
    return vectorstore


def load_vectorstore():
    """Kaydedilmiş FAISS index'i yükle."""
    embeddings = OllamaEmbeddings(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    return FAISS.load_local(
        VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )