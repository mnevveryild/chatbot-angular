from config import settings


def build_llm():
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY .env dosyasinda tanimli degil.")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "OpenAI icin langchain-openai paketi gerekli. "
            "Kurulum: pip install -r backend/requirements.txt"
        ) from exc

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
        timeout=settings.llm_timeout_seconds,
    )
