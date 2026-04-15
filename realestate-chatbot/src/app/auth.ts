import { Injectable, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar?: string;
}

export interface RegisterResponse {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
}

export interface LoginResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

@Injectable({ providedIn: 'root' })
export class AuthService {

  private apiUrl = 'http://localhost:8000/api';

  private _currentUser = signal<User | null>(null);
  currentUser = this._currentUser.asReadonly();
  isLoggedIn = computed(() => !!this._currentUser());

  // HttpClient'ı constructor'a ekledik
  constructor(
    private router: Router,
    private http: HttpClient
  ) {
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

  // LOGIN — Gerçek API'ye bağlandı
  async login(
    email: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await firstValueFrom(
        this.http.post<LoginResponse>(`${this.apiUrl}/login`, {
          email,
          password
        })
      );

      const user: User = {
        id: response.id,
        email: response.email,
        full_name: response.full_name
      };

      this.setSession(user);
      return { success: true };

    } catch (err) {
      const error = err as HttpErrorResponse;

      // Backend'den gelen hata mesajını kullan
      const message =
        error.error?.detail ||
        (error.status === 0
          ? 'Sunucuya bağlanılamıyor.'
          : 'Giriş yapılamadı.');

      return { success: false, error: message };
    }
  }

  // REGISTER — Gerçek API'ye bağlandı

  async register(
    full_name: string,
    email: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await firstValueFrom(
        this.http.post<RegisterResponse>(`${this.apiUrl}/register`, {
          full_name,
          email,
          password
        })
      );

      // Kayıt başarılı → oturumu aç
      const user: User = {
        id: String(response.id),
        email: response.email,
        full_name: response.full_name
      };

      this.setSession(user);
      return { success: true };

    } catch (err) {
      const error = err as HttpErrorResponse;

      let message = 'Kayıt olunamadı.';
      if (error.status === 409) {
        message = 'Bu e-posta adresi zaten kayıtlı.';
      } else if (error.status === 422) {
        message = 'Lütfen tüm alanları doğru doldurun.';
      } else if (error.status === 0) {
        message = 'Sunucuya bağlanılamıyor.';
      } else if (error.error?.detail) {
        message = error.error.detail;
      }

      return { success: false, error: message };
    }
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