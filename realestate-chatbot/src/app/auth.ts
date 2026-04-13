import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

export interface User {
  id: string; email: string; name?: string; avatar?: string;
}

const API = 'http://localhost:3000/api';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private _currentUser = signal<User | null>(null);
  currentUser = this._currentUser.asReadonly();
  isLoggedIn  = signal(false);

  constructor(private http: HttpClient, private router: Router) {
    this.restoreSession();
  }

  private restoreSession(): void {
    const token = localStorage.getItem('token');
    const user  = localStorage.getItem('user');
    if (token && user) {
      this._currentUser.set(JSON.parse(user));
      this.isLoggedIn.set(true);
    }
  }

  getToken(): string | null { return localStorage.getItem('token'); }

  async login(email: string, password: string):
      Promise<{ success: boolean; error?: string }> {
    try {
      const res: any = await firstValueFrom(
        this.http.post(`${API}/auth/login`, { email, password })
      );
      localStorage.setItem('token', res.token);
      localStorage.setItem('user', JSON.stringify(res.user));
      this._currentUser.set(res.user);
      this.isLoggedIn.set(true);
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e.error?.error || 'Login failed' };
    }
  }

  async register(name: string, email: string, password: string):
      Promise<{ success: boolean; error?: string }> {
    try {
      await firstValueFrom(
        this.http.post(`${API}/auth/register`, { name, email, password })
      );
      return { success: true };
    } catch (e: any) {
      return { success: false, error: e.error?.error || 'Registration failed' };
    }
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    this._currentUser.set(null);
    this.isLoggedIn.set(false);
    this.router.navigate(['/login']);
  }
}