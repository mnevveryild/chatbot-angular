import { Injectable, signal, computed } from '@angular/core';
import { Router } from '@angular/router';

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  // Private signal: Sadece bu servis içinde değiştirilebilir
  private _currentUser = signal<User | null>(null);
  
  // Public readonly signals: Dışarıdan sadece okunabilir
  currentUser = this._currentUser.asReadonly();
  
  // isLoggedIn değerini currentUser'a bağlı otomatik hesaplanan bir değer yapmak daha sağlıklıdır.
  isLoggedIn = computed(() => !!this._currentUser());

  constructor(private router: Router) {
    this.initializeAuth();
  }

  private initializeAuth(): void {
    const stored = sessionStorage.getItem('re_user');
    if (stored) {
      try {
        const user = JSON.parse(stored);
        this._currentUser.set(user);
      } catch (e) {
        console.error('Kullanıcı verisi ayrıştırılamadı:', e);
        sessionStorage.removeItem('re_user');
      }
    }
  }

  async login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    // API simülasyonu için küçük bir gecikme 
    await new Promise(resolve => setTimeout(resolve, 800));

    if (email && password.length >= 6) {
      const user: User = {
        id: crypto.randomUUID(),
        email,
        name: email.split('@')[0]// Basitçe e-posta'nın @ öncesini isim olarak kullanıyoruz
      };
      
      this.setSession(user);
      return { 
        success: true 
      };
    }

    return { 
      success: false, 
      error: 'Geçersiz kimlik bilgileri. Lütfen tekrar deneyin.' 
    };
  }

  async register(
    name: string, 
    email: string, 
    password: string): Promise<{ 
    success: boolean; 
    error?: string }> {
        
    await new Promise(resolve => setTimeout(resolve, 800));

    if (name && email && password.length >= 6) {
      const user: User = {
        id: crypto.randomUUID(),
        email,
        name
      };
      
      this.setSession(user);
      return { success: true };
    }

    return { 
      success: false, 
      error: 'Lütfen tüm alanları doldurun. Şifre en az 6 karakter olmalıdır.' 
    };
  }

  private setSession(user: User): void {
    this._currentUser.set(user);
    sessionStorage.setItem('re_user', JSON.stringify(user));
  }

  logout(): void {
    this._currentUser.set(null);
    sessionStorage.removeItem('re_user');
    this.router.navigate(['/login']);
  }
}