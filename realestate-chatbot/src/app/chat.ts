import { Injectable, signal } from '@angular/core';

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

@Injectable({ providedIn: 'root' })
export class ChatService {
  private _conversations = signal<Conversation[]>([]);
  private _activeConversation = signal<Conversation | null>(null);
  private _isTyping = signal(false);

  // Dışarıdan sadece okunabilir signaller
  conversations = this._conversations.asReadonly();
  activeConversation = this._activeConversation.asReadonly();
  isTyping = this._isTyping.asReadonly();

  selectConversation(id: string) {
    const found = this._conversations().find(c => c.id === id) ?? null;
    this._activeConversation.set(found);
  }

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

  sendMessage(content: string) {
    if (!content.trim()) return;
    
    // 1. Kullanıcı mesajını oluştur
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    };

    // 2. Kullanıcı mesajını aktif sohbete ekle
    this._activeConversation.update(conv => {
      if (!conv) return conv;
      const updated: Conversation = {
        ...conv,
        messages: [...conv.messages, userMsg],
        lastMessage: content.trim(),
        title: conv.title === 'Yeni Sohbet' && conv.messages.length === 0
          ? content.slice(0, 40) + (content.length > 40 ? '...' : '')
          : conv.title,
        timestamp: new Date()
      };
      
      this._conversations.update(list =>
        list.map(c => c.id === updated.id ? updated : c)
      );
      return updated;
    });

    // 3. Bot "yazıyor" durumunu aktif et
    this._isTyping.set(true);

    // 4. Burayı kendi API çağrımız ile değiştireceğiz
    setTimeout(() => {
      const botMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'vfhngjkmcdmjvfnhgkmdccmjfvnhgkmcdcmdjvfg', // Buraya API'den dönen text gelecek
        timestamp: new Date()
      };

      // Yazıyor durumunu kapat
      this._isTyping.set(false);
      
      // Bot mesajını aktif sohbete ekle
      this._activeConversation.update(conv => {
        if (!conv) return conv;
        const updated: Conversation = { 
          ...conv, 
          messages: [...conv.messages, botMsg], 
          lastMessage: botMsg.content, 
          timestamp: new Date() 
        };
        
        this._conversations.update(list => list.map(c => c.id === updated.id ? updated : c));
        return updated;
      });

    });
  }

  deleteConversation(id: string) {
    // 1. Gereksiz Signal tetiklemelerini önlemek için sohbetin var olup olmadığını kontrol et
    const hasConversation = this._conversations().some(c => c.id === id);
    if (!hasConversation) return;

    // 2. İlgili sohbeti listeden çıkararak listeyi güncelle
    this._conversations.update(list => list.filter(c => c.id !== id));

    // 3. Eğer silinen sohbet, kullanıcının şu an aktif olarak baktığı sohbetse durumu yönet
    if (this._activeConversation()?.id === id) {
      const remainingConversations = this._conversations();
      
      // Geriye başka sohbetler kaldıysa ilkini aktif yap, kalmadıysa ekranı boş (null) duruma getir
      this._activeConversation.set(remainingConversations.length > 0 ? remainingConversations[0] : null);
    }
  }
}