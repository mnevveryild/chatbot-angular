import { Component, signal, ViewChild, ElementRef, AfterViewChecked, effect } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from '../auth';
import { ChatService, Conversation } from '../chat';
import { Router } from '@angular/router';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './chat.html',
  styleUrl: './chat.scss'
})
export class ChatComponent implements AfterViewChecked {
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;
  
  inputText = '';
  sidebarOpen = signal(true); // Yan menü açık/kapalı durumu
  confirmDeleteId = signal<string | null>(null); // Silme onayı bekleyen sohbet ID'si
// dışarıdan erişim için servisler ve router
  constructor(
    public auth: AuthService,
    public chatService: ChatService,
    private router: Router
  ) {
    // Aktif sohbet değiştiğinde otomatik olarak en aşağı kaydır
    effect(() => {
      const conv = this.chatService.activeConversation();
      if (conv) this.scrollToBottom();
    });
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  private scrollToBottom() {
    try { 
      this.messagesEnd?.nativeElement?.scrollIntoView({ behavior: 'smooth' }); 
    } catch {}
  }

  sendMessage() {
    if (!this.inputText.trim()) return;
    
    // Eğer seçili bir sohbet yoksa yeni bir tane başlat
    if (!this.chatService.activeConversation()) {
      this.chatService.newConversation();
    }
    
    this.chatService.sendMessage(this.inputText);
    this.inputText = '';
  }

  onKeydown(e: KeyboardEvent) {
    // Shift+Enter ile alt satıra geçmeye izin ver, sadece Enter ile gönder
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  selectConv(id: string) { this.chatService.selectConversation(id); }
  newConv() { this.chatService.newConversation(); }
  logout() { this.auth.logout(); }
  toggleSidebar() { this.sidebarOpen.update(v => !v); }

  confirmDelete(id: string, e: Event) {
    e.stopPropagation(); // Tıklamanın sohbete geçmesini engelle
    this.confirmDeleteId.set(id);
  }

  cancelDelete() { this.confirmDeleteId.set(null); }

  doDelete(id: string) {
    this.chatService.deleteConversation(id);
    this.confirmDeleteId.set(null);
  }

  formatTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    
    if (diff < 60000) return 'Az önce';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}dk önce`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}sa önce`;
    
    return new Date(date).toLocaleDateString('tr-TR');
  }

  getSuggestions() {
    return [
      '2 milyon dolar altı lüks evleri bul',
      'Ankara mahallelerini karşılaştır',
      'Güncel kredi faiz oranları nedir?',
      'Evcil hayvan dostu daireleri göster'
    ];
  }

  useSuggestion(text: string) {
    this.inputText = text;
    this.sendMessage();
  }

  getUserInitials(): string {
    const name = this.auth.currentUser()?.name ?? '';
    if (!name) return '??';
    return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
  }
}