import { Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _currentUser = signal<User | null>(null);
  currentUser = this._currentUser.asReadonly();
  isLoggedIn = signal(false);

  constructor(private router: Router) {
    this.restoreSession();
  }

  // --- YARDIMCI METODLAR (DRY Prensibi İçin) ---

  private restoreSession(): void {
    const stored = sessionStorage.getItem('re_user');
    if (stored) {
      try {
        const user: User = JSON.parse(stored);
        this._currentUser.set(user);
        this.isLoggedIn.set(true);
      } catch (error) {
        // Eğer sessionStorage'daki veri bozulmuşsa (geçersiz JSON vb.), oturumu temizle
        console.error('Oturum verisi okunamadı, temizleniyor...', error);
        this.clearSession();
      }
    }
  }

  private setSession(user: User): void {
    this._currentUser.set(user);
    this.isLoggedIn.set(true);
    sessionStorage.setItem('re_user', JSON.stringify(user));
  }

  private clearSession(): void {
    this._currentUser.set(null);
    this.isLoggedIn.set(false);
    sessionStorage.removeItem('re_user');
  }

  // --- TEMEL İŞLEVLER ---

  login(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    return new Promise(resolve => {
      // API çağrısını simüle etmek için 500ms gecikme
      setTimeout(() => {
        if (!email || password.length < 6) {
          return resolve({ success: false, error: 'Geçersiz kimlik bilgileri. Lütfen tekrar deneyin.' });
        }

        const user: User = {
          id: crypto.randomUUID(),
          email,
          name: email.split('@')[0]
        };

        this.setSession(user);
        resolve({ success: true });
      }); 
    });
  }

  register(name: string, email: string, password: string): Promise<{ success: boolean; error?: string }> {
    return new Promise(resolve => {
      setTimeout(() => {
        if (!name || !email || password.length < 6) {
          return resolve({ success: false, error: 'Lütfen tüm alanları doldurun. Şifre en az 6 karakter olmalıdır.' });
        }
        
        const user: User = {
          id: crypto.randomUUID(),
          email,
          name
        };

        this.setSession(user);
        resolve({ success: true });
      });
    });
  }

  logout(): void {
    this.clearSession();
    this.router.navigate(['/login']);
  }
}