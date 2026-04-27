import os
from embeddings import build_vectorstore, load_vectorstore, VECTORSTORE_PATH
from chatbot import create_chatbot, chat

def main():
    print("🏠 Ev İlan Chatbotu Başlatılıyor...\n")

    # FAISS index daha önce oluşturulduysa yükle, yoksa oluştur
    if os.path.exists(VECTORSTORE_PATH):
        print("📂 Mevcut vektör veritabanı yükleniyor...")
        vectorstore = load_vectorstore()
    else:
        vectorstore = build_vectorstore()

    chain = create_chatbot(vectorstore)

    print("\n✅ Chatbot hazır! Çıkmak için 'q' yazın.\n")
    print("─" * 50)

    while True:
        user_input = input("Sen: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ["q", "quit", "çıkış", "exit"]:
            print("Görüşmek üzere! 👋")
            break

        print("Bot: ", end="", flush=True)
        response = chat(chain, user_input)
        print(response)
        print("─" * 50)


if __name__ == "__main__":
    # Eğer ilanlar güncellenirse index'i yeniden oluşturmak için:
    # import sys
    # if "--rebuild" in sys.argv:
    #     build_vectorstore()
    main()