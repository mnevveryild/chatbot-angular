import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { AuthService } from './auth';

export interface Message {
  id: string;
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
  private apiUrl = 'http://localhost:4200/api/chat';

  
  private _conversations = signal<Conversation[]>([]);
  private _activeConversation = signal<Conversation | null>(null);
  private _isTyping = signal(false);

  // Dışarıdan sadece okunabilir signaller
  conversations = this._conversations.asReadonly();
  activeConversation = this._activeConversation.asReadonly();
  isTyping = this._isTyping.asReadonly();

  constructor() {
    // Uygulama başladığında mevcut kullanıcının geçmişini yükle
    // Not: userId'yi normalde AuthService'den almalısın
    this.loadHistoryFromApi(1);
  }

  async loadHistoryFromApi(userId: number) {
    try {
      const history = await firstValueFrom(
        this.http.get<any[]>(`${this.apiUrl}/history/${userId}`)
      );

      const loadedMessages: Message[] = history.map(item => ({
        id: item.id,
        role: item.role,
        content: item.content,
        timestamp: new Date(item.created_at)
      }));

      const defaultConv: Conversation = {
        id: 'default-session',
        title: 'Genel Sohbet',
        lastMessage: loadedMessages[loadedMessages.length - 1]?.content || '',
        timestamp: new Date(),
        messages: loadedMessages
      };

      this._conversations.set([defaultConv]);
      this._activeConversation.set(defaultConv);
    } catch (error) {
      console.error('Mesaj geçmişi yüklenirken hata oluştu:', error);
    }
  }

  // Mesaj Gönderme (Signal + API Entegrasyonu)
  async sendMessage(content: string, userId: number) {
    if (!content.trim()) return;

    // Arayüzde hemen görünmesi için geçici kullanıcı mesajı
    const userMsg: Message = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    };

    // UI'ı anlık güncelle
    this.updateLocalMessages(userMsg);

    try {
      // API'ye Kaydet (POST)
      const saveRequest = {
        user_id: userId,
        role: 'user',
        content: content.trim()
      };

      await firstValueFrom(this.http.post(this.apiUrl, saveRequest));

      // Bot yanıtı simülasyonu (Veya gerçek AI API çağrın)
      this._isTyping.set(true);
      
      // Örnek Bot Yanıtı
      setTimeout(async () => {
        const botResponseContent = "Bu veritabanına kaydedilen bir cevaptır.";
        
        const botMsg: Message = {
          role: 'assistant',
          content: botResponseContent,
          timestamp: new Date()
        };

        // Bot cevabını da DB'ye kaydet
        await firstValueFrom(this.http.post(this.apiUrl, {
          user_id: userId,
          role: 'assistant',
          content: botResponseContent
        }));

        this._isTyping.set(false);
        this.updateLocalMessages(botMsg);
      }, 1000);

    } catch (error) {
      console.error('Mesaj gönderilirken hata oluştu:', error);
      this._isTyping.set(false);
    }
  }
// Local Signal güncelleme yardımcı fonksiyonu
  private updateLocalMessages(msg: Message) {
    this._activeConversation.update(conv => {
      if (!conv) return conv;
      const updated: Conversation = {
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

  // Sohbet Seçme
  selectConversation(id: string) {
    const found = this._conversations().find(c => c.id === id) ?? null;
    this._activeConversation.set(found);
  }

  // Yeni Sohbet Başlatma (Local)
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
}