from langchain_ollama import ChatOllama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate 
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

SYSTEM_PROMPT = """Sen bir Türkçe emlak danışmanısın. 
Sana verilen ev ilanı bilgilerini kullanarak kullanıcıların sorularını yanıtla.
Sadece verilen ilanlar hakkında konuş. Bilmediğin bir şeyi uydurma.
Fiyat karşılaştırması, bölge önerisi ve ilan detayları konusunda yardımcı ol.

Bağlam (İlan Bilgileri):
{context}

Sohbet Geçmişi:
{chat_history}

Kullanıcı Sorusu: {question}

Yanıt:"""

prompt = PromptTemplate(
    input_variables=["context", "chat_history", "question"],
    template=SYSTEM_PROMPT
)


def create_chatbot(vectorstore):
    """RAG tabanlı chatbot oluştur."""
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.3,       # Daha tutarlı yanıtlar için düşük tutuyoruz
        num_predict=1024,
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # En benzer 5 ilanı getir
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=False
    )

    return chain


def chat(chain, user_input: str) -> str:
    """Kullanıcı mesajını işle, yanıt döndür."""
    result = chain.invoke({"question": user_input})
    return result["answer"]