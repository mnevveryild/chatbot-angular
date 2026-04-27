import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface Message {
  id?: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messages: Message[];
}

@Injectable({ 
  providedIn: 'root' 
})
export class ChatService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000/api/chat';

  private currentUserId = signal<number | null>(null);

  private _conversations = signal<Conversation[]>([]);
  private _activeConversation = signal<Conversation | null>(null);
  private _isTyping = signal(false);

  conversations = this._conversations.asReadonly();
  activeConversation = this._activeConversation.asReadonly();
  isTyping = this._isTyping.asReadonly();


  // kullanıcı oturumu kontrolü, sayfa yenilense bile sessionStorage'dan kullanıcı bilgisi yükle
  constructor() {
    const stored = sessionStorage.getItem('re_user');
  if (stored) {
    try {
      const user = JSON.parse(stored);
      if (user?.id) {
        if (this.currentUserId() !== Number(user.id)) {
          this.setUserId(Number(user.id));
        }
      }
    } catch (e) {
      console.error('Kullanıcı verisi okunamadı:', e);
    }
  }
}


 // Yeni kullanıcı için önce eski veriyi temizle ve ardından yeni kullanıcı ID'sini yükle
  setUserId(id: number) {
  this._conversations.set([]);
  this._activeConversation.set(null);
  this.currentUserId.set(id);
  this.loadAllConversations(id);
}


// Kullanıcı çıkış yaparken tüm sohbet verilerini temizle
  clearSession() {
  this._conversations.set([]);
  this._activeConversation.set(null);
  this.currentUserId.set(null);
}

  async loadAllConversations(userId: number) {
    try {
      const history = await firstValueFrom( 
        this.http.get<any[]>(`${this.apiUrl}/${userId}`)
      );

      if (history.length === 0) {
        this.newConversation();
        return;
      }


// conversation_id'ye göre gruplandır
      const grouped = new Map<string, any[]>();
      for (const item of history) {
        if (!grouped.has(item.conversation_id)) {
          grouped.set(item.conversation_id, []);
        }
        grouped.get(item.conversation_id)!.push(item);
      }


// Her grup için Conversation oluştur
      const conversations: Conversation[] = [];
      grouped.forEach((messages, convId) => {
        const mapped: Message[] = messages.map(item => ({
          id: item.id,
          role: item.role,
          content: item.content,
          timestamp: new Date(item.created_at)
        }));
// mesaj içeriğinden başlık oluştur, son mesajı ve tarihini alarak conversation objesine ekle
        conversations.push({
          id: convId,
          title: mapped[0]?.content.slice(0, 30) || 'Sohbet',
          lastMessage: mapped[mapped.length - 1]?.content || '',
          timestamp: new Date(messages[messages.length - 1].created_at),
          messages: mapped
        });
      });



      //son mesaj tarihine göre sırala
      conversations.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

      this._conversations.set(conversations);
      this._activeConversation.set(conversations[0] ?? null);

    } catch (error) {
      console.error('Sohbet geçmişi yüklenemedi:', error);
      this.newConversation();
    }
  }



  async sendMessage(content: string) {
    const userId = this.currentUserId();
    if (!userId) {
      console.error('Kullanıcı ID bulunamadı.');
      return;
    }

    // aktif sohbet yoksa otomatik yeni sohbet aç
    if (!this._activeConversation()) {
      this.newConversation();
    }

    const activeConv = this._activeConversation();
    if (!activeConv) return;

    const cleanContent = content.trim();
    if (!cleanContent) return;

    const userMsg: Message = {
      role: 'user',
      content: cleanContent,
      timestamp: new Date()
    };
    this.updateLocalMessages(userMsg);

    try {
      await firstValueFrom(this.http.post(this.apiUrl, {
        user_id: userId,
        conversation_id: activeConv.id,
        role: 'user',
        content: cleanContent
      }));

      this._isTyping.set(true);

      setTimeout(async () => {
        const botResponseContent = "...kayıt kontrol...";
        const botMsg: Message = {
          role: 'assistant',
          content: botResponseContent,
          timestamp: new Date()
        };

        await firstValueFrom(this.http.post(this.apiUrl, {
          user_id: userId,
          conversation_id: activeConv.id,
          role: 'assistant',
          content: botResponseContent
        }));

        this._isTyping.set(false);
        this.updateLocalMessages(botMsg);
      }, 1000);

    } catch (error) {
      console.error('Mesaj gönderimi başarısız:', error);
      this._isTyping.set(false);
    }
  }


  // se.ilen sohbet ekrana getir, mesajları yükle ve aktif sohbet olarak ayarla
  selectConversation(id: string) {
    const found = this._conversations().find(c => c.id === id) ?? null;
    this._activeConversation.set(found);
  }


  // sohbet silme, önce mesajları sil sonra sohbeti kaldır
  deleteConversation(id: string) {
    const conv = this._conversations().find(c => c.id === id);
    if (!conv) return;

    const messageIds = conv.messages
      .map(m => m.id)
      .filter((mid): mid is number => mid !== undefined);

    if (messageIds.length === 0) {
      this._conversations.update(list => list.filter(c => c.id !== id));
      if (this._activeConversation()?.id === id) {
        this._activeConversation.set(null);
      }
      return;
    }

    firstValueFrom(
      this.http.post(`${this.apiUrl}/delete-messages`, {
        message_ids: messageIds
      })
    ).then(() => {
      this._conversations.update(list => list.filter(c => c.id !== id));
      if (this._activeConversation()?.id === id) {
        // Silinen sohbet aktifse bir sonrakine geç, yoksa yeni sohbet aç
        const remaining = this._conversations();
        if (remaining.length > 0) {
          this._activeConversation.set(remaining[0]);
        } else {
          this.newConversation();
        }
      }
    }).catch(error => {
      console.error('Mesajlar silinemedi:', error);
    });
  }



  // yeni sohbet oluştur, benzersiz ID üret, boş mesaj listesi ile başlat ve aktif sohbet yap
  newConversation() {
    const conv: Conversation = {
      id: crypto.randomUUID(),
      title: 'Yeni Sohbet',
      lastMessage: '',
      timestamp: new Date(),
      messages: []
    };
    this._conversations.update(list => [conv, ...list]);
    this._activeConversation.set(conv);
  }


// yeni mesaj geldiğinde aktif sohbeti güncelle, mesajı ekle, son mesajı ve tarihi güncelle, ardından tüm sohbetler listesini de güncelle
  private updateLocalMessages(msg: Message) {
    this._activeConversation.update(conv => {
      if (!conv) return null;
      const updated = {
        ...conv,
        messages: [...conv.messages, msg],
        lastMessage: msg.content,
        timestamp: new Date()
      };

      this._conversations.update(list =>
        list.map(c => c.id === updated.id ? updated : c)
      );
      return updated;
    });
  }
}